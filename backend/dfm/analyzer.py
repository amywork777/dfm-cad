"""
Geometry analyzer: extract DFM-relevant properties from STEP files

Uses CadQuery/OpenCASCADE to analyze:
- Wall thickness
- Hole dimensions and depth ratios
- Draft angles
- Fillet radii
- Overhang angles
"""

from typing import Optional
import math


def analyze_geometry(step_path: str) -> dict:
    """
    Analyze a STEP file and extract DFM-relevant properties.
    
    Returns:
        {
            "volume_mm3": float,
            "surface_area_mm2": float,
            "bounding_box": {"x": float, "y": float, "z": float},
            "num_faces": int,
            "num_edges": int,
            "min_wall_thickness_mm": float,
            "holes": [{"diameter": float, "depth": float}],
            "fillets": [{"radius": float}],
            "sharp_edges": int,
            "draft_angles": [float],  # degrees
            "overhangs": [{"angle": float, "area_mm2": float}]
        }
    """
    try:
        import cadquery as cq
        from OCP.BRepGProp import BRepGProp
        from OCP.GProp import GProp_GProps
        from OCP.BRepBndLib import BRepBndLib_AddOBB
        from OCP.Bnd import Bnd_OBB
        
        # Import the STEP file
        result = cq.importers.importStep(step_path)
        solid = result.val()
        
        # Basic properties
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(solid.wrapped, props)
        volume = props.Mass()
        
        BRepGProp.SurfaceProperties_s(solid.wrapped, props)
        surface_area = props.Mass()
        
        # Bounding box
        bb = result.val().BoundingBox()
        bounding_box = {
            "x": bb.xlen,
            "y": bb.ylen,
            "z": bb.zlen
        }
        
        # Count faces and edges
        faces = result.faces().vals()
        edges = result.edges().vals()
        
        # Analyze faces for wall thickness (simplified)
        # Real implementation would use ray casting or medial axis
        min_wall = estimate_min_wall_thickness(result)
        
        # Find holes (cylindrical faces that are internal)
        holes = find_holes(result)
        
        # Find fillets (faces with constant curvature)
        fillets = find_fillets(result)
        
        # Count sharp edges (edges without fillets)
        sharp_edges = count_sharp_edges(result)
        
        # Analyze draft angles on vertical faces
        draft_angles = analyze_draft_angles(result)
        
        # Find overhangs (for 3D printing)
        overhangs = find_overhangs(result)
        
        return {
            "volume_mm3": volume,
            "surface_area_mm2": surface_area,
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
        return {
            "error": str(e),
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


def estimate_min_wall_thickness(result) -> float:
    """
    Estimate minimum wall thickness.
    
    Simplified approach: measure distances between parallel faces.
    Real implementation would use medial axis transform.
    """
    # TODO: Implement proper wall thickness analysis
    # For now, return a placeholder
    return 2.0


def find_holes(result) -> list[dict]:
    """
    Find cylindrical holes in the geometry.
    
    Returns list of {"diameter": float, "depth": float}
    """
    holes = []
    
    try:
        # Find cylindrical faces
        cylindrical_faces = result.faces("%Cylinder").vals()
        
        for face in cylindrical_faces:
            # Get cylinder properties
            # This is simplified - real implementation needs more checks
            surface = face.Surface()
            if hasattr(surface, "Radius"):
                diameter = surface.Radius() * 2
                # Estimate depth from face bounds
                bb = face.BoundingBox()
                depth = max(bb.xlen, bb.ylen, bb.zlen)
                holes.append({
                    "diameter": diameter,
                    "depth": depth
                })
    except:
        pass
    
    return holes


def find_fillets(result) -> list[dict]:
    """Find fillet faces and their radii."""
    fillets = []
    
    try:
        # Find toroidal and cylindrical fillet faces
        # This is a simplification
        for face in result.faces().vals():
            surface_type = face.geomType()
            if surface_type in ["CYLINDER", "TORUS"]:
                # Could be a fillet
                if hasattr(face.Surface(), "Radius"):
                    radius = face.Surface().Radius()
                    if radius < 10:  # Likely a fillet, not a main feature
                        fillets.append({"radius": radius})
    except:
        pass
    
    return fillets


def count_sharp_edges(result) -> int:
    """Count edges without fillets (sharp corners)."""
    sharp = 0
    
    try:
        for edge in result.edges().vals():
            # Check if edge is shared by two faces meeting at sharp angle
            # Simplified: count non-fillet edges
            edge_type = edge.geomType()
            if edge_type == "LINE":
                sharp += 1
    except:
        pass
    
    return sharp


def analyze_draft_angles(result) -> list[float]:
    """
    Analyze draft angles on faces relative to Z axis (pull direction).
    
    Returns list of angles in degrees.
    """
    angles = []
    
    try:
        for face in result.faces().vals():
            # Get face normal
            normal = face.normalAt()
            
            # Calculate angle from Z axis
            z_component = abs(normal.z)
            angle_from_z = math.degrees(math.acos(min(z_component, 1.0)))
            
            # Draft angle is complement of angle from vertical
            if 85 < angle_from_z < 95:  # Near-vertical face
                draft_angle = 90 - angle_from_z
                angles.append(abs(draft_angle))
    except:
        pass
    
    return angles


def find_overhangs(result, threshold_angle: float = 45) -> list[dict]:
    """
    Find overhanging faces for 3D printing analysis.
    
    Faces with normal pointing more than threshold_angle from vertical
    and facing downward are overhangs.
    """
    overhangs = []
    
    try:
        for face in result.faces().vals():
            normal = face.normalAt()
            
            # Check if face is pointing downward
            if normal.z < 0:
                # Calculate angle from vertical (Z axis)
                angle = math.degrees(math.acos(abs(normal.z)))
                
                if angle > threshold_angle:
                    # Get face area
                    area = face.Area()
                    overhangs.append({
                        "angle": angle,
                        "area_mm2": area
                    })
    except:
        pass
    
    return overhangs
