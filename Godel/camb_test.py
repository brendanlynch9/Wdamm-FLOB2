import camb
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Planck fiducial
pars = camb.CAMBparams()
pars.set_cosmology(H0=67.4, ombh2=0.0224, omch2=0.120, mnu=0.06, omk=0, tau=0.054)
pars.InitPower.set_params(As=2.1e-9, ns=0.965, r=0)
pars.set_for_lmax(2500, lens_potential_accuracy=0)

# Base-24 mod: P(k) [1 + ε cos(log k / log 24)]
def mod_pk(k, z, pk):
    logk = np.log10(k)
    return pk * (1 + 0.03 * np.cos(logk / np.log10(24)))

results = camb.get_results(pars)
powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')
base_cl = powers['total'][:,0]  # TT

ell = np.arange(len(base_cl))

# Injected (mock via post-hoc injection on low-ℓ)
A_inj = 0.03
injected_cl = base_cl * (1 + A_inj * np.cos(ell * 2 * np.pi / 24))

# *****************************************************************
# FIX: Use Ratio Fit to stabilize against the complex base C_l shape
# *****************************************************************
modulation_factor = injected_cl / base_cl

def fit_modulation(ell, A, period):
    # This models the modulation factor: C_l_inj / C_l_base = 1 + A * cos(ell * 2 * pi / period)
    return 1 + A * np.cos(ell * 2 * np.pi / period)

# Limit the fit to a stable range (l=50 to l=400)
ell_fit = ell[50:401]
mod_factor_fit = modulation_factor[50:401]

# Fit amplitude A and period (24)
popt, pcov = curve_fit(fit_modulation, ell_fit, mod_factor_fit, p0=[A_inj, 24], maxfev=5000)
perr = np.sqrt(np.diag(pcov))

print(f"Fit period: {popt[1]:.1f} ± {perr[1]:.1f}")
print(f"Fit amplitude A: {popt[0]*1000:.1f}e-3 ± {perr[0]*1000:.1f}e-3 (Injected was {A_inj*1000:.1f}e-3)")


# *****************************************************************
# FIX: Skip the ill-defined l=0, 1 for residual calculation
# *****************************************************************
ell_plot = ell[2:]
base_cl_plot = base_cl[2:]
injected_cl_plot = injected_cl[2:]

residual = (injected_cl_plot - base_cl_plot) / base_cl_plot

plt.figure(figsize=(8, 6))
plt.loglog(ell_plot, np.abs(residual), 'o', markersize=2, label='Injected $|\Delta C_{\\ell}/C_{\\ell}|$')
plt.axhline(0.005, color='gray', linestyle='--', label='Planck Sens (95% CL)')
plt.xlabel('Multipole $\\ell$'); plt.ylabel('$|\\Delta C_{\\ell}/C_{\\ell}|$'); plt.legend()
plt.title('CMB Power Spectrum: Base-24 Harmonic Residuals')
plt.grid(True, which="both", ls=":", alpha=0.7)
plt.xlim(2, 2500)
plt.tight_layout()
plt.savefig('camb_mod_final.pdf')
plt.close()

print("camb_mod_final.pdf generated!")