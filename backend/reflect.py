"""
Reflect: post-run learning extraction

After every run, analyzes what happened and improves skill files.
"""

import json
from pathlib import Path
from datetime import datetime
from agent.logger import read_recent_logs, get_failure_patterns


def reflect_on_run(run_log: list[dict]):
    """
    Analyze a run and extract learnings.
    
    1. Classify each learning by scope
    2. Route to appropriate skill file or spec notes
    3. Commit improvements
    """
    
    logs = read_recent_logs(50)
    patterns = get_failure_patterns()
    
    learnings = []
    
    # Analyze code failures
    for error_type, count in patterns["code_errors"].items():
        if count >= 2:  # Recurring error
            learnings.append({
                "scope": "universal",
                "type": "code_pattern",
                "content": f"Recurring error: {error_type} ({count} occurrences). Add handling to codegen prompt.",
                "skill": "cadquery"
            })
    
    # Analyze DFM failures
    for rule, count in patterns["dfm_warnings"].items():
        if count >= 2:
            learnings.append({
                "scope": "process_specific",
                "type": "dfm_pattern",
                "content": f"Recurring DFM issue: {rule} ({count} occurrences). Strengthen rule in codegen prompt.",
                "skill": f"dfm_{rule.split('_')[0]}" if '_' in rule else "dfm_general"
            })
    
    # Write learnings to skill files
    for learning in learnings:
        if learning["scope"] in ["universal", "process_specific"]:
            append_to_skill(learning["skill"], learning["content"])
    
    # Log reflection
    reflection_log = {
        "timestamp": datetime.now().isoformat(),
        "learnings": learnings,
        "patterns": patterns
    }
    
    log_path = Path("logs/reflections.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(reflection_log) + "\n")
    
    print(f"   📝 Extracted {len(learnings)} learnings")
    
    return learnings


def append_to_skill(skill_name: str, content: str):
    """Append a learning to a skill file."""
    skill_path = Path(f"skills/{skill_name}/skill.md")
    
    if not skill_path.exists():
        # Create new skill file
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(f"# {skill_name}\n\n## Learnings\n\n")
    
    # Append learning with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    with open(skill_path, "a") as f:
        f.write(f"\n- [{timestamp}] {content}\n")


def classify_learning(learning: dict) -> str:
    """
    Classify a learning by scope:
    - universal: applies to all parts/processes
    - process_specific: applies to a specific manufacturing process
    - part_specific: only applies to this specific part
    """
    content = learning.get("content", "").lower()
    
    # Check for process-specific keywords
    processes = ["cnc", "injection", "molding", "fdm", "printing", "sheet metal"]
    for process in processes:
        if process in content:
            return "process_specific"
    
    # Check for part-specific indicators
    if any(word in content for word in ["this part", "specific dimension", "custom"]):
        return "part_specific"
    
    return "universal"
