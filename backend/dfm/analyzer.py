"""
Geometry analyzer: extract DFM-relevant properties from STEP files

Uses CadQuery/OpenCASCADE to analyze:
- Wall thickness
- Hole dimensions and depth ratios
- Draft angles
- Fillet radii
- Overhang angles
"""

import math


def analyze_geometry(step_path: str) -> dict:
    """
    Analyze a STEP file and extract DFM-relevant properties.
    """
    try:
        import cadquery as cq
        
        # Import the STEP file
        wp = cq.importers.importStep(step_path)
        solid = wp.solids().vals()[0]
        
        # Bounding box
        bb = solid.BoundingBox()
        bounding_box = {
            "x": bb.xlen,
            "y": bb.ylen,
            "z": bb.zlen
        }
        
        # Volume and surface area using CadQuery methods
        volume = solid.Volume()
        
        # Count faces and edges
        faces = wp.faces().vals()
        edges = wp.edges().vals()
        
        # Find holes (cylindrical faces)
        holes = find_holes(wp)
        
        # Find fillets
        fillets = find_fillets(wp)
        
        # Count sharp edges
        sharp_edges = count_sharp_edges(wp)
        
        # Analyze draft angles
        draft_angles = analyze_draft_angles(wp)
        
        # Find overhangs
        overhangs = find_overhangs(wp)
        
        # Estimate wall thickness (simplified)
        min_wall = estimate_min_wall_thickness(wp, bounding_box)
        
        return {
            "volume_mm3": volume,
            "surface_area_mm2": 0,  # TODO: calculate properly
            "bounding_box": bounding_box,
            "num_faces": len(faces),
            "num_edges": len(edges),
            "min_wall_thickness_mm": min_wall,
            "holes": holes,
            "fillets": fillets,
            "sharp_edges": sharp_edges,
            "draft_angles": draft_angles,
            "overhangs": overhangs
        }
        
    except Exception as e:
        import traceback
        return {
            "error": f"{str(e)}\n{traceback.format_exc()}",
            "volume_mm3": 0,
            "surface_area_mm2": 0,
            "bounding_box": {"x": 0, "y": 0, "z": 0},
            "num_faces": 0,
            "num_edges": 0,
            "min_wall_thickness_mm": 0,
            "holes": [],
            "fillets": [],
            "sharp_edges": 0,
            "draft_angles": [],
            "overhangs": []
        }


def estimate_min_wall_thickness(wp, bounding_box) -> float:
    """
    Estimate minimum wall thickness.
    Simplified: uses smallest bounding box dimension as proxy.
    Real implementation would use ray casting.
    """
    return min(bounding_box["x"], bounding_box["y"], bounding_box["z"])


def find_holes(wp) -> list[dict]:
    """Find cylindrical holes in the geometry."""
    holes = []
    
    try:
        for face in wp.faces().vals():
            geom_type = face.geomType()
            if geom_type == "CYLINDER":
                # Get cylinder properties
                bb = face.BoundingBox()
                # Estimate diameter from face dimensions
                dims = sorted([bb.xlen, bb.ylen, bb.zlen])
                diameter = dims[0]  # Smallest dimension is likely the diameter
                depth = dims[2]     # Largest is likely the depth
                
                if diameter < depth:  # Likely a hole, not a boss
                    holes.append({
                        "diameter": diameter,
                        "depth": depth
                    })
    except:
        pass
    
    return holes


def find_fillets(wp) -> list[dict]:
    """Find fillet faces and their radii."""
    fillets = []
    
    try:
        for face in wp.faces().vals():
            geom_type = face.geomType()
            if geom_type in ["CYLINDER", "TORUS"]:
                bb = face.BoundingBox()
                # Small cylindrical/toroidal faces are likely fillets
                min_dim = min(bb.xlen, bb.ylen, bb.zlen)
                if min_dim < 5:  # Likely a fillet
                    fillets.append({"radius": min_dim / 2})
    except:
        pass
    
    return fillets


def count_sharp_edges(wp) -> int:
    """Count edges that are likely sharp (no fillet)."""
    sharp = 0
    
    try:
        for edge in wp.edges().vals():
            if edge.geomType() == "LINE":
                sharp += 1
    except:
        pass
    
    return sharp


def analyze_draft_angles(wp) -> list[float]:
    """Analyze draft angles on faces relative to Z axis."""
    angles = []
    
    try:
        for face in wp.faces().vals():
            if face.geomType() == "PLANE":
                # Get face normal at center
                center = face.Center()
                normal = face.normalAt(center)
                
                # Calculate angle from Z axis
                z_component = abs(normal.z)
                if z_component < 0.99:  # Not horizontal
                    angle_from_z = math.degrees(math.acos(min(z_component, 1.0)))
                    # Near-vertical faces
                    if 80 < angle_from_z < 100:
                        draft_angle = abs(90 - angle_from_z)
                        angles.append(draft_angle)
    except:
        pass
    
    return angles


def find_overhangs(wp, threshold_angle: float = 45) -> list[dict]:
    """Find overhanging faces for 3D printing analysis."""
    overhangs = []
    
    try:
        for face in wp.faces().vals():
            center = face.Center()
            normal = face.normalAt(center)
            
            # Check if face is pointing downward
            if normal.z < -0.1:
                angle = math.degrees(math.acos(abs(normal.z)))
                if angle > threshold_angle:
                    area = face.Area()
                    overhangs.append({
                        "angle": angle,
                        "area_mm2": area
                    })
    except:
        pass
    
    return overhangs
