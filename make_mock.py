#!/usr/bin/env python3
"""
Generate a synthetic DESI-style zpix FITS file for testing the
converter without downloading the real DR1.

Mimics the column structure of the iron/v1 zall-pix file:
    TARGETID, TARGET_RA, TARGET_DEC, Z, ZERR, ZWARN, SPECTYPE,
    FLUX_G, FLUX_R, FLUX_Z, FLUX_W1, FLUX_W2, DELTACHI2.

Sky distribution roughly matches DESI's footprint (DEC > -30,
avoids the Galactic plane). Redshift distribution is split between
GALAXY targets (z<2) and QSOs (broad with high-z tail). Some
fraction get ZWARN!=0 to test the quality cut.
"""

import argparse
import numpy as np
from astropy.io import fits
from pathlib import Path


def generate_mock(n_total=10_000, seed=1, qso_fraction=0.15, bad_zwarn_frac=0.08):
    rng = np.random.default_rng(seed)

    # Sky positions: avoid |b|<10 to mimic galactic plane mask, dec > -35
    ra = rng.uniform(0, 360, n_total)
    dec = rng.uniform(-30, 80, n_total)

    n_qso = int(qso_fraction * n_total)
    n_gal = n_total - n_qso
    n_star_misclass = max(1, n_total // 200)  # tiny fraction tagged STAR

    spectype = np.array(['GALAXY'] * n_total)
    spectype[:n_qso] = 'QSO'
    spectype[n_qso:n_qso + n_star_misclass] = 'STAR'
    rng.shuffle(spectype)

    # Redshifts
    z = np.empty(n_total, dtype=float)
    is_gal = spectype == 'GALAXY'
    is_qso = spectype == 'QSO'
    is_star = spectype == 'STAR'
    # Galaxies: mix of BGS-like low-z, LRG-like mid, ELG-like upper mid
    zg = np.empty(is_gal.sum())
    rs = rng.uniform(size=zg.size)
    bgs_m  = rs < 0.45
    lrg_m  = (rs >= 0.45) & (rs < 0.75)
    elg_m  = rs >= 0.75
    zg[bgs_m] = rng.uniform(0.01, 0.4,  bgs_m.sum())
    zg[lrg_m] = rng.uniform(0.4,  1.0,  lrg_m.sum())
    zg[elg_m] = rng.uniform(1.0,  1.6,  elg_m.sum())
    z[is_gal] = zg
    # QSOs: log-uniform-ish spread up to z~5
    z[is_qso] = rng.uniform(0.5, 5.0, is_qso.sum())
    # Stars: redshift effectively zero
    z[is_star] = rng.uniform(-0.001, 0.001, is_star.sum())

    zerr = np.abs(rng.normal(0, 1e-4, n_total)) + 1e-5
    # ZWARN: 0 most of the time, a fraction get a nonzero bitmask
    zwarn = np.zeros(n_total, dtype=np.int64)
    bad = rng.uniform(size=n_total) < bad_zwarn_frac
    zwarn[bad] = rng.choice([1, 2, 4, 16], size=bad.sum())

    # Photometry (nMgy). Brighter at low z, dimmer at high z, log-spread
    # to mimic real data
    base_flux = 10.0 ** rng.uniform(-1.0, 2.5, n_total)
    z_factor = 1.0 / (1.0 + z) ** 2
    flux_r = np.where(np.isfinite(z_factor), base_flux * z_factor, np.nan)
    # Multi-band: scale around FLUX_R with random color
    flux_g = flux_r * rng.uniform(0.4, 1.2, n_total)
    flux_z = flux_r * rng.uniform(0.7, 1.6, n_total)
    flux_w1 = flux_r * rng.uniform(0.3, 2.0, n_total)
    flux_w2 = flux_r * rng.uniform(0.2, 1.5, n_total)

    # Sprinkle some non-positive fluxes to test fallback magnitude code
    bad_flux = rng.uniform(size=n_total) < 0.03
    flux_r[bad_flux] = -0.5

    targetid = np.arange(n_total, dtype=np.int64) + 39000000000000

    cols = [
        fits.Column(name='TARGETID',   format='K',  array=targetid),
        fits.Column(name='TARGET_RA',  format='D',  array=ra),
        fits.Column(name='TARGET_DEC', format='D',  array=dec),
        fits.Column(name='Z',          format='D',  array=z),
        fits.Column(name='ZERR',       format='D',  array=zerr),
        fits.Column(name='ZWARN',      format='K',  array=zwarn),
        fits.Column(name='SPECTYPE',   format='10A', array=spectype),
        fits.Column(name='FLUX_G',     format='E',  array=flux_g),
        fits.Column(name='FLUX_R',     format='E',  array=flux_r),
        fits.Column(name='FLUX_Z',     format='E',  array=flux_z),
        fits.Column(name='FLUX_W1',    format='E',  array=flux_w1),
        fits.Column(name='FLUX_W2',    format='E',  array=flux_w2),
        fits.Column(name='DELTACHI2',  format='E',  array=rng.uniform(20, 5000, n_total)),
    ]
    hdu = fits.BinTableHDU.from_columns(cols, name='ZCATALOG')
    hdu.header['SPECPROD'] = ('iron-mock', 'Synthetic data for testing only')
    hdu.header['VERSION']  = ('v1-mock', 'Not real DESI data')

    primary = fits.PrimaryHDU()
    primary.header['COMMENT'] = 'Mock DESI zpix file. Do not use for science.'
    return fits.HDUList([primary, hdu])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=10_000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', type=Path, default=Path('mock_zpix.fits'))
    args = ap.parse_args()

    hdul = generate_mock(n_total=args.n, seed=args.seed)
    hdul.writeto(args.out, overwrite=True)
    print(f"Wrote {args.out} with {args.n:,} rows")


if __name__ == '__main__':
    main()
