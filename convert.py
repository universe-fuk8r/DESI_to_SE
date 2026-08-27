#!/usr/bin/env python3
"""
DESI -> SpaceEngine addon converter.

Usage:
    python convert.py --input zall-pix-iron.fits --tier heavy --output ./addons

Tiers:
    lite    ~250k objects, BGS-Bright at z<0.4. No QSOs.
    normal  ~2.5M objects, BGS+LRG+ELG. No QSOs.
    heavy   ~6M galaxies + ~400k QSOs to z~3.
    insane  Full DR1 main extragalactic (~14.1M galaxies + ~1.65M QSOs).

Source:
    Download DESI DR1 zall-pix-iron.fits from
    https://data.desi.lbl.gov/public/dr1/spectro/redux/iron/zcatalog/v1/

Output (per tier):
    addons/DESI_DR1_<tier>/
      catalogs/galaxies/desi_galaxies.csv
      catalogs/galaxies/desi_qsos.sc           (heavy/insane only)
      README.md
      CITATIONS.txt
"""

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import numpy as np

from desi_se import __version__
from desi_se import reader, writers
from desi_se.cosmology import z_to_distance_pc, z_to_luminosity_distance_pc
from desi_se.magnitudes import (
    flux_nmgy_to_appmag, appmag_to_absmag, fallback_absmag_by_z,
    clamp_absmag,
)
from desi_se.morphology import assign_hubble_types
from desi_se.tiers import TIERS, apply_tier_filters
from desi_se.writers import _name_for_targetid


def parse_args():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    p.add_argument('--input', '-i', required=True, type=Path,
                   help='DESI zpix/ztile FITS file path.')
    p.add_argument('--tier', '-t', required=True, choices=list(TIERS.keys()))
    p.add_argument('--output', '-o', default=Path('./addons'), type=Path,
                   help='Output root directory (default: ./addons).')
    p.add_argument('--seed', type=int, default=42,
                   help='RNG seed for reproducibility (default: 42).')
    p.add_argument('--no-morphology', action='store_true',
                   help='Skip Hubble type assignment; SE will procedurally pick.')
    p.add_argument('--quiet', action='store_true')
    return p.parse_args()


def setup_logging(quiet):
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s',
    )


def compute_absmag(table, idx):
    """
    Compute absolute magnitude using FLUX_R if available, falling back
    to a redshift-binned median otherwise. Clamps to physically
    plausible ranges to filter photometry artifacts.
    """
    flux_r = table['FLUX_R'][idx]
    z = table['Z'][idx]
    spectype = table['SPECTYPE'][idx]

    appmag = flux_nmgy_to_appmag(flux_r)
    d_lum = z_to_luminosity_distance_pc(z)
    absmag = appmag_to_absmag(appmag, d_lum)

    nan_mask = ~np.isfinite(absmag)
    if nan_mask.any():
        fallback = fallback_absmag_by_z(z[nan_mask], spectype[nan_mask])
        absmag[nan_mask] = fallback

    absmag = clamp_absmag(absmag, spectype)
    return absmag


def radius_from_absmag(absmag, fudge=1.0):
    """
    Crude size-luminosity scaling: R[kpc] ~ 5 * 10^(-0.2*(M+21)).
    Returns parsecs. Pure plausibility heuristic.
    """
    absmag = np.asarray(absmag, dtype=float)
    r_kpc = 5.0 * fudge * 10.0 ** (-0.2 * (absmag + 21.0))
    r_kpc = np.clip(r_kpc, 0.5, 200.0)
    return r_kpc * 1000.0


def assign_qso_host_types(z, rng):
    """
    QSO hosts are predominantly early-type galaxies at the relevant z range.
    Mix is biased toward S0/E to match observed QSO host morphology, with
    some spirals and irregulars (more at high z due to merger-driven AGN).

    Pure plausibility heuristic.
    """
    z = np.asarray(z, dtype=float)
    n = len(z)
    out = np.empty(n, dtype=object)

    # z < 1: predominantly S0 / early-type ellipticals (Seyferts, low-z QSOs)
    low = z < 1.0
    nlow = int(low.sum())
    if nlow > 0:
        out[low] = rng.choice(
            ['S0', 'E0', 'E1', 'E2', 'Sa', 'Sb'],
            size=nlow,
            p=[0.35, 0.20, 0.15, 0.10, 0.10, 0.10],
        )

    # 1 <= z < 2.5: ellipticals dominant, with merger-driven irregulars rising
    mid = (z >= 1.0) & (z < 2.5)
    nmid = int(mid.sum())
    if nmid > 0:
        out[mid] = rng.choice(
            ['E0', 'E1', 'E2', 'S0', 'Sb', 'Irr'],
            size=nmid,
            p=[0.25, 0.20, 0.15, 0.20, 0.10, 0.10],
        )

    # z >= 2.5: high-z QSOs in proto-galaxies, more disturbed morphology
    high = z >= 2.5
    nhigh = int(high.sum())
    if nhigh > 0:
        out[high] = rng.choice(
            ['Irr', 'E0', 'E1', 'Sc', 'Sd'],
            size=nhigh,
            p=[0.40, 0.20, 0.15, 0.15, 0.10],
        )

    # Fill anything unmatched (negative z, NaN) with E0
    unfilled = out == None  # noqa: E711
    out[unfilled] = 'E0'
    return out.astype(str)


