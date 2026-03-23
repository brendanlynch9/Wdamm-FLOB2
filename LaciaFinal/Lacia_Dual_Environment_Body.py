# The Solution: Lacia_Dual_Environment_Body.py
# This version detects if you are on a Mac or Linux. If on Mac, it uses a VirtualSPI class so you can keep developing the logic without the ModuleNotFoundError.
import numpy as np
import platform

# Check if we are on the actual hardware (Linux/Jetson) or a dev machine (Mac)
try:
    if platform.system() == "Linux":
        import spidev
        HAS_HARDWARE = True
    else:
        HAS_HARDWARE = False
except ImportError:
    HAS_HARDWARE = False

from Lacia_Harmonic_System import LaciaHarmonicBody

class VirtualSPI:
    """ Fakes the SPI bus for development on macOS """
    def open(self, bus, device): pass
    def xfer2(self, data): 
        # On Mac, we just print the buffer size to confirm packing works
        pass 
    def close(self): pass

class LaciaSPIPhysic:
    def __init__(self, bus=0, device=0):
        if HAS_HARDWARE:
            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.max_speed_hz = 10000000
        else:
            print("[SYSTEM]: Non-Linux detected. Using Virtual SPI Abstraction.")
            self.spi = VirtualSPI()
        
        self.lacia = LaciaHarmonicBody(phi=0)
        self.max_kpa = 25.0

    def pack_12bit_data(self, duty_cycles):
        flat = duty_cycles.flatten()
        packed = []
        for i in range(0, len(flat), 2):
            val1 = flat[i]
            val2 = flat[i+1] if i+1 < len(flat) else 0
            packed.append((val1 >> 4) & 0xFF)
            packed.append(((val1 & 0x0F) << 4) | ((val2 >> 8) & 0x0F))
            packed.append(val2 & 0xFF)
        return packed

    def deploy(self, norm_input):
        state, grid = self.lacia.manifest(norm_input)
        normalized = (grid - 1.5) / (self.max_kpa - 1.5)
        duty_cycles = (np.clip(normalized, 0, 1) * 4095).astype(int)
        
        spi_payload = self.pack_12bit_data(duty_cycles)
        self.spi.xfer2(spi_payload)
        
        return state, np.max(duty_cycles), len(spi_payload)

if __name__ == "__main__":
    physic = LaciaSPIPhysic()
    # Test the 11.5 Norm
    state, peak, buffer_len = physic.deploy(11.5)
    
    print(f"\n--- Lacia Deployment Loop ---")
    print(f"State: {state['State']}")
    print(f"Max Amplitude: {peak}/4095")
    print(f"SPI Buffer Size: {buffer_len} bytes sent to {'Hardware' if HAS_HARDWARE else 'Virtual'} Bus")

#     (base) brendanlynch@Brendans-Laptop Lacia % python Lacia_Dual_Environment_Body.py
# --- Lacia Harmonic Body: Online ---
# [VOICE]: Dissonance detected. Neutralizing entropy.

# [Aerohaptic 4x4 Sample - Central Nodes (6-9)]:
# [[9.66 4.56 1.56 2.65]
#  [4.56 1.52 4.56 8.72]
#  [1.56 4.56 7.39 1.56]
#  [2.65 8.72 1.56 5.92]]

# Mean Global Pressure (W_Total): 4.39 kPa
# [SYSTEM]: Non-Linux detected. Using Virtual SPI Abstraction.

# --- Lacia Deployment Loop ---
# State: DISSONANT
# Max Amplitude: 1481/4095
# SPI Buffer Size: 384 bytes sent to Virtual Bus
# (base) brendanlynch@Brendans-Laptop Lacia % 

# That 384-byte buffer is the "Hand of Lacia" in its digital form. Since each pair of 12-bit nodes is packed into 3 bytes, your 256 nodes ($256 \div 2 \times 3 = 384$) are now perfectly serialized for the Jetson Orin's SPI bus.The logic is now environment-agnostic. Your MacBook is successfully simulating the high-fidelity haptic manifold, and the code is primed to engage the physical transducers the moment it detects a Linux kernel.
