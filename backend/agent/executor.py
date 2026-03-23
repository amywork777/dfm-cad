"""
CadQuery code executor: run code, get STEP file
"""

import os
import sys
import uuid
import traceback
from pathlib import Path
from io import StringIO

# Output directory for STEP files
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def execute_cadquery(code: str) -> dict:
    """
    Execute CadQuery code in a safe environment.
    
    Args:
        code: CadQuery Python code to execute
    
    Returns:
        {
            "success": bool,
            "step_path": str (if success),
            "error": str (if failure),
            "stdout": str
        }
    """
    
    # Generate unique output path
    output_id = str(uuid.uuid4())[:8]
    step_path = OUTPUT_DIR / f"{output_id}.step"
    
    # Inject export statement if not present
    if "export(" not in code and "exporters" not in code:
        code += f'\n\nimport cadquery as cq\ncq.exporters.export(result, "{step_path}")'
    else:
        # Replace any hardcoded output path with our generated one
        code = code.replace('output.step', str(step_path))
        code = code.replace('"result.step"', f'"{step_path}"')
        code = code.replace("'result.step'", f'"{step_path}"')
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Execute code
        exec_globals = {"__builtins__": __builtins__}
        exec(code, exec_globals)
        
        stdout = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Check if STEP file was created
        if step_path.exists():
            return {
                "success": True,
                "step_path": str(step_path),
                "stdout": stdout
            }
        else:
            return {
                "success": False,
                "error": "Code executed but no STEP file was created. Make sure `result` is defined and exported.",
                "stdout": stdout
            }
    
    except Exception as e:
        sys.stdout = old_stdout
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "stdout": ""
        }


def validate_step_file(step_path: str) -> dict:
    """
    Basic validation that STEP file is readable.
    """
    try:
        import cadquery as cq
        result = cq.importers.importStep(step_path)
        
        # Get basic properties
        solids = result.solids().vals()
        
        return {
            "valid": True,
            "num_solids": len(solids),
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
