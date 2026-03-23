# my_theory_model.py

import numpy as np
from cobaya.theory import Theory
from cobaya.theory import CosmologySettings
from cobaya.likelihoods.base_classes import PlanckLikelihoods

# Note: This class must calculate the theoretical C_l spectrum,
# potentially by calling an external Boltzmann code (like CLASS) and then
# applying your specific UFT-F/Base-24 modification.

class UFTF_CMB_Theory(Theory):
    """
    A custom theoretical model class for Cobaya, implementing the
    Base-24 CMB modifications to the primordial power spectrum.
    """
    # Define which results the likelihoods will ask for (in this case, C_l)
    # The cosmological parameters needed by this theory are also defined here.
    # Note: We must ensure this theory is run *after* the base cosmology (e.g., CLASS).
    
    # Required products: typically the C_l for TT, EE, TE, PP, etc.
    # We require the standard ones used by Planck.
    requires = {'Cl': {'tt': None, 'ee': None, 'te': None, 'bb': None, 'pp': None, 'nnu': None, 'r': None}}

    # The parameters that this specific custom theory introduces (e.g., your new Base-24 parameter)
    # The values will be passed from the main YAML file.
    input_params = ['A_base24', 'k_base24']

    def initialize(self):
        """
        Called once at the start. Initialize your Base-24 modification code here.
        If you use CLASS for the base C_l, you would initialize it here, but
        for simplicity, we assume you'll modify the C_l output from another theory
        that runs before this one (like the built-in 'camb' or 'classy' in Cobaya).
        """
        print("UFTF_CMB_Theory initialized. Ready to apply Base-24 modifications.")

    def calculate(self, state, want_derived=False, **params_values):
        """
        Calculates the theoretical Cls.

        Args:
            state: The dictionary holding results from previous theories (like base cosmology).
            params_values: Dictionary of current parameter values (e.g., 'A_base24').
        """
        # 1. Get the base Cls from a preceding theory (e.g., CLASS/CAMB)
        # Cobaya automatically handles running theories in order of dependencies.
        try:
            Cls_base = state['Cl']
        except KeyError:
            # Handle case where the preceding theory (e.g., CLASS) hasn't run or failed
            raise RuntimeError("Could not find base Cls. Ensure 'classy' or 'camb' is in 'theory' block of YAML.")

        # 2. Extract your model parameters
        A_base24 = params_values.get('A_base24')
        k_base24 = params_values.get('k_base24')

        # 3. Apply your Base-24 Modification
        # This is where you would implement the "log-periodic modifications"
        # as described in your 'dark_matter.pdf'. This is a placeholder logic:
        
        # Create a modified C_l dictionary
        Cls_modified = {}
        for spectrum_type, Cl_array in Cls_base.items():
            # Only modify the temperature and polarization spectra
            if spectrum_type in ['tt', 'ee', 'te']:
                # The 'ell' (multipole) values are needed for the modification.
                # Assume the first element of Cl_array is for ell=0, second for ell=1, etc.
                ell = np.arange(len(Cl_array))

                # --- Core Modification Logic Placeholder ---
                # Example: log-periodic oscillation on the spectrum
                modification_factor = 1 + A_base24 * np.sin(k_base24 * np.log(ell + 1e-10))

                Cls_modified[spectrum_type] = Cl_array * modification_factor
            else:
                Cls_modified[spectrum_type] = Cl_array # Pass through other spectra (like lensing phi-phi)

        # 4. Store the modified C_l in the state dictionary for the likelihood
        # This overwrites the base C_l with your modified C_l.
        state['Cl'] = Cls_modified

        return Cls_modified

    def get_Cl(self, **params_values):
        """
        Required method by Cobaya for C_l providers.
        The results are calculated in the 'calculate' method and stored in the state.
        We retrieve them from the state's result cache.
        """
        return self.current_state['Cl']

    # We must define the path to this module so Cobaya can find it when using the YAML
    def get_desc(self):
        return 'UFTF_CMB_Theory implementation'