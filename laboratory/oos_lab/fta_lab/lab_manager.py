#!/usr/bin/env python3
"""
FTA Virtual Laboratory v1.0 - Central Orchestrator (lab_manager.py)
------------------------------------------------------------------
Author: Basel Yahya Abdullah | March 2026
Project: Field Transistor Alternative (FTA) Research
"""

import os
import sys
import yaml
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Ensure UTF-8 for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class FTALaboratory:
    """
    The orchestrator for the Virtual Laboratory.
    Manages device creation, simulation execution, and result archiving.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the lab environment."""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        config_full_path = os.path.join(self.base_dir, config_path)
        
        self.config = self._load_config(config_full_path)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
        self.device_under_test = None
        
        # Setup paths
        self._init_directories()
        
        print("=" * 60)
        print(f"FTA Virtual Laboratory v1.0 - Unified Physics Workspace")
        print(f"Session: {self.session_id}")
        print(f"Hardware: {self.config.get('hardware', {}).get('taichi_arch', 'cpu').upper()}")
        print("=" * 60)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration or use defaults."""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            print(f"[Warning] Config not found at {config_path}. Using internal defaults.")
            return {
                "simulation": {"default_resolution": [120, 100]},
                "hardware": {"use_gpu": False}
            }
    
    def _init_directories(self):
        """Ensure output directories exist."""
        for d in ['outputs/plots', 'outputs/data', 'outputs/reports']:
            os.makedirs(os.path.join(self.base_dir, d), exist_ok=True)
    
    def create_device(self, device_type: str, geometry: Dict, **kwargs) -> Any:
        """
        Instantiate a device model for testing.
        
        Args:
            device_type: 'u_plate', 'differential', etc.
            geometry: Dictionary of physical dimensions.
        """
        print(f"\n[DEVICE] Creating {device_type} architecture...")
        
        if device_type == 'u_plate':
            try:
                from .device_models.u_plate_fta import UPlateFTA
                self.device_under_test = UPlateFTA(geometry, **kwargs)
                return self.device_under_test
            except ImportError:
                print("[Error] UPlateFTA model not found in device_models.")
                return None
        elif device_type == 'nested_inductor':
            try:
                from .device_models.nested_inductor_fta import NestedInductorFTA
                self.device_under_test = NestedInductorFTA(geometry, **kwargs)
                return self.device_under_test
            except ImportError:
                print("[Error] NestedInductorFTA model not found in device_models.")
                return None
        else:
            print(f"[Error] Untested device type: {device_type}")
            return None

    def run_analysis(self, analysis_type: str, params: Dict) -> Dict:
        """
        Execute a specific simulation analysis.
        """
        if self.device_under_test is None:
            raise RuntimeError("No active device to analyze.")
            
        print(f"[ANALYZE] Running {analysis_type} sweep...")
        
        # Mapping to analyzer modules (Phase 4)
        # For now, we will placeholder the calls
        return {"status": "success", "type": analysis_type}

    def save_session(self):
        """Archive technical data and metadata."""
        print(f"[ARCHIVE] Saving session {self.session_id} to outputs/data/")
        # Implementation for saving state
        
    def summary(self):
        """Display current lab status."""
        print(f"\nLab Status:")
        print(f"  - Device: {self.device_under_test if self.device_under_test else 'Empty'}")
        print(f"  - Session Data: {len(self.results)} analyses cached.")

if __name__ == "__main__":
    lab = FTALaboratory()
    lab.summary()
