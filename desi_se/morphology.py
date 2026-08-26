"""
Morphology heuristic.

DESI does not measure morphology. We assign Hubble types stochastically
from a redshift-dependent distribution that loosely tracks DESI's
target-selection biases:
    BGS at z<0.4   -> mostly spirals + some ellipticals
    LRG at 0.4-1.0 -> mostly ellipticals/S0
    ELG at 1.0-1.6 -> mostly star-forming spirals
    z > 1.6        -> irregulars and late-type spirals dominate

These are PLAUSIBILITY HEURISTICS, not measured distributions.
The user can disable them by setting --no-morphology, in which case
SE will procedurally pick a type per object.

Hubble types valid in SpaceEngine (per the manual / NGC-IC.csv):
    Ellipticals: E0, E1, E2, E3, E4, E5, E6, E7
    Lenticulars: S0
    Spirals:     Sa, Sb, Sc, Sd
    Barred:      SBa, SBb, SBc, SBm
    Irregular:   Irr
"""

import numpy as np


# ((z_low, z_high, [(weight, type_or_pool), ...]))
# Each pool entry is either a string (single type) or a list (uniform
# random choice within the pool). Weights need not sum to 1.
_DISTRIBUTIONS = [
    (0.00, 0.10, [
        (0.30, ['Sa', 'Sb', 'Sc']),
        (0.20, ['SBa', 'SBb', 'SBc']),
        (0.20, ['E0', 'E1', 'E2', 'E3', 'E4', 'E5']),
        (0.10, ['E6', 'E7', 'S0']),
        (0.10, ['Sd', 'SBm']),
        (0.10, 'Irr'),
    ]),
    (0.10, 0.40, [
        (0.20, ['Sa', 'Sb', 'Sc']),
        (0.15, ['SBa', 'SBb', 'SBc']),
        (0.30, ['E0', 'E1', 'E2', 'E3', 'E4']),
        (0.20, ['E5', 'E6', 'E7', 'S0']),
        (0.10, ['Sd']),
        (0.05, 'Irr'),
    ]),
    (0.40, 1.00, [
        (0.10, ['Sa', 'Sb']),
        (0.15, ['SBa', 'SBb']),
        (0.45, ['E0', 'E1', 'E2', 'E3']),
        (0.25, ['E4', 'E5', 'E6', 'S0']),
        (0.05, 'Irr'),
    ]),
    (1.00, 1.60, [
        (0.30, ['Sb', 'Sc']),
        (0.30, ['SBb', 'SBc']),
        (0.10, ['Sd', 'SBm']),
        (0.10, ['E0', 'E1', 'S0']),
        (0.20, 'Irr'),
    ]),
    (1.60, 99.0, [
        (0.20, ['Sc', 'Sd']),
        (0.20, ['SBc', 'SBm']),
        (0.10, ['E0', 'E1']),
        (0.50, 'Irr'),
    ]),
]


def _pick_one(rng, pool):
    """pool is either a string or a list of strings."""
    if isinstance(pool, str):
        return pool
    return pool[rng.integers(0, len(pool))]


def assign_hubble_types(z, rng):
    """
    Vectorized assignment of Hubble types from the redshift-conditioned
    distribution. Returns an array of strings, one per input z.

    rng: numpy.random.Generator
    """
    z = np.asarray(z, dtype=float)
    out = np.empty(z.shape, dtype=object)

    for z_low, z_high, dist in _DISTRIBUTIONS:
        mask = (z >= z_low) & (z < z_high)
        n = int(mask.sum())
        if n == 0:
            continue
        weights = np.array([w for w, _ in dist], dtype=float)
        weights = weights / weights.sum()
        pools = [pool for _, pool in dist]
        # Choose pool index for each masked object
        pool_idx = rng.choice(len(dist), size=n, p=weights)
        # Then pick a type from that pool
        chosen = np.empty(n, dtype=object)
        for i, pi in enumerate(pool_idx):
            chosen[i] = _pick_one(rng, pools[pi])
        out[mask] = chosen

    # Fill anything that didn't match (negative z, NaN) with E0
    unfilled = out == None  # noqa: E711
    out[unfilled] = 'E0'
    return out.astype(str)


def random_unit_quaternions(n, rng):
    """Uniform random unit quaternions, returned as (n, 4) array w,x,y,z."""
    # Standard method: sample in 4D Gaussian, normalize. Uniform on S^3.
    q = rng.standard_normal((n, 4))
    norms = np.linalg.norm(q, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return q / norms
