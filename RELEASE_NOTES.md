# GitHub Release body templates

One template per tier, to paste into the Release description when
attaching `DESI_DR1_<tier>.zip`. Substitution values are at the bottom.

Suggested release title format:

```
DESI DR1 Cosmic Web — Lite (~250k galaxies)
DESI DR1 Cosmic Web — Normal (~2.5M galaxies)
DESI DR1 Cosmic Web — Heavy (~6M galaxies + ~400k quasars)
DESI DR1 Cosmic Web — Insane (~14.1M galaxies + ~1.65M quasars)
```

Suggested repo topics: `spaceengine`, `desi`, `astronomy`,
`cosmology`, `data-visualization`, `catalog`.

If you cut all four tiers as one release, use a single tag (e.g. `v1.0.0`)
with four attached zips and paste the four "What you get" blocks under
one heading. If you cut them separately, tag per tier
(e.g. `v1.0.0-heavy`).

---

## TEMPLATE — paste into the Release description, edit per tier

---

# DESI DR1 Cosmic Web — {TIER} tier

Imports the **Dark Energy Spectroscopic Instrument (DESI) Data Release 1**
catalog into SpaceEngine. Real galaxies and quasars at correct cosmological
distances, mapping the actual large-scale structure of the universe out to
{REDSHIFT_RANGE_FOR_THIS_TIER — e.g. "z~0.4" / "z~1.6" / "z~3" / "z>5"}.

## What you get

- **{N_GALAXIES_FOR_TIER}** real galaxies with measured redshifts
- **{N_QSOS_FOR_TIER}** real quasars *(omit this line for lite/normal)*
- Distances span from ~46 million light-years (just outside the Local
  Group) to {MAX_LY_FOR_TIER — e.g. "5 billion ly" / "16 billion ly" /
  "21 billion ly" / "26+ billion ly"}
- Filaments, voids, and the cosmic web become directly explorable

## Install

Pick either asset below:

- `DESI_DR1_{TIER}.pak` — just the data. Drop it into your `addons`
  folder. Nothing to unzip.
- `DESI_DR1_{TIER}.zip` — the same `.pak` plus a README and
  CITATIONS.txt. Unzip into `addons`.

Then launch SpaceEngine. **Leave the `.pak` packed either way** —
SpaceEngine reads it as an archive.

