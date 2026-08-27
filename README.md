# desi-to-spaceengine

Convert DESI Data Release 1 redshift catalogs into SpaceEngine addons
that visualize the cosmic web from real spectroscopic data.

> **Looking to use the addon, not build it?**
> Grab a prebuilt tier from the
> [Releases](../../releases) page, unzip it into your SpaceEngine
> `addons/` directory, and launch. You don't need Python, the DESI
> source data, or anything else in this repo. See
> [Installing a prebuilt addon](#installing-a-prebuilt-addon).

## What this does

The Dark Energy Spectroscopic Instrument has measured spectroscopic
redshifts across about a third of the sky, out to redshift z > 5. After
quality cuts and deduplication, this tool extracts about 15.8 million
galaxies and quasars from DR1 (released March 2025). SpaceEngine ships
with about 10,000 catalog galaxies (NGC + IC). This tool builds a
bridge: take DESI's `zall-pix-iron.fits`, filter and transform it, write
the result as a drop-in SpaceEngine addon.

The output is a directory of catalog files SE loads at startup. No
runtime computation; the cosmology, magnitude derivation, and morphology
heuristic all happen here at build time.

## Tiers

Four tiers are produced from the same source data, differing only in
how aggressively they're filtered and subsampled. Each ships as a
separate release asset. **Install exactly one** — they overlap, so
installing two loads both and duplicates every shared object.

| Tier   | Galaxies | QSOs   | Download | RAM      | Notes                                   |
|--------|---------:|-------:|---------:|----------|-----------------------------------------|
| lite   |     250k |      0 |   6.7 MB | any      | BGS at z<0.4. Runs on anything.         |
| normal |     2.5M |      0 |    63 MB | 16 GB    | BGS+LRG+ELG to z~1.6. No QSOs.          |
| heavy  |       6M |   400k |   157 MB | 16-32 GB | Adds QSOs to z~3.                       |
| insane |    14.1M |  1.65M |   378 MB | 32 GB+   | Full DR1 main extragalactic. Wants RAM. |

Download size is also the on-disk size — the `.pak` stays packed, so
there's no unpacked catalog tree to store. (Uncompressed, the catalogs
would be 22 MB / 216 MB / 568 MB / 1.4 GB respectively.)

