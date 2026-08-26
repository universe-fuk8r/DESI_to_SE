"""
Tier definitions for the four flavors of the addon.

Filters operate on a structured array / Table with columns:
    SPECTYPE (decoded to str), Z, ZWARN, optionally other columns.

Each tier returns boolean masks for galaxies and QSOs separately so the
writers can split them.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tier:
    name: str
    description: str
    target_galaxies: int        # nominal target count, for logging
    target_qsos: int            # nominal target count
    z_min: float                # lower redshift bound (excludes Local Group + spurious near-zero z)
    z_max_galaxy: float         # upper redshift bound for galaxies
    z_max_qso: Optional[float]  # upper bound for QSOs; None = unbounded
    include_qsos: bool
    galaxy_subsample: Optional[int] = None  # if set, randomly subsample
    qso_subsample: Optional[int] = None


TIERS = {
    'lite': Tier(
        name='lite',
        description='~250k local-universe BGS galaxies, no QSOs. Runs on anything.',
        target_galaxies=250_000,
        target_qsos=0,
        z_min=0.0033,
        z_max_galaxy=0.4,
        z_max_qso=None,
        include_qsos=False,
        galaxy_subsample=250_000,
    ),
    'normal': Tier(
        name='normal',
        description='~2.5M galaxies through z~1.6 (BGS + LRG + ELG). No QSOs.',
        target_galaxies=2_500_000,
        target_qsos=0,
        z_min=0.0033,
        z_max_galaxy=1.6,
        z_max_qso=None,
        include_qsos=False,
        galaxy_subsample=2_500_000,
    ),
    'heavy': Tier(
        name='heavy',
        description='~6M galaxies + ~400k QSOs to z~3.',
        target_galaxies=6_000_000,
        target_qsos=400_000,
        z_min=0.0033,
        z_max_galaxy=99.0,
        z_max_qso=3.0,
        include_qsos=True,
        galaxy_subsample=6_000_000,
        qso_subsample=400_000,
    ),
    'insane': Tier(
        name='insane',
        description='Full deduplicated DR1 main extragalactic (~14.1M galaxies + ~1.65M QSOs).',
        target_galaxies=15_000_000,
        target_qsos=1_500_000,
        z_min=0.0033,
        z_max_galaxy=99.0,
        z_max_qso=None,
        include_qsos=True,
    ),
}


def apply_tier_filters(table, tier: Tier):
    """
    Return (galaxy_mask, qso_mask) for the given table and tier.

    The table must have SPECTYPE (str), Z (float), ZWARN (int) at minimum.
    If a PRIMARY column is present (ZCAT_PRIMARY / MAIN_PRIMARY), only
    primary rows are kept. Otherwise rows are deduplicated by TARGETID
    keeping the first occurrence (which arrives in HDU order, typically
    the canonical entry).
    """
    spectype = table['SPECTYPE']
    z = table['Z']
    zwarn = table['ZWARN']

    # Quality cut applied to everything. The z_min cut excludes the
    # Local Group (where SE has its own curated NGC catalog), spurious
    # near-zero redshifts, peculiar-velocity-dominated objects, and
    # stellar contamination that slipped past DESI's star-galaxy cut.
    # 0.0033 ~ 14 Mpc, matching DESIVAST's analysis floor.
    good = (zwarn == 0) & np.isfinite(z) & (z >= tier.z_min)

    # Primary / dedup
    if table.get('_HAS_PRIMARY', False):
        good = good & table['PRIMARY']
    else:
        # Fallback: dedup by TARGETID, keeping first occurrence
        targetid = table['TARGETID']
        _, first_idx = np.unique(targetid, return_index=True)
        keep = np.zeros_like(good, dtype=bool)
        keep[first_idx] = True
        good = good & keep

    galaxy_mask = good & (spectype == 'GALAXY') & (z < tier.z_max_galaxy)

    if tier.include_qsos:
        qso_mask = good & (spectype == 'QSO')
        if tier.z_max_qso is not None:
            qso_mask = qso_mask & (z < tier.z_max_qso)
    else:
        qso_mask = np.zeros_like(z, dtype=bool)

    return galaxy_mask, qso_mask
