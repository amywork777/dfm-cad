# CadQuery Skill

## Engineering Domain

CadQuery is a Python library for building parametric 3D CAD models using OpenCASCADE.

### Key Concepts
- Workplane-based modeling: start with a 2D plane, sketch, then extrude/revolve
- Selectors: use strings like ">Z" (top face), "<X" (left face) to select features
- Chaining: operations chain together fluently

### Best Practices
- Always define dimensions as variables at the top for parametric control
- Use `result` as the final variable name for the model
- Export with `cq.exporters.export(result, "output.step")`

## CadQuery Implementation

### Common Patterns

**Basic box with hole:**
```python
import cadquery as cq

width = 50
height = 30
thickness = 10
hole_diameter = 8

result = (
    cq.Workplane("XY")
    .box(width, height, thickness)
    .faces(">Z")
    .workplane()
    .hole(hole_diameter)
)

cq.exporters.export(result, "output.step")
```

**L-bracket:**
```python
import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(50, 10, 30)
    .faces("<Z")
    .workplane()
    .box(50, 30, 10, centered=(True, False, False))
)
```

**Fillet edges:**
```python
result = result.edges("|Z").fillet(2)  # Vertical edges
result = result.edges(">Z").fillet(1)  # Top edges
```

**Chamfer:**
```python
result = result.edges().chamfer(0.5)
```

**Multiple holes in pattern:**
```python
result = (
    cq.Workplane("XY")
    .box(100, 50, 10)
    .faces(">Z")
    .workplane()
    .rect(80, 30, forConstruction=True)
    .vertices()
    .hole(5)
)
```

### Common Errors

- `ValueError: No solid to modify`: ensure previous operations created a solid
- Selector errors: check face/edge selector syntax (">Z", "<X", "|Z", etc.)

## Learnings

<!-- Learnings will be appended here by reflect.py -->