def build_addon(input_path: Path, tier_name: str, output_root: Path, seed: int,
                no_morphology: bool):
    log = logging.getLogger('convert')
    tier = TIERS[tier_name]
    rng = np.random.default_rng(seed)

    log.info(f"Tier: {tier.name} - {tier.description}")
    log.info(f"Seed: {seed}")

    table = reader.read_zcatalog(input_path)
    reader.summarize(table)

    galaxy_mask, qso_mask = apply_tier_filters(table, tier)
    galaxy_idx = np.where(galaxy_mask)[0]
    qso_idx = np.where(qso_mask)[0]
    log.info(f"After tier filter: {len(galaxy_idx):,} galaxies, "
             f"{len(qso_idx):,} QSOs")

    if tier.galaxy_subsample and len(galaxy_idx) > tier.galaxy_subsample:
        galaxy_idx = rng.choice(galaxy_idx, size=tier.galaxy_subsample,
                                replace=False)
        galaxy_idx = np.sort(galaxy_idx)
        log.info(f"  subsampled galaxies to {len(galaxy_idx):,}")
    if tier.qso_subsample and len(qso_idx) > tier.qso_subsample:
        qso_idx = rng.choice(qso_idx, size=tier.qso_subsample, replace=False)
        qso_idx = np.sort(qso_idx)
        log.info(f"  subsampled QSOs to {len(qso_idx):,}")

    out_dir = output_root / f"DESI_DR1_{tier.name}"
    log.info(f"Output -> {out_dir}")

    if len(galaxy_idx) > 0:
        ra = table['RA'][galaxy_idx]
        dec = table['DEC'][galaxy_idx]
        z = table['Z'][galaxy_idx]
        targetids = table['TARGETID'][galaxy_idx]

        dist_pc = z_to_distance_pc(z)
        absmag = compute_absmag(table, galaxy_idx)
        if no_morphology:
            types = np.array([''] * len(galaxy_idx), dtype=object)
        else:
            types = assign_hubble_types(z, rng)
        radius = radius_from_absmag(absmag)
        names = np.array([_name_for_targetid(t) for t in targetids])

        writers.write_galaxies_csv(
            out_dir / 'catalogs' / 'galaxies' / 'desi_galaxies.csv',
            names, types, ra, dec, dist_pc, absmag, radius,
        )

    if tier.include_qsos and len(qso_idx) > 0:
        ra = table['RA'][qso_idx]
        dec = table['DEC'][qso_idx]
        z = table['Z'][qso_idx]
        targetids = table['TARGETID'][qso_idx]

        dist_pc = z_to_distance_pc(z)
        absmag = compute_absmag(table, qso_idx)
        if no_morphology:
            types = np.array([''] * len(qso_idx), dtype=object)
        else:
            types = assign_qso_host_types(z, rng)
        radius = radius_from_absmag(absmag)
        names = np.array([_name_for_targetid(t, prefix='DESI QSO')
                          for t in targetids])

        writers.write_qsos_sc(
            out_dir / 'catalogs' / 'galaxies' / 'desi_qsos.sc',
            names, types, ra, dec, dist_pc, absmag, radius,
        )

    write_readme(out_dir, tier, len(galaxy_idx),
                 len(qso_idx) if tier.include_qsos else 0)
    write_citations(out_dir)
    log.info(f"Done. Addon at {out_dir}")


