"""
Task logger: append-only log for learning
"""

import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("logs/task_log.jsonl")
LOG_PATH.parent.mkdir(exist_ok=True)


def log_task(task_id: str, status: str, **kwargs):
    """
    Log a task result for later learning.
    
    Args:
        task_id: Task identifier
        status: passed, code_fail, dfm_fail, etc.
        **kwargs: Additional data (code, error, warnings, etc.)
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "status": status,
        **kwargs
    }
    
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_recent_logs(n: int = 50) -> list[dict]:
    """Read the most recent n log entries."""
    if not LOG_PATH.exists():
        return []
    
    with open(LOG_PATH) as f:
        lines = f.readlines()
    
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    
    return entries


def get_failure_patterns() -> dict:
    """
    Analyze logs for common failure patterns.
    Used by reflect.py to identify skill gaps.
    """
    logs = read_recent_logs(200)
    
    patterns = {
        "code_errors": {},
        "dfm_warnings": {},
        "retry_counts": {}
    }
    
    for entry in logs:
        if entry["status"] == "code_fail":
            error_type = entry.get("error", "").split(":")[0]
            patterns["code_errors"][error_type] = patterns["code_errors"].get(error_type, 0) + 1
        
        elif entry["status"] == "dfm_fail":
            for warning in entry.get("warnings", []):
                rule = warning.get("rule", "unknown")
                patterns["dfm_warnings"][rule] = patterns["dfm_warnings"].get(rule, 0) + 1
    
    return patterns
