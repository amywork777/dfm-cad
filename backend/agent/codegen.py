"""
Code generation: Claude → CadQuery python code
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert mechanical engineer and CadQuery programmer.

You generate CadQuery Python code that:
1. Creates precise, manufacturable geometry
2. Follows DFM (Design for Manufacturing) best practices
3. Outputs valid STEP files

IMPORTANT RULES:
- Always use `cq.Workplane` as the entry point
- Export to STEP using `cq.exporters.export(result, "output.step")`
- Use millimeters as the default unit
- Add fillets/chamfers where appropriate for manufacturing
- Consider draft angles for injection molding
- Ensure wall thickness meets minimums for the process

OUTPUT FORMAT:
Return ONLY valid Python code. No markdown, no explanations.
The code must be self-contained and executable.
The final result must be assigned to a variable called `result`.
"""


def generate_cadquery_code(
    task_description: str,
    constraints: dict,
    skills: str = "",
    previous_code: str = None,
    previous_error: str = None
) -> str:
    """
    Generate CadQuery code using Claude.
    
    Args:
        task_description: What to build
        constraints: Material, process, dimensions, etc.
        skills: Accumulated knowledge from skill files
        previous_code: If retrying, the code that failed
        previous_error: If retrying, what went wrong
    
    Returns:
        CadQuery Python code as a string
    """
    
    prompt_parts = [
        f"Generate CadQuery code for: {task_description}",
        f"\nConstraints: {constraints}",
    ]
    
    if skills:
        prompt_parts.append(f"\n\nRelevant knowledge:\n{skills}")
    
    if previous_code and previous_error:
        prompt_parts.append(f"\n\nPREVIOUS ATTEMPT FAILED:")
        prompt_parts.append(f"Code:\n```python\n{previous_code}\n```")
        prompt_parts.append(f"Error: {previous_error}")
        prompt_parts.append("\nFix the issue and generate corrected code.")
    
    prompt = "\n".join(prompt_parts)
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    
    code = response.content[0].text
    
    # Strip markdown code blocks if present
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    
    return code.strip()