def write_readme(out_dir, tier, n_gal, n_qso):
    p = out_dir / 'README.md'
    p.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    p.write_text(f"""# DESI DR1 cosmic web for SpaceEngine — {tier.name.upper()} tier

This addon imports {n_gal + n_qso:,} real galaxies and quasars from the
**Dark Energy Spectroscopic Instrument (DESI) Data Release 1** into
SpaceEngine, letting you fly through the actual large-scale structure of
the universe at correct cosmological distances.

> Built: {today} — converter v{__version__} — tier: {tier.name}

## What's in this tier

{tier.description}

| Object class | Count |
|---|---:|
| Galaxies | {n_gal:,} |
| Quasar hosts | {n_qso:,} |
| **Total** | **{n_gal + n_qso:,}** |

Distance range covered: roughly 14 megaparsecs (~46 million light-years,
just outside the Local Group) out to several gigaparsecs (over 20 billion
light-years for high-redshift quasars). All objects are placed at their
correct comoving distances under DESI's fiducial flat ΛCDM cosmology
(H₀ = 67.36 km/s/Mpc, Ωₘ = 0.3145).

## Installation

Drop `DESI_DR1_{tier.name}.pak` into a SpaceEngine `addons` directory.
That's the entire install — no folders to create, nothing to unpack.

As of SpaceEngine 0.991.50.2140 (May 2026) there are three places SE
looks for addons:

```
%USERPROFILE%\\Documents\\Cosmographic\\SpaceEngine\\addons\\
    ^ recommended
SpaceEngine\\addons\\
    the Steam install folder
SpaceEngine\\data\\
```

The Documents location is recommended — Steam can overwrite the install
folder when the game updates or you verify file integrity, which would
take the addon with it.

So you want this, and nothing more:

```
...\\addons\\DESI_DR1_{tier.name}.pak
```

**Leave the `.pak` packed.** SpaceEngine reads it as an archive; unpacking
it is unnecessary. This README and `CITATIONS.txt` are inside it.

If you prefer to keep things tidy, a subfolder works identically:
`...\\addons\\DESI_DR1_{tier.name}\\DESI_DR1_{tier.name}.pak` loads the
same way.

Then launch SpaceEngine — the catalog loads at startup. Expect a
noticeably longer first launch on the heavy and insane tiers.

To uninstall, delete the `.pak`. Nothing is written outside it.

### If the addon doesn't show up

- **Clear SE's cache and restart.** Delete
  `%LOCALAPPDATA%\\Cosmographic\\SpaceEngine` — SE rebuilds it on next
  launch. This isn't normally required, but it clears stale filesystem
  entries that can hide a newly added addon.
- **Check `se.log`** in SpaceEngine's system folder for catalog parse
  errors.
- **Check the `.pak` sits directly in `addons`** — not inside a
  `catalogs` subfolder, and not one level above `addons`.

## Recommendations for the best experience

- **Don't run multiple DESI DR1 tiers at once.** They're cumulative —
  installing lite + insane will load both, with duplicate objects
  and double the memory cost. Pick one tier.
- **Galaxy filter.** Settings → Filter Objects lets you reduce the
  visibility of procedurally-generated galaxies if you find the
  overlap with DESI catalog objects distracting.
- **Cosmic web is best appreciated zoomed out.** Filaments, voids, and
  the sponge-like structure become visible at the 100 megaparsec to
  several gigaparsec scale. Zoom in to individual galaxies for the
  procedural starfield SE generates around each one.

## What's accurate, what's not

DESI provides extremely precise spectroscopic redshifts for every object
in this catalog. That means the **positions and distances are real
science data**. What's not from DESI:

- **Morphology (Hubble type)** — DESI is a spectroscopic survey, not an
  imaging one. It does not measure galaxy shape. Hubble types in this
  addon are sampled from a redshift-conditioned probability distribution
  that loosely matches DESI target-selection biases (more spirals at
  low z, more ellipticals at intermediate z, more irregulars and
  late-type spirals at high z). Treat morphology as visual flavor, not
  measurement.
- **Galaxy radius** — Derived from luminosity using a crude size-
  luminosity scaling. Order-of-magnitude correct; not measured.
- **Galaxy orientation** — Set to identity. SE renders galaxies face-on
  by default. DESI doesn't measure orientation.
- **Quasar central black holes** — SpaceEngine generates these
  procedurally from the host galaxy. We don't import explicit BH masses.
- **Quasar star counts** — QSO absolute magnitudes reflect AGN accretion
  disk emission, not stellar light. SpaceEngine interprets this luminosity
  as stellar population and will render some quasar hosts as implausibly
  massive galaxies — occasionally in the hundreds of trillions of stars.
  This is expected, not a bug. The luminosity values are real DESI
  measurements; SpaceEngine simply has no way to distinguish AGN emission
  from starlight. Some genuinely extreme objects (brightest cluster
  galaxies, massive ellipticals) do reach these scales — IC 1101 clocks
  in at ~100 trillion — so not every monster you encounter is an artifact.

Other things to be aware of:

- Absolute magnitudes are computed from DESI Legacy Imaging Surveys
  FLUX_R photometry, with no K-correction. Errors of a few tenths of
  a magnitude at moderate z, growing to ~1 mag at z > 1.5.
- Where photometry is missing, brightness falls back to redshift-binned
  population medians.
- Galaxies near already-cataloged objects (NGC, IC, etc.) may produce
  visible duplicates with the stock SE catalogs. The overlap is
  cosmetic, not catastrophic.
- Coverage matches DESI's footprint (about a third of the sky). The
  Galactic plane is not covered; you'll see DESI's "zone of avoidance."
  This is real, not a bug.

## Credits

This addon is **not affiliated with the DESI collaboration or
SpaceEngine.** It's a community contribution that imports public DESI
data into SpaceEngine using the addon system.

- **Data:** DESI Collaboration et al. (2025), Data Release 1 of the
  Dark Energy Spectroscopic Instrument. arXiv:2503.14745.
- **DESI public data portal:** https://data.desi.lbl.gov/
- **SpaceEngine:** https://spaceengine.org/

DESI data is released under Creative Commons Attribution 4.0
International (CC BY 4.0). See `CITATIONS.txt` for the official
DESI acknowledgment text — please include it in any video, post,
publication, or presentation that uses imagery from this addon.

## License

This addon's code and configuration: MIT License.
The DESI data this addon imports: CC BY 4.0 (DESI Collaboration).
""")


