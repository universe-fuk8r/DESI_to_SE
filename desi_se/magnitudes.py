"""
Magnitude helpers.

DESI Legacy Imaging photometry is in nanomaggies (nMgy). Convert to AB
apparent magnitude with:
    m_AB = 22.5 - 2.5 * log10(flux_nmgy)

Absolute magnitude:
    M = m_AB - 5 * log10(D_L_pc / 10) - K_corr

We skip K-correction for v1; this introduces a few-tenths-of-a-mag
error at moderate z, growing to ~1 mag at z~1.5+. Fine for a
visualization, well below SE's rendering tolerance for galaxy
brightness.
"""

import numpy as np


def flux_nmgy_to_appmag(flux_nmgy):
    """nanomaggies -> AB apparent magnitude. Returns NaN where flux<=0."""
    flux = np.asarray(flux_nmgy, dtype=float)
    out = np.full_like(flux, np.nan, dtype=float)
    valid = flux > 0
    out[valid] = 22.5 - 2.5 * np.log10(flux[valid])
    return out


def appmag_to_absmag(m_app, d_lum_pc):
    """Distance modulus conversion. NaN-safe."""
    m_app = np.asarray(m_app, dtype=float)
    d_lum_pc = np.asarray(d_lum_pc, dtype=float)
    out = np.full_like(m_app, np.nan, dtype=float)
    valid = (~np.isnan(m_app)) & (d_lum_pc > 0)
    out[valid] = m_app[valid] - 5.0 * np.log10(d_lum_pc[valid] / 10.0)
    return out


def fallback_absmag_by_z(z, spectype):
    """
    Per-redshift-bin fallback absolute magnitude when photometry is missing.

    These are crude population medians informed by DESI target-selection
    biases (BGS, LRG, ELG, QSO). NOT measured values - a plausibility
    heuristic to give SE a sensible brightness when FLUX_R is missing.
    """
    z = np.asarray(z, dtype=float)
    spectype = np.asarray(spectype)
    out = np.full(z.shape, -20.5)  # generic galaxy default

    # Galaxy population medians by z bin
    is_gal = spectype == 'GALAXY'
    out[is_gal & (z < 0.1)] = -20.0
    out[is_gal & (z >= 0.1) & (z < 0.4)] = -20.8
    out[is_gal & (z >= 0.4) & (z < 1.0)] = -21.5  # LRGs are luminous
    out[is_gal & (z >= 1.0) & (z < 1.6)] = -21.8  # ELGs at high z must be bright to be seen
    out[is_gal & (z >= 1.6)] = -22.5

    # Quasars are intrinsically much brighter
    is_qso = spectype == 'QSO'
    out[is_qso & (z < 1.0)] = -23.0
    out[is_qso & (z >= 1.0) & (z < 2.5)] = -25.0
    out[is_qso & (z >= 2.5) & (z < 4.0)] = -26.5
    out[is_qso & (z >= 4.0)] = -27.5

    return out


def clamp_absmag(absmag, spectype, gal_brightest=-24.5, qso_brightest=-29.0,
                 faintest=-12.0):
    """
    Clamp absolute magnitudes to physically plausible ranges.

    Galaxies brighter than ~M_r = -24 are vanishingly rare; brightest
    cluster galaxies sit near -23.5. Anything intrinsically brighter is
    almost certainly a photometry artifact (foreground star contamination,
    wrong-z fit, blended source).

    QSOs legitimately reach -27 to -28 at high z; we use -29 as the
    upper limit, which is just past the most extreme known quasars.

    The faint end -12 prevents unphysically dim "galaxies" from
    showing up as missing render objects.
    """
    absmag = np.asarray(absmag, dtype=float).copy()
    spectype = np.asarray(spectype)
    is_qso = spectype == 'QSO'
    is_gal = ~is_qso
    # Brightest end (most negative)
    np.clip(absmag, gal_brightest, faintest, out=absmag, where=is_gal)
    np.clip(absmag, qso_brightest, faintest, out=absmag, where=is_qso)
    return absmag


def luminosity_solar_from_absmag(M, M_sun=4.83):
    """L / L_sun from absolute magnitude (V-band, M_sun=4.83 default)."""
    M = np.asarray(M, dtype=float)
    return 10.0 ** (-0.4 * (M - M_sun))


def bolometric_luminosity_erg_per_s(L_solar, bol_correction=10.0):
    """
    Bolometric luminosity in erg/s.

    Using BC ~ 10 for QSOs (Richards+2006 ballpark). For galaxies a BC
    of ~1.5 is more appropriate, but this function is mainly used for
    showcase QSO BH-mass estimation.
    """
    L_sun_erg = 3.828e33  # erg/s
    return L_solar * bol_correction * L_sun_erg
