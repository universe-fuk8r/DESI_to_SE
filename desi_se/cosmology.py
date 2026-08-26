"""
Cosmology helpers.

We use DESI's fiducial flat LambdaCDM (Planck 2018-ish), which is the
cosmology DESI's pipeline assumes. SE wants distances in parsecs.

Choice of comoving vs luminosity distance: SE's Dist field for galaxies
is treated as a Euclidean spatial distance for placement and for the
inverse-square law in apparent magnitude rendering. Comoving distance
puts the object at its actual co-moving spatial location at the present
epoch, which is what the visualization is meant to show. Luminosity
distance is used internally by SE only when computing apparent
magnitude from absolute magnitude (which we precompute and feed in
directly via AbsMagn). So we use comoving distance.
"""

from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
import numpy as np

# DESI fiducial cosmology (matches Planck 2018 base flat LCDM, the choice
# DESI uses for its pipeline analyses)
DESI_COSMO = FlatLambdaCDM(H0=67.36, Om0=0.3145)


def z_to_distance_pc(z):
    """Comoving distance in parsecs for an array of redshifts.

    SE expects parsecs. astropy returns Mpc by default.
    Returns a numpy array.
    """
    z = np.asarray(z)
    # comoving_distance returns a Quantity in Mpc by default
    d_mpc = DESI_COSMO.comoving_distance(z).to(u.Mpc).value
    return d_mpc * 1.0e6  # parsecs


def z_to_luminosity_distance_pc(z):
    """Luminosity distance in parsecs (for AbsMagn from AppMagn)."""
    z = np.asarray(z)
    d_mpc = DESI_COSMO.luminosity_distance(z).to(u.Mpc).value
    return d_mpc * 1.0e6
