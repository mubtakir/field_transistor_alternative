import numpy as np

def simulate_thermal_balance(input_power_w, cooling_rate_w, area_m2):
    """
    سكون التوازن الحراري (Heat Scavenging) لمصفوفة FTA.
    
    هذا النموذج يحاكي التوازن الحراري في المُبعث الهجين حيث يتم تحويل الطاقة الحرارية الجوهرية
    إلى تيار كهربائي (تبريد الإلكترونات).
    """
    # ظاهرة تبريد الإلكترونات (Electron Cooling)
    # كل إلكترون مغادر يحمل معه متوسط طاقة (phi + 2kBT)
    # هذا يقلل من الطاقة الحرارية الكلية للجهاز.
    
    net_heat_flow = input_power_w - cooling_rate_w
    equilibrium_temp = 300 + (net_heat_flow / (area_m2 * 10.0)) # فرضية خطية للتبديد
    
    return max(300.0, equilibrium_temp)

if __name__ == "__main__":
    print("--- Thermal Balance Simulation (QTMS) ---")
    res = simulate_thermal_balance(input_power_w=5.0, cooling_rate_w=3.2, area_m2=1e-6)
    print(f"Equilibrium Temperature: {res:.2f} K")
