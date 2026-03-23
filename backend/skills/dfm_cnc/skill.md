# DFM: CNC Milling

## Engineering Domain

### Process Overview
CNC milling removes material using rotating cutting tools. Parts are typically held in a vise or fixture.

### Key Constraints

**Wall Thickness**
- Minimum: 1.0mm (aluminum), 0.5mm (steel)
- Thin walls vibrate during cutting, causing chatter and poor surface finish

**Internal Corners**
- Cannot be perfectly sharp - limited by tool radius
- Minimum internal radius = tool radius (typically 1.5mm for small parts)
- Design internal corners with fillets matching available tool sizes

**Hole Depth**
- Standard drills: max depth = 10x diameter
- Deep holes require peck drilling or gun drilling (expensive)

**Undercuts**
- Standard 3-axis cannot reach undercuts
- Require 5-axis or secondary operations
- Avoid if possible

**Tool Access**
- Tool must be able to reach all features
- Consider fixturing and workholding

### Material Considerations

| Material | Min Wall | Machinability |
|----------|----------|---------------|
| Aluminum 6061 | 1.0mm | Excellent |
| Steel 1018 | 0.5mm | Good |
| Stainless 304 | 1.0mm | Poor (work hardens) |
| Brass | 0.8mm | Excellent |
| Plastic (Delrin) | 1.5mm | Good |

## CadQuery Implementation

**Adding fillets for CNC:**
```python
# Internal corners need radius >= tool radius
result = result.edges("|Z").fillet(1.5)  # 1.5mm matches 3mm end mill
```

**Designing for workholding:**
```python
# Leave flat surfaces for vise grip
# Minimum 10mm grip area
```

## Learnings

<!-- Learnings will be appended here -->
