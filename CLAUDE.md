# desi-to-spaceengine — orientation for Claude

Converts DESI redshift catalogs into SpaceEngine addons. Four tiers, built
from one source FITS, distributed as GitHub Release assets.

**Repo:** https://github.com/universe-fuk8r/DESI_to_SE (public)
**Status as of 2026-08-27: shipped and mothballed.** v1.0.0 is released and
public. Nothing is in progress. The next planned work is a DR2 rebuild,
expected spring 2027.

If you are resuming this project, read this file and the
"When DR2 lands" section of `README.md`. That section is the DR2 task list
and is intentionally not duplicated here.

## Hard invariants — do not violate without explicit instruction

1. **The DR1 catalog output is frozen.** The four addons under `addons/`
   were built 2026-05-02 and are verified working in-game, including at
   insane density. Any change that alters catalog bytes invalidates the
   shipped release and requires a full multi-GB rebuild plus in-game
   retesting. Docstrings, comments, and markdown may be edited freely.

   When you edit a `.py` file, prove the catalog output is unchanged:
   build the mock twice (once with the current tree, once with a known-good
   copy) and `cmp` the `catalogs/` files. This has been done for every
   `convert.py` edit so far and has always come back byte-identical.

2. **QSOs are emitted as `Quasar` blocks, not `Galaxy`.** An earlier
   revision used `Galaxy` to dodge suspected emission-region artifacts;
   it was reverted, and `Quasar` is confirmed working at ~1.6M blocks.
   Stale docs once claimed otherwise and sent an analysis badly wrong.
   Do not change the keyword without full-scale in-game retesting.

3. **The `insane` tier is deliberately uncapped.** It sets no
   `galaxy_subsample` / `qso_subsample`, unlike the other three. This is
   the point of the tier — the full deduplicated catalog, whatever it
   costs. When DR2 doubles it, update the RAM guidance, not the cap.

4. **A `.pak` must have only standard SE folders at its archive root.**
   Per the SpaceEngine manual, "the pak file cannot contain additional
   subfolders, only default ones are allowed." Build paks from *inside*
   the addon directory. Zipping `DESI_DR1_<tier>/` puts a non-standard
   folder at the root and SE silently loads nothing — no error, objects
   just never appear. `package_release.sh` asserts this before finishing;
   use it rather than hand-rolling a zip.

   Root-level *files* are fine: each pak also carries `README.md` and
   `CITATIONS.txt`, verified working in-game across all tiers.

## Layout

```
convert.py              CLI; one tier per invocation. Also holds the
                        generated end-user README template (write_readme).
desi_se/
  reader.py             FITS -> dict of numpy arrays. Tolerant of column
                        name drift between DESI releases.
  tiers.py              The four tier definitions + filter logic.
  cosmology.py          z -> comoving / luminosity distance.
  magnitudes.py         FLUX_R -> apparent -> absolute mag, with fallbacks.
  morphology.py         Redshift-conditioned Hubble type heuristic.
  writers.py            CSV (galaxies) and .sc (quasars) emitters.
make_mock.py            Synthetic DESI-shaped FITS, for testing without
                        the 22 GB download.
package_release.sh      Builds dist/ release assets. Asserts pak layout.
addons/DESI_DR1_*/      Built addons. catalogs/ is gitignored; the
                        generated README.md and CITATIONS.txt are tracked.
RELEASE_NOTES.md        Release body templates + per-tier substitutions.
```

**Not in git, by design:** `*.fits` (the 22 GB source), `addons/*/catalogs/`
(2.2 GB, and all but one file exceed GitHub's 100 MB limit), `dist/`,
`*.pak`. All are reproducible from the pipeline.

The generated addon `README.md` files must stay in sync with `convert.py`'s
template. Re-render them through `write_readme` rather than hand-editing,
and preserve each file's existing `> Built:` date — the catalogs really
were built 2026-05-02 and restamping it misreports provenance.

## Workflow

```bash
# Source data (not in repo) — DR1:
#   https://data.desi.lbl.gov/public/dr1/spectro/redux/iron/zcatalog/v1/
#   'iron' is DR1's reduction codename; DR2 will have its own.

# Test without the real data
python make_mock.py --n 100000 --out mock.fits
python convert.py -i mock.fits -t heavy -o ./test_out

# Build one tier / all four
python convert.py -i zall-pix-iron.fits -t heavy -o ./addons
for t in lite normal heavy insane; do
  python convert.py -i zall-pix-iron.fits -t $t -o ./addons
done

# Package release assets into dist/ (bare .pak + wrapper .zip per tier)
./package_release.sh                # all four
./package_release.sh lite heavy     # named tiers

# Publish
gh release create vX.Y.Z dist/*.pak dist/*.zip \
  --title "..." --notes-file dist/RELEASE_BODY_vX.Y.Z.md
```

Peak build memory scales with **source** row count, not output size —
`reader.py` materializes full columns before filtering. A doubled DR2
catalog roughly doubles the build machine's requirement even for lite.

## Measured facts (don't re-derive)

DR1 v1.0.0, built 2026-05-02, measured 2026-08-27:

| Tier | Galaxies | QSOs | Download | Max comoving | Reach |
|---|---:|---:|---:|---:|---:|
| lite | 250,000 | 0 | 6.7 MB | 1.606 Gpc | 5.24 Gly |
| normal | 2,500,000 | 0 | 63 MB | 4.670 Gpc | 15.23 Gly |
| heavy | 6,000,000 | 400,000 | 157 MB | 6.513 Gpc | 21.24 Gly |
| insane | 14,106,595 | 1,645,843 | 378 MB | 8.770 Gpc | 28.60 Gly |

- Heavy's ceiling is exactly z=3.00 — its `z_max_qso` cut.
- Insane is uncapped; its furthest quasar is at z≈6.86.
- Galaxies top out at 4.840 Gpc even uncapped (DESI's `GALAXY` spectype
  effectively ends near z≈1.65; beyond that they're QSOs).
- Uncompressed catalogs: 22 MB / 216 MB / 568 MB / 1.4 GB.
- Compression ratios: ~3.2x on galaxy CSVs, ~4.7x on quasar `.sc` files.

## SpaceEngine specifics

As of SE **0.991.50.2140** (4 May 2026) addons are searched in three
places, and the Documents path is recommended because Steam can overwrite
the install folder on update or file verification:

```
%USERPROFILE%\Documents\Cosmographic\SpaceEngine\addons\   <- recommended
SpaceEngine\addons\
SpaceEngine\data\
```

Cache lives at `%LOCALAPPDATA%\Cosmographic\SpaceEngine`. Deleting it is a
*troubleshooting* step, not a required install step. `se.log` in SE's
system folder reports catalog parse errors.

`.pak` is optional — loose folders work too, and `addons/<AnyName>/catalogs/`
is an explicitly supported layout. We ship paks because they're one file.

## Distribution decisions

- **GitHub only, never Steam Workshop.** A deliberate choice, not an oversight — do not reintroduce Workshop framing.
- Each tier ships twice: a bare `.pak` (drop into `addons`, no unzip) and a
  `.zip` wrapping the same pak with loose copies of the docs.
- Licensing: code MIT (the notice carries the repo URL, so forks point
  home), DESI data CC BY 4.0. Anyone redistributing the addons is bound by
  CC BY to credit DESI — that obligation is DESI's, not ours. Credit for
  this project is a request in the README, not a license term.