As of SpaceEngine 0.991.50.2140 (May 2026), the recommended addons
location is `%USERPROFILE%\Documents\Cosmographic\SpaceEngine\addons\`.
`SpaceEngine\addons\` in the Steam install folder also works, but Steam
can overwrite it on update or file verification.

To uninstall, delete the folder — nothing is written outside it.

Download {DOWNLOAD_SIZE_FOR_TIER}, {INSTALLED_SIZE_FOR_TIER} on disk.

**Addon not showing up?** Delete `%LOCALAPPDATA%\Cosmographic\SpaceEngine`
to clear SE's cache and relaunch (SE rebuilds it), then check `se.log` in
SpaceEngine's system folder for catalog parse errors.

## Recommended hardware

{TIER-SPECIFIC GUIDANCE — pick one:}

- **Lite:** runs on anything that runs SpaceEngine itself.
- **Normal:** 16 GB RAM recommended. Comfortable on most modern systems.
- **Heavy:** 16–32 GB RAM. Noticeable load time on first launch.
- **Insane:** 32 GB+ RAM. Long load time. Stability and framerate may
  suffer on lower-end systems. Try Heavy first.

## Important — pick ONE tier

**Don't install multiple DESI DR1 tiers at the same time.** They overlap,
and SpaceEngine will load both, doubling memory cost and producing
duplicate objects. Pick the tier that fits your hardware.

## How it works

DESI is a 5,000-fiber spectrograph at Kitt Peak that has measured precise
redshifts for tens of millions of galaxies and quasars across about a third
of the sky. This addon takes the public DR1 catalog (released March 2025,
licensed CC BY 4.0) and converts it into SpaceEngine catalog files.

**What's accurate:** positions, distances, and redshifts are real DESI
measurements. Distances are comoving distances under DESI's fiducial
cosmology (Planck 2018 ΛCDM).

**What's not from DESI:** galaxy morphology (Hubble type), orientation,
and exact size. DESI is a spectroscopic survey and doesn't measure shape.
The addon assigns plausible Hubble types from a redshift-conditioned
distribution to give visual variety. Treat morphology as flavor, not data.

## Coverage notes

- DESI's footprint covers about a third of the sky. The Galactic plane
  (the "zone of avoidance") is not observed. You'll see this absence as
  a band of empty sky — that's real, not a bug.
- Quasars are imported as quasar objects; SE generates their central
  black holes procedurally.
- Quasar host galaxies may show implausibly large star counts. QSO
  luminosity comes from accretion-disk emission, but SpaceEngine reads it
  as starlight. Expected, not a bug.
- Galaxies near already-cataloged objects (NGC, IC) may produce visible
  duplicates with the stock SE catalogs. Cosmetic, not catastrophic.

## Credits

**Data:** DESI Collaboration et al. (2025), "Data Release 1 of the Dark
Energy Spectroscopic Instrument",
[arXiv:2503.14745](https://arxiv.org/abs/2503.14745).

**DESI public data:** https://data.desi.lbl.gov/

This addon is **not affiliated with the DESI collaboration** or with
SpaceEngine. It's a community contribution that imports public DESI data
using SpaceEngine's addon system.

If you make videos or images using this addon, please credit the DESI
collaboration. The full official acknowledgment text is in the addon's
`CITATIONS.txt`.

License: addon code MIT, DESI data CC BY 4.0.

---

## END TEMPLATE

---

## Per-tier substitution values

**LITE**

```
{N_GALAXIES_FOR_TIER}          = ~250,000
{N_QSOS_FOR_TIER}              = (omit the line)
{REDSHIFT_RANGE_FOR_THIS_TIER} = z<0.4
{MAX_LY_FOR_TIER}              = 5 billion light-years
{DOWNLOAD_SIZE_FOR_TIER}       = 6.7 MB
{INSTALLED_SIZE_FOR_TIER}      = 6.7 MB (the .pak stays packed)
```

**NORMAL**

```
{N_GALAXIES_FOR_TIER}          = ~2,500,000
{N_QSOS_FOR_TIER}              = (omit the line)
{REDSHIFT_RANGE_FOR_THIS_TIER} = z<1.6
{MAX_LY_FOR_TIER}              = 16 billion light-years
{DOWNLOAD_SIZE_FOR_TIER}       = 63 MB
{INSTALLED_SIZE_FOR_TIER}      = 63 MB (the .pak stays packed)
```

**HEAVY**

```
{N_GALAXIES_FOR_TIER}          = ~6,000,000
{N_QSOS_FOR_TIER}              = ~400,000
{REDSHIFT_RANGE_FOR_THIS_TIER} = z<3
{MAX_LY_FOR_TIER}              = 21 billion light-years
{DOWNLOAD_SIZE_FOR_TIER}       = 157 MB
{INSTALLED_SIZE_FOR_TIER}      = 157 MB (the .pak stays packed)
```

**INSANE**

```
{N_GALAXIES_FOR_TIER}          = ~14,100,000 (full DR1)
{N_QSOS_FOR_TIER}              = ~1,650,000 (full DR1)
{REDSHIFT_RANGE_FOR_THIS_TIER} = z up to ~5
{MAX_LY_FOR_TIER}              = over 26 billion light-years
{DOWNLOAD_SIZE_FOR_TIER}       = 378 MB
{INSTALLED_SIZE_FOR_TIER}      = 378 MB (the .pak stays packed)
```

Sizes above are measured from the actual release assets built by
`./package_release.sh` on 2026-08-26. Because the `.pak` is never
unpacked, download size and on-disk size are the same; the uncompressed
catalog trees would be 22 MB / 216 MB / 568 MB / 1.4 GB.

---

## Screenshots worth having

Not required, but a README/release image does most of the selling. One
per tier, ideally:

- **Lite:** a wedge shot showing the local-universe filaments, the
  z<0.4 region. The "Slice of the Universe" pie-chart-like view.
- **Normal:** zoomed-out view showing filaments and voids clearly. The
  100–500 Mpc shell is the sweet spot.
- **Heavy:** a close pass near a quasar with the cosmic web visible in
  the background. Sells "real quasars at real distances."
- **Insane:** maximum zoom-out, the entire DESI footprint visible,
  showing scale up to multi-Gpc. Sells the volume.

Each should make the tier's selling point obvious at a glance. Committing
them under `docs/img/` and linking from the top-level README is the
simplest option — they're small enough to track in git, unlike the
catalogs.
