# DFM-CAD

An autonomous mechanical engineering agent that generates manufacturable CAD from plain English. Uses CadQuery for STEP output, validates against DFM rules, and learns from every run.

Built on the autoresearch loop pattern - every failure makes the system smarter.

## Architecture

```
User: "make a bracket with 4 mounting holes"
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  pipeline.py (orchestrator)                                   │
│                                                               │
│  1. Load spec (constraints: material, process, tolerances)   │
│  2. Load relevant skills (cadquery patterns, DFM rules)      │
│  3. For each task in spec:                                   │
│     → Claude generates CadQuery code                         │
│     → Execute code → STEP file                               │
│     → DFM layer validates geometry                           │
│     → Pass? Continue. Fail? Learn & retry.                   │
│                                                               │
│  4. /reflect after every run                                 │
│     → Classify learnings (universal vs part-specific)        │
│     → Commit improvements to skill files                     │
│     → Skills get better over time                            │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
   Output: STEP file + DFM report + learnings
```

## Core Concepts

### Specs (`specs/*.json`)
Define what you're building: geometry intent, constraints, manufacturing process.

```json
{
  "name": "mounting-bracket",
  "description": "L-bracket with 4 holes for M5 bolts",
  "constraints": {
    "material": "aluminum_6061",
    "process": "cnc_milling",
    "max_mass_kg": 0.5,
    "min_wall_thickness_mm": 2.0
  },
  "tasks": [
    {"id": "base", "description": "Create L-shaped base profile"},
    {"id": "holes", "description": "Add 4 mounting holes for M5"},
    {"id": "fillets", "description": "Add fillets to inside corner"}
  ]
}
```

### Skills (`skills/*.md`)
Accumulated knowledge about how to do things reliably. Two sections:

1. **Engineering Domain** - physics, DFM rules, material properties (CAD-agnostic)
2. **CadQuery Implementation** - working code patterns, parameter values

Skills improve after every run via `/reflect`.

### DFM Rules (`dfm/rules/`)
Manufacturing constraint checkers:

| Rule | Process | Check |
|------|---------|-------|
| wall_thickness | injection_molding | min 1.5mm |
| draft_angle | injection_molding | min 1° |
| hole_depth_ratio | cnc_drilling | max 10:1 |
| overhang_angle | fdm_printing | max 45° |
| internal_radius | cnc_milling | min = tool radius |

### Learning Loop

After every run, `/reflect` fires automatically:

1. Harvests learnings from task logs
2. Classifies each by scope:
   - `universal` → goes to skill file
   - `process_specific` → goes to process skill
   - `part_specific` → stays in spec notes only
3. Commits improvements to skills
4. Next run benefits from new knowledge

## Directory Structure

```
dfm-cad/
├── pipeline.py              # Main orchestrator
├── reflect.py               # Post-run learning extractor
│
├── agent/
│   ├── codegen.py           # Claude → CadQuery code
│   ├── executor.py          # Run CadQuery, get STEP
│   └── logger.py            # Task logging
│
├── dfm/
│   ├── analyzer.py          # Geometry analysis (faces, edges, thickness)
│   ├── validator.py         # Run rules against geometry
│   └── rules/
│       ├── cnc.py
│       ├── injection_molding.py
│       ├── fdm_printing.py
│       └── sheet_metal.py
│
├── skills/
│   ├── SKILLS.md            # Index of all skills
│   ├── cadquery/
│   │   └── skill.md         # CadQuery patterns, working code
│   ├── dfm_cnc/
│   │   └── skill.md         # CNC-specific DFM knowledge
│   └── dfm_injection/
│       └── skill.md         # Injection molding DFM knowledge
│
├── specs/                   # Your design targets
│   └── mounting-bracket.json
│
├── outputs/                 # Generated STEP files
│
└── logs/
    └── task_log.jsonl       # Run history for learning
```

## Quick Start

```bash
# Install
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY

# Create a spec
python new_spec.py

# Run the loop
python pipeline.py specs/your-part.json

# Skills improve automatically after each run
```

## Stack

- **CAD Engine**: CadQuery (outputs real STEP/B-rep)
- **Geometry Kernel**: OpenCASCADE (via CadQuery)
- **Code Generation**: Claude API
- **DFM Analysis**: Custom rules on OCCT geometry

## Why This Architecture?

1. **STEP output** - real B-rep geometry, not mesh. Can analyze faces, edges, dimensions.
2. **DFM baked in** - catches manufacturing issues during generation, not after.
3. **Self-improving** - every run makes the system smarter via skill accumulation.
4. **CAD-agnostic knowledge** - DFM rules separated from CadQuery implementation.
5. **Open source** - no API costs for CAD (only Claude for code generation).
