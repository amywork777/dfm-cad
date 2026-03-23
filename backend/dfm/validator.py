"""
DFM Validator: check geometry against manufacturing rules
"""

from typing import Optional
from dfm.analyzer import analyze_geometry


# Default DFM rules by process
DFM_RULES = {
    "cnc_milling": {
        "min_wall_thickness_mm": 1.0,
        "min_internal_radius_mm": 1.5,  # Based on smallest end mill
        "max_hole_depth_ratio": 10,      # depth / diameter
        "min_fillet_radius_mm": 0.5,
    },
    "injection_molding": {
        "min_wall_thickness_mm": 1.5,
        "max_wall_thickness_mm": 4.0,    # Avoid sink marks
        "min_draft_angle_deg": 1.0,
        "min_fillet_radius_mm": 0.5,
    },
    "fdm_printing": {
        "min_wall_thickness_mm": 0.8,    # 2x nozzle diameter
        "max_overhang_angle_deg": 45,
        "min_hole_diameter_mm": 2.0,
    },
    "sheet_metal": {
        "min_wall_thickness_mm": 0.5,
        "min_bend_radius_mm": 1.0,       # Based on material thickness
        "min_hole_diameter_mm": 1.0,
        "min_edge_to_hole_mm": 2.0,
    },
    "general": {
        "min_wall_thickness_mm": 1.0,
    }
}


def validate_geometry(
    step_path: str,
    process: Optional[str] = None,
    constraints: Optional[dict] = None
) -> dict:
    """
    Validate geometry against DFM rules.
    
    Args:
        step_path: Path to STEP file
        process: Manufacturing process (cnc_milling, injection_molding, etc.)
        constraints: Additional constraints from spec
    
    Returns:
        {
            "passed": bool,
            "warnings": [{"rule": str, "message": str, "severity": str}],
            "geometry": dict (analysis results)
        }
    """
    
    # Analyze geometry
    geometry = analyze_geometry(step_path)
    
    if "error" in geometry:
        return {
            "passed": False,
            "warnings": [{"rule": "analysis", "message": geometry["error"], "severity": "error"}],
            "geometry": geometry
        }
    
    # Get rules for this process
    process = process or "general"
    rules = DFM_RULES.get(process, DFM_RULES["general"])
    
    # Override with spec constraints
    if constraints:
        for key, value in constraints.items():
            if key.startswith("min_") or key.startswith("max_"):
                rules[key] = value
    
    warnings = []
    
    # Check wall thickness
    if "min_wall_thickness_mm" in rules:
        if geometry["min_wall_thickness_mm"] < rules["min_wall_thickness_mm"]:
            warnings.append({
                "rule": "wall_thickness",
                "message": f"Wall thickness {geometry['min_wall_thickness_mm']:.2f}mm is below minimum {rules['min_wall_thickness_mm']}mm for {process}",
                "severity": "error"
            })
    
    # Check hole depth ratios
    if "max_hole_depth_ratio" in rules:
        for hole in geometry["holes"]:
            ratio = hole["depth"] / hole["diameter"] if hole["diameter"] > 0 else 0
            if ratio > rules["max_hole_depth_ratio"]:
                warnings.append({
                    "rule": "hole_depth_ratio",
                    "message": f"Hole depth ratio {ratio:.1f}:1 exceeds maximum {rules['max_hole_depth_ratio']}:1",
                    "severity": "warning"
                })
    
    # Check draft angles (injection molding)
    if "min_draft_angle_deg" in rules:
        for angle in geometry["draft_angles"]:
            if angle < rules["min_draft_angle_deg"]:
                warnings.append({
                    "rule": "draft_angle",
                    "message": f"Draft angle {angle:.1f}° is below minimum {rules['min_draft_angle_deg']}° for mold release",
                    "severity": "error"
                })
    
    # Check overhangs (3D printing)
    if "max_overhang_angle_deg" in rules:
        for overhang in geometry["overhangs"]:
            if overhang["angle"] > rules["max_overhang_angle_deg"]:
                warnings.append({
                    "rule": "overhang",
                    "message": f"Overhang at {overhang['angle']:.0f}° exceeds {rules['max_overhang_angle_deg']}° (needs support)",
                    "severity": "warning"
                })
    
    # Check fillet radii
    if "min_fillet_radius_mm" in rules:
        for fillet in geometry["fillets"]:
            if fillet["radius"] < rules["min_fillet_radius_mm"]:
                warnings.append({
                    "rule": "fillet_radius",
                    "message": f"Fillet radius {fillet['radius']:.2f}mm is below minimum {rules['min_fillet_radius_mm']}mm",
                    "severity": "warning"
                })
    
    # Check sharp edges
    if geometry["sharp_edges"] > 0 and process in ["injection_molding", "cnc_milling"]:
        warnings.append({
            "rule": "sharp_edges",
            "message": f"Found {geometry['sharp_edges']} sharp edges. Consider adding fillets for stress relief.",
            "severity": "info"
        })
    
    # Determine pass/fail
    # Fail on errors, pass with warnings
    has_errors = any(w["severity"] == "error" for w in warnings)
    
    return {
        "passed": not has_errors,
        "warnings": warnings,
        "geometry": geometry
    }


def get_rules_for_process(process: str) -> dict:
    """Get DFM rules for a specific process."""
    return DFM_RULES.get(process, DFM_RULES["general"])