def write_citations(out_dir):
    p = out_dir / 'CITATIONS.txt'
    p.write_text("""DESI DR1 — Required Citations and Acknowledgment
=================================================

This addon imports public data from the Dark Energy Spectroscopic
Instrument (DESI) Data Release 1, released under the Creative Commons
Attribution 4.0 International License (CC BY 4.0).

If you publish, broadcast, or otherwise share content (videos, articles,
papers, social media posts, screenshots) that uses imagery generated
from this addon, the DESI collaboration asks that you include the
following.

CITE
----

DESI Collaboration et al. (2025), "Data Release 1 of the Dark Energy
Spectroscopic Instrument", arXiv:2503.14745.

If you use Early Data Release content as well:
DESI Collaboration et al. (2024), "The Early Data Release of the Dark
Energy Spectroscopic Instrument", AJ, 168, 58.

ACKNOWLEDGMENT (verbatim, per DESI policy)
-------------------------------------------

This research used data obtained with the Dark Energy Spectroscopic
Instrument (DESI). DESI construction and operations is managed by the
Lawrence Berkeley National Laboratory. This material is based upon
work supported by the U.S. Department of Energy, Office of Science,
Office of High-Energy Physics, under Contract No. DE-AC02-05CH11231,
and by the National Energy Research Scientific Computing Center, a DOE
Office of Science User Facility under the same contract. Additional
support for DESI was provided by the U.S. National Science Foundation
(NSF), Division of Astronomical Sciences under Contract No. AST-0950945
to the NSF's National Optical-Infrared Astronomy Research Laboratory;
the Science and Technology Facilities Council of the United Kingdom;
the Gordon and Betty Moore Foundation; the Heising-Simons Foundation;
the French Alternative Energies and Atomic Energy Commission (CEA);
the National Council of Humanities, Science and Technology of Mexico
(CONAHCYT); the Ministry of Science, Innovation and Universities of
Spain (MICIU/AEI/10.13039/501100011033), and by the DESI Member
Institutions: https://www.desi.lbl.gov/collaborating-institutions.

Any opinions, findings, and conclusions or recommendations expressed
in this material are those of the author(s) and do not necessarily
reflect the views of the U. S. National Science Foundation, the U. S.
Department of Energy, or any of the listed funding agencies.

The authors are honored to be permitted to conduct scientific research
on Iolkam Du'ag (Kitt Peak), a mountain with particular significance
to the Tohono O'odham Nation.

LICENSING
---------

DESI DR1 data: Creative Commons Attribution 4.0 International (CC BY 4.0).
For full license text and the latest acknowledgment requirements:
  https://data.desi.lbl.gov/doc/acknowledgments/

This SpaceEngine addon (the catalog conversion code, structure, and
generated SC/CSV format): MIT License. The addon is not affiliated
with the DESI collaboration or with Cosmographic Software (SpaceEngine).
""")


def main():
    args = parse_args()
    setup_logging(args.quiet)
    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(2)
    build_addon(
        input_path=args.input,
        tier_name=args.tier,
        output_root=args.output,
        seed=args.seed,
        no_morphology=args.no_morphology,
    )


if __name__ == '__main__':
    main()
