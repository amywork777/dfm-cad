"""
Code generation: Claude → CadQuery python code
Supports text-only, image-only, and text+image input.
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
- The final result MUST be assigned to a variable called `result`

OUTPUT FORMAT:
Return ONLY valid Python code. No markdown, no explanations, no code fences.
The code must be self-contained and executable.
"""


def generate_cadquery_code(
    task_description: str,
    constraints: dict,
    skills: str = "",
    previous_code: str = None,
    previous_error: str = None
) -> str:
    """
    Generate CadQuery code from text description.
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
    return _clean_code(code)


def generate_cadquery_code_with_image(
    prompt: str,
    image_data: str,
    image_type: str,
    constraints: dict,
    previous_code: str = None,
    previous_error: str = None
) -> str:
    """
    Generate CadQuery code from image (with optional text).
    
    Args:
        prompt: Text description (can be empty for image-only)
        image_data: Base64 encoded image
        image_type: MIME type (e.g., "image/png")
        constraints: Material, process, etc.
    """
    
    # Build message content with image
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": image_type,
                "data": image_data
            }
        }
    ]
    
    # Add text prompt
    text_parts = []
    
    if prompt:
        text_parts.append(f"Generate CadQuery code based on this image. User description: {prompt}")
    else:
        text_parts.append("Generate CadQuery code to recreate the part shown in this image.")
    
    text_parts.append(f"\nConstraints: {constraints}")
    
    if previous_code and previous_error:
        text_parts.append(f"\n\nPREVIOUS ATTEMPT FAILED:")
        text_parts.append(f"Code:\n```python\n{previous_code}\n```")
        text_parts.append(f"Error: {previous_error}")
        text_parts.append("\nFix the issue and generate corrected code.")
    
    content.append({
        "type": "text",
        "text": "\n".join(text_parts)
    })
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}]
    )
    
    code = response.content[0].text
    return _clean_code(code)


def _clean_code(code: str) -> str:
    """Strip markdown code blocks if present."""
    code = code.strip()
    
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    
    if code.endswith("```"):
        code = code[:-3]
    
    return code.strip()
