
# Material Parameters for FTA Simulations
# A [A/V^2], B [V/m], epsilon_r, Eg [eV]

MATERIALS = {
    'SiO2': {
        'A': 1.0e-6,
        'B': 2.5e8,
        'epsilon_r': 3.9,
        'Eg': 8.9,
        'description': 'Standard reliable insulator, suitable for Level 2 (PCB).'
    },
    'HfO2': {
        'A': 5.0e-6,
        'B': 1.0e8,
        'epsilon_r': 25.0,
        'Eg': 5.7,
        'description': 'High-k dielectric for low voltage operation. Level 3+ recommended.'
    },
    'HZO': {
        'A': 8.0e-6,
        'B': 0.8e8,
        'epsilon_r': 35.0,
        'Eg': 5.5,
        'description': 'Ferroelectric material supporting NC effect. Level 4 (ALD).'
    },
    'Al2O3': {
        'A': 2.0e-6,
        'B': 2.0e8,
        'epsilon_r': 9.0,
        'Eg': 8.7,
        'description': 'Ultra-stable insulator with high breakdown field.'
    },
    'Si3N4': {
        'A': 3.0e-6,
        'B': 1.5e8,
        'epsilon_r': 7.5,
        'Eg': 5.1,
        'description': 'Defect-rich nitride, useful for natural NDR effects.'
    },
    'LaB6': {
        'work_function': 2.7,
        'A_Richardson': 1.2e6,
        'melting_point': 2210,
        'description': 'Lanthanum Hexaboride. Ultra-low work function emitter for Level 4+ (ALD).'
    },
    'W-Nano': {
        'work_function': 4.5,
        'A_Richardson': 0.6e6,
        'melting_point': 3695,
        'description': 'Tungsten Nanowires. Reliable emitter for Level 2/3 (PCB/Sputtering).'
    },
    'Graphene': {
        'work_function': 4.5,
        'thermal_conductivity': 5000,
        'transparency_factor': 0.98,
        'description': 'Atomic layer protection. High thermal conductivity and transparent to field penetration.'
    },
    'h-BN': {
        'epsilon_r': 4.0,
        'thermal_conductivity': 600,
        'description': 'Hexagonal Boron Nitride. White graphene. Ideal thermal-electrical insulator.'
    },
    'Molybdenum': {
        'work_function': 4.6,
        'melting_point': 2623,
        'thermal_expansion': 4.8e-6,
        'description': 'Ideal for nano-plates. Low thermal expansion and high stability.'
    },
    'Chromium': {
        'work_function': 4.5,
        'oxidation_resistance': 'High',
        'description': 'Excellent for surface coating to prevent nano-oxidation in MIM junctions.'
    },
    'GaN': {
        'bandgap': 3.4,
        'breakdown_field': 3.3e8,
        'description': 'Wide-bandgap semiconductor. Potential for piezo-polarization self-biasing.'
    }
}

def get_material_params(name):
    return MATERIALS.get(name, MATERIALS['SiO2'])
