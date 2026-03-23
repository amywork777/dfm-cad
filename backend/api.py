"""
DFM-CAD API Server

Endpoints:
- GET / - serve frontend
- POST /generate - text and/or image input → 3D model
- POST /iterate - modify existing model
- GET /model/{id}/preview - STL for 3D viewer
- GET /model/{id}/download - STEP/STL download
"""

import os
import uuid
import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.codegen import generate_cadquery_code, generate_cadquery_code_with_image
from agent.executor import execute_cadquery
from dfm.validator import validate_geometry
from dfm.analyzer import analyze_geometry

app = FastAPI(title="DFM-CAD API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for generated models
MODELS_DIR = Path("outputs")
MODELS_DIR.mkdir(exist_ok=True)

# In-memory model registry
model_registry = {}


class IterateRequest(BaseModel):
    model_id: str
    modification: str


@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/generate")
async def generate_model(
    prompt: str = Form(...),
    process: str = Form("cnc_milling"),
    material: str = Form("aluminum_6061"),
    image: Optional[UploadFile] = File(None)
):
    """Generate a 3D model from text and/or image input."""
    model_id = str(uuid.uuid4())[:8]
    
    constraints = {
        "material": material,
        "process": process,
        "units": "mm"
    }
    
    # Handle image input
    image_data = None
    image_type = None
    if image:
        image_bytes = await image.read()
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        image_type = image.content_type or "image/png"
    
    # Generate code (with retry)
    max_retries = 3
    code = None
    step_path = None
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if image_data:
                code = generate_cadquery_code_with_image(
                    prompt=prompt,
                    image_data=image_data,
                    image_type=image_type,
                    constraints=constraints,
                    previous_code=code if attempt > 0 else None,
                    previous_error=last_error
                )
            else:
                code = generate_cadquery_code(
                    task_description=prompt,
                    constraints=constraints,
                    previous_code=code if attempt > 0 else None,
                    previous_error=last_error
                )
            
            result = execute_cadquery(code)
            
            if result["success"]:
                step_path = result["step_path"]
                break
            else:
                last_error = result["error"]
                
        except Exception as e:
            last_error = str(e)
    
    if not step_path:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate model: {last_error}"
        )
    
    # Validate DFM
    dfm_result = validate_geometry(step_path, process=process, constraints=constraints)
    
    # Analyze geometry
    geometry = analyze_geometry(step_path)
    
    # Export STL for preview
    stl_path = None
    try:
        import cadquery as cq
        wp = cq.importers.importStep(step_path)
        stl_path = str(MODELS_DIR / f"{model_id}.stl")
        cq.exporters.export(wp, stl_path)
    except Exception as e:
        print(f"STL export failed: {e}")
    
    # Store model info
    model_registry[model_id] = {
        "id": model_id,
        "prompt": prompt,
        "process": process,
        "material": material,
        "step_path": step_path,
        "stl_path": stl_path,
        "code": code,
        "dfm": dfm_result,
        "geometry": geometry
    }
    
    return {
        "model_id": model_id,
        "preview_url": f"/model/{model_id}/preview",
        "download_url": f"/model/{model_id}/download",
        "dfm_passed": dfm_result["passed"],
        "dfm_warnings": dfm_result["warnings"],
        "geometry": {
            "volume_mm3": geometry["volume_mm3"],
            "bounding_box": geometry["bounding_box"],
            "faces": geometry["num_faces"],
            "holes": len(geometry["holes"]),
            "fillets": len(geometry["fillets"])
        }
    }


@app.post("/iterate")
async def iterate_model(request: IterateRequest):
    """Modify an existing model based on user feedback."""
    if request.model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")
    
    original = model_registry[request.model_id]
    
    new_prompt = f"""Original: {original['prompt']}
Previous code:
{original['code']}

Modification requested: {request.modification}
Generate updated CadQuery code."""
    
    return await generate_model(
        prompt=new_prompt,
        process=original["process"],
        material=original["material"]
    )


@app.get("/model/{model_id}/preview")
async def get_preview(model_id: str):
    """Serve STL file for 3D preview."""
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")
    
    stl_path = model_registry[model_id].get("stl_path")
    if not stl_path or not Path(stl_path).exists():
        raise HTTPException(status_code=404, detail="Preview not available")
    
    return FileResponse(stl_path, media_type="application/octet-stream")


@app.get("/model/{model_id}/download")
async def download_model(model_id: str, format: str = "step"):
    """Download model in STEP or STL format."""
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = model_registry[model_id]
    
    if format == "step":
        path = model.get("step_path")
        filename = f"{model_id}.step"
    else:
        path = model.get("stl_path")
        filename = f"{model_id}.stl"
    
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="File not available")
    
    return FileResponse(path, filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
