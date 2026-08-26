# DESI DR1 cosmic web for SpaceEngine — INSANE tier

This addon imports 15,752,438 real galaxies and quasars from the
**Dark Energy Spectroscopic Instrument (DESI) Data Release 1** into
SpaceEngine, letting you fly through the actual large-scale structure of
the universe at correct cosmological distances.

> Built: 2026-05-02 — converter v1.0.0 — tier: insane

## What's in this tier

Full deduplicated DR1 main extragalactic (~14.1M galaxies + ~1.65M QSOs).

| Object class | Count |
|---|---:|
| Galaxies | 14,106,595 |
| Quasar hosts | 1,645,843 |
| **Total** | **15,752,438** |

Distance range covered: roughly 14 megaparsecs (~46 million light-years,
just outside the Local Group) out to several gigaparsecs (over 20 billion
light-years for high-redshift quasars). All objects are placed at their
correct comoving distances under DESI's fiducial flat ΛCDM cosmology
(H₀ = 67.36 km/s/Mpc, Ωₘ = 0.3145).

## Installation

Drop this folder into your SpaceEngine `addons/` directory so the path
becomes:

```
SpaceEngine/addons/DESI_DR1_insane/
```

Then launch SpaceEngine — the catalog loads at startup. Keep the
`catalogs/` subdirectory structure intact; that's what SE looks for. If
your unzip tool nested the folder inside another folder of the same
name, move the inner one up a level.

To uninstall, delete this folder. Nothing is written outside it.

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