The RAM column is what SpaceEngine wants at runtime to load the tier;
building a tier yourself has its own, larger appetite (see
[Get the source data](#get-the-source-data)).

All tiers exclude objects below z=0.0033 (~14 Mpc) to avoid
peculiar-velocity-dominated objects, BGS stellar contamination, and
spurious low-z fits that would render as bright objects implausibly
close to Earth. Quality cut is `ZWARN==0` and `ZCAT_PRIMARY==True`
(or first-occurrence dedup if `ZCAT_PRIMARY` is missing).

## Installing a prebuilt addon

Prebuilt tiers are attached to [Releases](../../releases). No Python, no
DESI download, no build. Each tier comes two ways — pick either:

- **`DESI_DR1_<tier>.pak`** — the whole addon in one file, README and
  citations included. Drop it straight into your `addons` folder. That's
  the entire install: no folder to create, nothing to unpack.
- **`DESI_DR1_<tier>.zip`** — the same `.pak`, with the README and
  `CITATIONS.txt` also unpacked alongside it so you can read them without
  opening an archive. Unzip into `addons`, giving you
  `addons/DESI_DR1_<tier>/DESI_DR1_<tier>.pak` — which SE loads exactly
  the same as a bare `.pak`.

So the minimal install is just:

```
...\addons\DESI_DR1_heavy.pak
```

Then launch SpaceEngine. The catalog loads at startup — expect a
noticeably longer first launch on heavy and insane. **Leave the `.pak`
packed either way**; SE reads it as an archive.

As of SpaceEngine 0.991.50.2140 (May 2026) there are three locations SE
searches for addons:

```
%USERPROFILE%\Documents\Cosmographic\SpaceEngine\addons\    <- recommended
SpaceEngine\addons\    (Steam install folder)
SpaceEngine\data\
```

The Documents path is the recommended one, since Steam can overwrite the
install folder on update or file verification.

To uninstall, delete the folder. Nothing is written outside it.

If the addon doesn't appear: clear SE's cache by deleting
`%LOCALAPPDATA%\Cosmographic\SpaceEngine` and relaunch (SE rebuilds it),
and check `se.log` in SpaceEngine's system folder for catalog parse
errors.

## Building it yourself

Everything below is the build pipeline — only needed if you want to
change the filtering, re-tune the heuristics, or regenerate against a
future DESI release.

### Setup

Requires Python 3.10+ and:

```
pip install -r requirements.txt
```

(astropy, numpy, scipy. astropy's `comoving_distance` calls
`scipy.special.hyp2f1`, hence scipy.)

### Get the source data

Download `zall-pix-iron.fits` from the DESI public DR1 release:

```
https://data.desi.lbl.gov/public/dr1/spectro/redux/iron/zcatalog/v1/
```

The file is several GB. It's opened with memmap, but the columns the
converter needs are then materialized as numpy arrays, so peak memory
scales with the source row count, not just with the output size. Budget
several GB of headroom on top of the tier's output.

### Run

```
python convert.py --input zall-pix-iron.fits --tier heavy --output ./addons
```

Options:

```
  -i, --input PATH       DESI zpix/ztile FITS file
  -t, --tier {lite,normal,heavy,insane}
  -o, --output DIR       output root (default ./addons)
      --seed INT         RNG seed for reproducibility (default 42)
      --no-morphology    skip Hubble-type assignment (SE picks procedurally)
      --quiet
```

Each invocation produces one tier. To build all four:

```
for t in lite normal heavy insane; do
  python convert.py -i zall-pix-iron.fits -t $t -o ./addons
done
```

### Output structure

```
addons/DESI_DR1_<tier>/
  catalogs/
    galaxies/
      desi_galaxies.csv          # all galaxies
      desi_qsos.sc               # QSO hosts (heavy/insane only)
  README.md                      # end-user readme, generated from build metadata
  CITATIONS.txt                  # DESI acknowledgment text and license
```

The addon is self-contained. Drop the directory under
`SpaceEngine/addons/` and SE picks it up at next launch.

Note that `catalogs/` is **not** tracked in git — see `.gitignore`.
Every catalog file except lite's CSV is over GitHub's 100 MB per-file
limit, and they're all reproducible from this pipeline. The addon
`README.md` and `CITATIONS.txt` *are* tracked, so the repo records what
each tier ships without carrying two gigabytes of it.

### Test without downloading DESI

A mock-data generator is included. It produces a synthetic FITS with
the same column structure as DESI zpix:

```
python make_mock.py --n 100000 --out mock.fits
python convert.py -i mock.fits -t heavy -o ./test_out
```

Useful for verifying the converter is working end-to-end before
committing to the multi-GB real-data download.

### Packaging a release

`convert.py` writes loose `catalogs/` directories. Turning those into
release assets is a separate step:

```
./package_release.sh                # all four tiers
./package_release.sh lite heavy     # named tiers only
```

For each tier that produces two release assets in `dist/`:

```
DESI_DR1_<tier>.pak        # standalone, self-contained:
  catalogs/                #   the only root-level folder
  README.md                #   root-level files
  CITATIONS.txt
DESI_DR1_<tier>.zip        # the same .pak, plus loose copies of the
  DESI_DR1_<tier>/         #   two docs so they're readable without
    DESI_DR1_<tier>.pak    #   unpacking anything
    README.md
    CITATIONS.txt
```

`README.md` and `CITATIONS.txt` live inside the `.pak` as well as beside
it, so the DESI CC BY 4.0 attribution travels with the data no matter
which asset someone downloads. They're root-level *files*, which the
manual's subfolder restriction doesn't cover — only directories at the
pak root have to be standard SE names.

A bare `.pak` dropped into `addons/` is a complete, valid install, so
both forms are worth publishing — the `.pak` for people who just want it
working, the `.zip` for people who want to read the caveats without
opening an archive. The wrapper zip hardlinks the pak rather than copying
it, so producing both costs no extra compression time.

**The `.pak` internal layout is not arbitrary.** Per the
[SpaceEngine manual](https://spaceengine.org/manual/making-addons/):

> "The pak file cannot contain additional subfolders, only default ones
> are allowed."

The topmost entries inside a `.pak` must be standard SE folders
(`catalogs`, `models`, `textures`). Zipping the `DESI_DR1_<tier>`
directory itself puts a non-standard folder at the archive root and SE
silently won't load it — an easy and near-invisible mistake, so
`package_release.sh` asserts the `.pak` root is exactly `catalogs/`
before it finishes. The wrapper zip is stored uncompressed (`-0`),
because recompressing an already-compressed `.pak` costs minutes and
saves nothing.

Attach the four zips to a GitHub Release — all are far inside the 2 GB
per-asset limit. Release body copy for each tier is in
[RELEASE_NOTES.md](RELEASE_NOTES.md).

Note that the addon `README.md` describes the packaged `.pak` layout,
not the loose `catalogs/` tree that `convert.py` emits — it ships next
to the `.pak`, so by the time anyone reads it the packaging step has
already run.

## Design notes

A few decisions worth flagging if you're modifying this:

- **Quasars are emitted as `Quasar` blocks.** They appear in SE as
  quasar objects; galaxies arrive as galaxy objects via the CSV. SE
  generates the central BHs procedurally. Names retain the "DESI QSO"
  prefix for identification. An earlier revision switched these to
  `Galaxy` blocks to dodge suspected emission-region artifacts at high
  density; that was reverted, and `Quasar` is confirmed working in-game
  at insane-tier density (~1.6M blocks). Don't change the keyword
  without re-testing in SE at full scale.
- **No explicit accretion disks.** An earlier version derived BH masses
  and accretion rates for the brightest QSOs and emitted explicit
  `AccretionDisk` blocks. The derived rates were 5–7 orders of
  magnitude larger than stock SE values, producing nebula-sized disk
  artifacts. SE's procedural generation looks better.
- **Morphology heuristic.** DESI doesn't measure shape. Hubble types
  come from a redshift-conditioned probability distribution
  (`desi_se/morphology.py`). It's a plausibility heuristic, not
  measurement. Disable with `--no-morphology` if you'd rather SE
  procedurally pick.
- **Distance is comoving.** Comoving puts the object at its
  present-epoch spatial location, which is what the visualization
  shows. Luminosity distance is used internally for the apparent →
  absolute magnitude conversion only.
- **AbsMagn clamps.** Galaxies brighter than -24.5 and QSOs brighter
  than -29 are clamped. Anything intrinsically brighter is almost
  certainly a photometry artifact.
- **Identity quaternion in CSV.** Stock SE galaxies almost universally
  omit orientation. Random quats added visual noise without scientific
  basis.
- **`LogLevel 0` in SC files.** Suppresses per-object catalog-load
  warnings. Without it, insane tier produces ~300 MB of SE log spam.

## When DR2 lands

DESI DR2 is expected around spring 2027. This pipeline was written
against DR1 and is not being actively maintained against the DESI
roadmap, so here's what a DR2 update should actually involve, written
down while it's still fresh.

The good news: nothing in the filtering logic is DR1-specific.
`desi_se/tiers.py` cuts on `SPECTYPE`, `Z`, and `ZWARN` only, and
`desi_se/reader.py` already tries column-name alternatives
(`TARGET_RA`/`RA`, `ZCAT_PRIMARY`/`MAIN_PRIMARY`) precisely because
these drift between releases. Expect it to run largely as-is.

What will need attention:

- **The input filename and path.** `iron` is DR1's spectroscopic
  reduction codename; DR2 will have its own, so both the download URL
  and the `zall-pix-*.fits` filename change. Nothing hardcodes it —
  it's a `--input` argument — but every doc example names the DR1 file.
- **Object counts, everywhere.** DR2 roughly doubles DR1's spectra. The
  counts appear in this README's tier table, `convert.py`'s module
  docstring, the `description` field of each tier in `desi_se/tiers.py`
  (which is interpolated into the generated addon README), and
  `RELEASE_NOTES.md`. Rebuild first, then propagate the real numbers
  from the build log rather than estimating.
- **RAM guidance, not tier caps.** lite/normal/heavy are subsample-
  capped, so their output size is unchanged by a bigger source catalog;
  only their sampling gets sparser. `insane` is deliberately uncapped —
  it is defined as "the full deduplicated catalog, whatever that costs,"
  and that is the entire point of the tier. When DR2 makes it bigger,
  update the RAM numbers in the tier table and in `RELEASE_NOTES.md`.
  Do not add a cap.
- **Peak build memory scales with source rows for every tier**, because
  `reader.py` materializes full columns before filtering. A doubled DR2
  catalog roughly doubles the build machine's requirement even if you
  only want the lite tier.
- **Re-verify in SpaceEngine at full scale** before releasing. The
  `Quasar`-block decision in the design notes above is confirmed only
  at DR1 insane density (~1.6M blocks); doubling that is untested
  territory.
- **Rename to `DESI_DR2_<tier>`** so a DR2 addon can coexist with an
  installed DR1 one instead of half-overwriting it. The `DESI_DR1_`
  prefix is a hardcoded literal in three places in `convert.py`: the
  output path (`convert.py:182`), the install-path example in the
  generated addon README, and the module docstring.

## Citations

If you use this in published work or videos, cite:

- DESI Collaboration et al. (2025), "Data Release 1 of the Dark Energy
  Spectroscopic Instrument", arXiv:2503.14745.

Each generated addon includes a `CITATIONS.txt` with the full DESI
acknowledgment text per their data policy.

## License

This code: MIT (see `LICENSE`).
DESI DR1 data this code processes: CC BY 4.0 (DESI Collaboration).
SpaceEngine itself: proprietary, by Cosmographic Software.

MIT requires the copyright notice — which includes this repo's URL — to
be kept in copies and modified versions, so a fork carries a pointer
back here by default.

If you re-host the built addons somewhere else, a link back to this repo
is appreciated so people can find the build pipeline and the DESI
citations. That's a request, not a condition. Do note that the addons
contain DESI data, and CC BY 4.0 requires you to credit DESI wherever
they end up — see `CITATIONS.txt` inside each `.pak`.

This project is not affiliated with the DESI collaboration or with
SpaceEngine / Cosmographic Software. It's a community contribution
that uses both via their public APIs and addon system.
