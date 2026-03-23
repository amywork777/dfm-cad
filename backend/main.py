"""
DFM-CAD Pipeline

Orchestrates: prompt → CadQuery code → STEP → DFM validation → learning
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

from agent.codegen import generate_cadquery_code
from agent.executor import execute_cadquery
from agent.logger import log_task
from dfm.validator import validate_geometry
from reflect import reflect_on_run

load_dotenv()


def load_spec(spec_path: str) -> dict:
    """Load a spec file."""
    with open(spec_path) as f:
        return json.load(f)


def load_skills(skill_names: list[str]) -> str:
    """Load and concatenate relevant skills."""
    skills_content = []
    for name in skill_names:
        skill_path = Path(f"skills/{name}/skill.md")
        if skill_path.exists():
            skills_content.append(skill_path.read_text())
    return "\n\n---\n\n".join(skills_content)


def run_pipeline(spec_path: str, max_retries: int = 3):
    """
    Main pipeline loop.
    
    1. Load spec and skills
    2. For each task: generate code, execute, validate
    3. Learn from failures, retry if needed
    4. Reflect at end to improve skills
    """
    spec = load_spec(spec_path)
    print(f"\n🚀 Running pipeline for: {spec['name']}")
    print(f"   Process: {spec['constraints'].get('process', 'unspecified')}")
    
    # Load relevant skills based on process type
    process = spec["constraints"].get("process", "general")
    skills = load_skills(["cadquery", f"dfm_{process}"])
    
    run_log = []
    
    for task in spec["tasks"]:
        if task.get("status") == "passed":
            print(f"   ✓ Skipping {task['id']} (already passed)")
            continue
            
        print(f"\n   📦 Task: {task['id']}")
        print(f"      {task['description']}")
        
        for attempt in range(max_retries):
            # Generate CadQuery code
            code = generate_cadquery_code(
                task_description=task["description"],
                constraints=spec["constraints"],
                skills=skills,
                previous_code=task.get("previous_code"),
                previous_error=task.get("previous_error")
            )
            
            # Execute code
            result = execute_cadquery(code)
            
            if result["success"]:
                step_path = result["step_path"]
                
                # Validate against DFM rules
                dfm_result = validate_geometry(
                    step_path=step_path,
                    process=spec["constraints"].get("process"),
                    constraints=spec["constraints"]
                )
                
                if dfm_result["passed"]:
                    print(f"      ✅ Passed (attempt {attempt + 1})")
                    task["status"] = "passed"
                    task["code"] = code
                    log_task(task["id"], "passed", code=code)
                    break
                else:
                    print(f"      ⚠️  DFM warnings: {dfm_result['warnings']}")
                    task["previous_error"] = f"DFM: {dfm_result['warnings']}"
                    log_task(task["id"], "dfm_fail", warnings=dfm_result["warnings"])
            else:
                print(f"      ❌ Code error: {result['error'][:100]}")
                task["previous_code"] = code
                task["previous_error"] = result["error"]
                log_task(task["id"], "code_fail", error=result["error"])
        
        else:
            print(f"      💀 Failed after {max_retries} attempts")
            run_log.append({"task": task["id"], "status": "failed"})
            break
        
        run_log.append({"task": task["id"], "status": "passed"})
    
    # Save updated spec
    with open(spec_path, "w") as f:
        json.dump(spec, f, indent=2)
    
    # Reflect and improve skills
    print("\n🔄 Reflecting on run...")
    reflect_on_run(run_log)
    
    print("\n✨ Pipeline complete")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py specs/your-part.json")
        sys.exit(1)
    run_pipeline(sys.argv[1])
