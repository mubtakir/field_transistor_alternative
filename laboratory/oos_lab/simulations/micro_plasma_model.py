import numpy as np

def simulate_micro_plasma_ion_propulsion(input_voltage_v, gas_type='Argon'):
    """
    نموذج تأيين الغاز في الفجوة النانوية (مُحرك أيوني ميكروي).
    
    مصفوفات النانو-FTA يمكنها توليد مجالات قوية كافية لتأيين جزيئات الغاز
    في الفجوة (10 نانومتر) حتى عند ضغوط منخفضة جداً.
    """
    ionization_potentials = {'Argon': 15.76, 'Air': 14.5}
    
    if input_voltage_v > ionization_potentials[gas_type]:
        return "Ionization Detected: Micro-plasma Formation"
    else:
        return "Steady-state Tunneling Mode: No Ionization"

if __name__ == "__main__":
    print("--- Nano-Propulsion Micro-plasma Analysis ---")
    status = simulate_micro_plasma_ion_propulsion(25.0)
    print(f"Propulsion State: {status}")
