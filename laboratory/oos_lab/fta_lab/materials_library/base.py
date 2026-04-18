"""
Materials Library - Unified Properties Database
-----------------------------------------------
Retrieves physical constants for conductors, insulators, and magnetic cores.
"""

from typing import Dict, Any, Optional

class MaterialsLibrary:
    """
    Interface to access material properties from configuration.
    """
    def __init__(self, config: Dict):
        self.materials = config.get('materials', {})
        
    def get_conductor(self, name: str = "copper") -> Dict[str, float]:
        """Get properties for a conductor material."""
        return self.materials.get(name, self.materials.get("copper", {}))
        
    def get_insulator(self, name: str = "sio2") -> Dict[str, float]:
        """Get properties for an insulator material."""
        return self.materials.get(name, self.materials.get("sio2", {}))
        
    def get_magnetic(self, name: str = "mu_metal") -> Dict[str, float]:
        """Get properties for a magnetic core material."""
        return self.materials.get(name, self.materials.get("mu_metal", {}))
