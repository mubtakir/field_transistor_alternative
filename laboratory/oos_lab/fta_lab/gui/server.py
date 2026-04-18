from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import sys

# Add parent directory for fta_lab imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fta_lab.lab_manager import FTALaboratory
from fta_lab.analyzers import IVAnalyzer, FrequencyAnalyzer, DynamicAnalyzer

app = FastAPI(title="FTA Virtual Laboratory v1.1 Supreme API")

# Initialize Lab
lab = FTALaboratory()

# Request Models
class Geometry(BaseModel):
    length: float = 100e-6
    width: float = 10e-6
    gap: float = 5e-9
    eps_r: float = 4.0

class SimulationRequest(BaseModel):
    device_type: str = "u_plate"
    geometry: Geometry
    v_dd: float = 50.0
    v_gate_range: List[float] = [0.0, 10.0, 20]

class DynamicRequest(BaseModel):
    device_type: str = "nested_inductor"
    geometry: Geometry
    v_source: float = 50.0
    v_drain: float = 0.0
    pulse_high: float = 1.0
    pulse_duration_ns: float = 100.0

@app.get("/api/config")
async def get_config():
    return lab.config

@app.post("/api/simulate/iv")
async def simulate_iv(req: SimulationRequest):
    try:
        device = lab.create_device(
            device_type=req.device_type,
            geometry=req.geometry.dict(),
            V_DD=req.v_dd
        )
        if not device:
            raise HTTPException(status_code=400, detail="Device creation failed")
            
        iva = IVAnalyzer(lab.config)
        res = iva.run_sweep(device, (req.v_gate_range[0], req.v_gate_range[1], int(req.v_gate_range[2])))
        
        return {
            "vg": res['vg'].tolist(),
            "id": res['id'].tolist(),
            "vd": res['vd'].tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate/dynamic")
async def simulate_dynamic(req: DynamicRequest):
    try:
        device = lab.create_device(
            device_type=req.device_type,
            geometry=req.geometry.dict()
        )
        if not device:
            raise HTTPException(status_code=400, detail="Device creation failed")
            
        analyzer = DynamicAnalyzer(lab.config)
        res = analyzer.run_pulse_test(device, {
            "v_high": req.pulse_high,
            "duration_ns": req.pulse_duration_ns
        })
        
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/materials")
async def get_materials():
    return lab.config.get('materials', {})

# Serve Static Files (Frontend)
gui_dir = os.path.dirname(os.path.abspath(__file__))
# Note: In production, we would use a more robust path, but for now we mount the current dir.
app.mount("/", StaticFiles(directory=gui_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
