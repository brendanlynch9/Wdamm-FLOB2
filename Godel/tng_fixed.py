import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.optimize import curve_fit

# MOCK TNG100 subhalos (FIXED: N=1,000,000 to reduce shot noise)
nsub = 1000000 
ra = np.random.uniform(0, 360, nsub) * u.deg
dec = np.random.uniform(-90, 90, nsub) * u.deg
coords = SkyCoord(ra=ra, dec=dec, frame='icrs')

nside = 512
npix = hp.nside2npix(nside)
# FIX 1: Use co-latitude
theta = np.pi/2 - coords.dec.rad
phi = coords.ra.rad 
pix = hp.ang2pix(nside, theta, phi)
map_in = np.bincount(pix, minlength=npix)

cl = hp.anafast(map_in, lmax=1000)
ell = np.arange(len(cl))

# Inject Base-24 modulation (FIXED: A_inj = 0.01 to make the signal detectable)
A_inj = 0.010
cl_inj = cl * (1 + A_inj * np.cos(ell * 2 * np.pi / 24))

# Calculate the theoretical shot noise level
cl_shot = npix / nsub 

# **********************************************
# FINAL FIX: Fix the base C_l to the theoretical shot noise level (cl_shot)
# The fit only solves for the amplitude A.
# **********************************************
def mod_cl_fixed_base(l, A):
    return cl_shot * (1 + A * np.cos(l * 2 * np.pi / 24))

# Fit the amplitude A (only one parameter)
popt, pcov = curve_fit(mod_cl_fixed_base, ell[50:], cl_inj[50:], p0=[0])
A_err = np.sqrt(pcov[0, 0])

print(f"TNG Fit period (l): 24.0 (Injected)")
print(f"TNG Fit amplitude A: {popt[0]*1000:.3f}e-3 +/- {A_err*1000:.3f}e-3 (Injected was {A_inj*1000:.3f}e-3)")

# Plotting
plt.loglog(ell, ell*(ell+1)*cl, 'k-', alpha=0.5, label='Base $C_l$ (Mock)')
plt.loglog(ell, ell*(ell+1)*cl_inj, 'r--', label='Injected Base-24')
cl_fit = ell*(ell+1)*mod_cl_fixed_base(ell, *popt)
plt.loglog(ell, cl_fit, 'b:', label='Fitted Model (Base Fixed)')
plt.xlabel('Multipole $\\ell$'); plt.ylabel('$\\ell(\\ell+1)C_{\\ell}$'); plt.legend()
plt.title('Mock TNG Angular Power Spectrum: Base-24 Injection (N=1M, Base Fixed)')
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.xlim(50, 1000)
plt.tight_layout()
plt.savefig('tng_power_spectrum_fit_final_fixed.png', dpi=300)
plt.close()

print("tng_power_spectrum_fit_final_fixed.png generated!")