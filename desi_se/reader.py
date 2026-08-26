"""
DESI zcatalog FITS reader.

Reads the relevant columns from a zall-pix or zall-tile file (or a per-
survey zpix file) into a flat dict of numpy arrays. Defensive about
column name variants between different DESI releases (TARGET_RA vs RA,
etc.).
"""

import logging
import numpy as np
from astropy.io import fits

log = logging.getLogger(__name__)


def _decode_bytes(arr):
    """Decode and strip byte-string arrays from FITS (e.g. SPECTYPE)."""
    if arr.dtype.kind == 'S':
        return np.char.strip(np.char.decode(arr, encoding='ascii'))
    if arr.dtype.kind == 'U':
        return np.char.strip(arr)
    return arr


def _pick_column(hdu_data, candidates, required=True, default=None):
    """Find a column by trying alternative names. Returns None if not found
    and not required."""
    for c in candidates:
        if c in hdu_data.columns.names:
            return hdu_data[c]
    if required:
        raise KeyError(
            f"None of {candidates} found in HDU. "
            f"Available: {hdu_data.columns.names[:30]}..."
        )
    if default is not None:
        # broadcast a default scalar to the row count
        n = len(hdu_data)
        return np.full(n, default)
    return None


def read_zcatalog(path, hdu_name='ZCATALOG'):
    """
    Load DESI zpix/ztile catalog into a dict of arrays.

    Returns dict with keys:
        TARGETID, RA (deg), DEC (deg), Z, ZERR, ZWARN, SPECTYPE,
        FLUX_G, FLUX_R, FLUX_Z, FLUX_W1, FLUX_W2

    Missing flux columns are filled with NaN.
    """
    log.info(f"Opening {path}")
    with fits.open(path, memmap=True) as hdul:
        # Find the right HDU
        if hdu_name in [h.name for h in hdul]:
            hdu = hdul[hdu_name]
        else:
            # Fall back to first table HDU
            hdu = next(h for h in hdul if isinstance(h, fits.BinTableHDU))
            log.warning(f"HDU '{hdu_name}' not found, using {hdu.name}")
        data = hdu.data
        log.info(f"Reading {len(data):,} rows from HDU '{hdu.name}'")

        out = {
            'TARGETID': np.array(_pick_column(data, ['TARGETID']), dtype=np.int64),
            'RA':       np.array(_pick_column(data, ['TARGET_RA', 'RA']), dtype=np.float64),
            'DEC':      np.array(_pick_column(data, ['TARGET_DEC', 'DEC']), dtype=np.float64),
            'Z':        np.array(_pick_column(data, ['Z']), dtype=np.float64),
            'ZERR':     np.array(_pick_column(data, ['ZERR'], required=False, default=np.nan), dtype=np.float64),
            'ZWARN':    np.array(_pick_column(data, ['ZWARN']), dtype=np.int64),
            'SPECTYPE': _decode_bytes(np.array(_pick_column(data, ['SPECTYPE']))),
        }

        # Optional photometry
        for col in ['FLUX_G', 'FLUX_R', 'FLUX_Z', 'FLUX_W1', 'FLUX_W2']:
            arr = _pick_column(data, [col], required=False)
            if arr is None:
                out[col] = np.full(len(data), np.nan, dtype=np.float64)
            else:
                out[col] = np.array(arr, dtype=np.float64)

        # Primary-row flag for deduplication. DESI uses ZCAT_PRIMARY
        # (unique across all surveys) as the canonical "best row per
        # target". Older releases had MAIN_PRIMARY for the main survey
        # only. If neither is present we fall back to first-occurrence
        # dedup on TARGETID (handled in the filter stage).
        primary = _pick_column(data, ['ZCAT_PRIMARY', 'MAIN_PRIMARY'],
                               required=False)
        if primary is None:
            log.warning("No ZCAT_PRIMARY/MAIN_PRIMARY column - "
                        "falling back to TARGETID-based dedup")
            out['PRIMARY'] = np.zeros(len(data), dtype=bool)
            out['_HAS_PRIMARY'] = False
        else:
            out['PRIMARY'] = np.array(primary).astype(bool)
            out['_HAS_PRIMARY'] = True
            n_primary = int(out['PRIMARY'].sum())
            log.info(f"  primary-flag rows: {n_primary:,} "
                     f"({100*n_primary/len(data):.1f}%)")

    return out


def summarize(table):
    """Print a quick summary of what was loaded."""
    n = len(table['Z'])
    spectypes, counts = np.unique(table['SPECTYPE'], return_counts=True)
    log.info(f"Loaded {n:,} rows. SPECTYPE distribution:")
    for st, c in zip(spectypes, counts):
        log.info(f"  {st!r}: {c:,}")
    z = table['Z']
    log.info(f"  Z range: {np.nanmin(z):.4f} to {np.nanmax(z):.4f}")
    zwarn0 = (table['ZWARN'] == 0).sum()
    log.info(f"  ZWARN=0 (good): {zwarn0:,} ({100*zwarn0/n:.1f}%)")
