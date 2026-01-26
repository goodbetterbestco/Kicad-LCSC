# KiCad IC Footprint Creation Guide

A practical guide for creating accurate footprints from datasheet land patterns. Focuses on QFN and similar packages with complex pad geometries.

---

## Table of Contents

0. [Initial Footprint Generation (easyeda2kicad)](#0-initial-footprint-generation-easyeda2kicad)
1. [Coordinate System](#1-coordinate-system)
2. [Reading Land Pattern Drawings](#2-reading-land-pattern-drawings)
3. [Layer Definitions](#3-layer-definitions)
4. [Pad Types and Syntax](#4-pad-types-and-syntax)
5. [Calculating Pad Positions](#5-calculating-pad-positions)
6. [Complex Pad Shapes](#6-complex-pad-shapes)
7. [Silkscreen, Courtyard, and Fab Outline](#7-silkscreen-courtyard-and-fab-outline)
8. [File Format Rules](#8-file-format-rules)
9. [Verification Checklist](#9-verification-checklist)
10. [Worked Example: QFN-20 with E-Shaped Pads](#10-worked-example-qfn-20-with-e-shaped-pads)

---

## 0. Initial Footprint Generation (easyeda2kicad)

Generate baseline assets from LCSC/EasyEDA:

```bash
pip install easyeda2kicad --break-system-packages
easyeda2kicad --lcsc_id C5173872 --output ~/Documents/KiCad/9.0/3rdparty/LCSC
```

**What typically needs refinement:**
- Pad positions (often incorrect for complex packages)
- Pad shapes (custom polygons may be wrong or missing)
- Layer assignments and outlines
- Courtyard dimensions

---

## 1. Coordinate System

### KiCad Footprint Coordinates

| Axis | Direction |
|------|-----------|
| X | Positive = Right |
| Y | Positive = Down |
| Origin | Center of footprint |

### Converting from Datasheet to KiCad

Datasheets typically use quadrant-based dimensions with positive values measured from datum lines. The horizontal and vertical datum lines cross at the footprint origin.

**Quadrant mapping:**

```
          Datasheet                    KiCad
     Y+                              Y- (up)
      │                                │
  ────┼────  X+               X- ──────┼────── X+
      │                                │
                                     Y+ (down)
```

**Conversion rules:**
- Upper quadrants: Datasheet Y+ → KiCad Y-
- Lower quadrants: Datasheet Y+ → KiCad Y+
- Left quadrants: Datasheet X+ → KiCad X-
- Right quadrants: Datasheet X+ → KiCad X+

---

## 2. Reading Land Pattern Drawings

### Anatomy of a Land Pattern

Land patterns show **recommended PCB pad positions**, not the component's physical pin locations. Pads typically extend beyond the silicon outline to facilitate soldering.

### Key Dimensions to Extract

| Dimension | Description |
|-----------|-------------|
| Pad width/height | Size of each pad |
| Pad centers | X, Y position from datum |
| Silicon outline | Physical component boundary |
| Pad outer edges | Where pads align with silicon (for non-protruding pins) |

### Example Dimension Interpretation

For a pad dimensioned as:
- Horizontal: starts at 2.10, ends at 2.80 (from vertical datum)
- Vertical: starts at 0.25, ends at 0.50 (from horizontal datum)

Calculate:
- Width: 2.80 - 2.10 = 0.70mm
- Height: 0.50 - 0.25 = 0.25mm
- X center: (2.10 + 2.80) / 2 = 2.45mm (apply quadrant sign)
- Y center: (0.25 + 0.50) / 2 = 0.375mm (apply quadrant sign)

---

## 3. Layer Definitions

| Layer | Purpose | Contents |
|-------|---------|----------|
| F.Cu | Front copper | Pad copper for soldering |
| F.Paste | Solder paste | Stencil openings (usually same as pads) |
| F.Mask | Solder mask | Mask openings (usually same as pads) |
| F.SilkS | Silkscreen | Component outline, pin 1 marker |
| F.Fab | Fabrication | Physical component body outline |
| F.CrtYd | Courtyard | Placement clearance boundary |

### Layer Guidelines

**F.Fab (Component Outline):**
- Shows actual silicon/package dimensions
- Does NOT include pad extents
- Used for assembly documentation

**F.CrtYd (Courtyard):**
- Must encompass ALL pad extents
- Must encompass component body (F.Fab)
- Add 0.25mm minimum clearance on all sides
- Used by DRC for component spacing

**F.SilkS (Silkscreen):**
- Should not overlap pads
- Include pin 1 marker
- Outline near but not on pads

---

## 4. Pad Types and Syntax

### Simple Rectangular Pad

```
(pad "1" smd rect (at X Y) (size W H) (layers "F.Cu" "F.Paste" "F.Mask"))
```

| Parameter | Description |
|-----------|-------------|
| "1" | Pad number (must match symbol pin) |
| smd | Surface mount (vs thru_hole) |
| rect | Rectangular shape |
| (at X Y) | Center position in mm |
| (size W H) | Width and height in mm |

### Rotated Rectangular Pad

```
(pad "1" smd rect (at X Y 90) (size W H) (layers "F.Cu" "F.Paste" "F.Mask"))
```

The third value in `(at X Y 90)` is rotation in degrees.

### Custom Polygon Pad

For complex shapes (chamfered corners, E-shapes, L-shapes):

```
(pad "1" smd custom (at X Y)
    (size 0.1 0.1)
    (layers "F.Cu" "F.Paste" "F.Mask")
    (zone_connect 0)
    (options (clearance outline) (anchor rect))
    (primitives
        (gr_poly
            (pts
                (xy x1 y1)
                (xy x2 y2)
                (xy x3 y3)
                ...
            )
            (width 0) (fill yes)
        )
    )
)
```

**Critical:** Polygon coordinates are **relative to the pad center** specified in `(at X Y)`.

---

## 5. Calculating Pad Positions

### Standard Rectangular Pads

Given datasheet dimensions for a pad in the upper-left quadrant:
- X: 2.10 to 2.80 from vertical datum
- Y: 0.25 to 0.50 from horizontal datum

KiCad position:
- X center: -((2.10 + 2.80) / 2) = **-2.45**
- Y center: -((0.25 + 0.50) / 2) = **-0.375**
- Size: (0.70, 0.25)

### Pad Arrays at Regular Pitch

For N pads at pitch P, centered on an axis:

```python
def pad_positions(n, pitch):
    """Calculate centered positions for n pads at given pitch."""
    start = -((n - 1) * pitch) / 2
    return [start + i * pitch for i in range(n)]

# Example: 6 pads at 0.5mm pitch
# Positions: -1.25, -0.75, -0.25, +0.25, +0.75, +1.25
```

---

## 6. Complex Pad Shapes

### Chamfered Corner

For a pad with a 45° chamfer of size C on one corner:

```
Original rectangle: W × H centered at origin
Chamfer on top-right corner:

(gr_poly
    (pts
        (xy -W/2 -H/2)          ; top-left
        (xy W/2-C -H/2)         ; before chamfer
        (xy W/2 -H/2+C)         ; after chamfer
        (xy W/2 H/2)            ; bottom-right
        (xy -W/2 H/2)           ; bottom-left
    )
    (width 0) (fill yes)
)
```

### E-Shaped Pads (Power Module Thermal Pads)

E-shaped pads consist of a vertical bar with horizontal teeth. To assign separate pin numbers to each tooth region:

**Geometry breakdown:**
- Overall E: width W_total, height H_total
- Vertical bar: width W_bar
- Teeth: width W_tooth, height H_tooth
- Tooth Y centers: Y1, Y2, Y3

**Split into 3 pads (one per tooth):**

Each pad's center is at the tooth's Y position. Primitives define:
1. The tooth (full width)
2. The bar section for that pad's region

```
; Top tooth pad
(pad "4" smd custom (at X_center Y_tooth1)
    (size 0.1 0.1)
    (layers "F.Cu" "F.Paste" "F.Mask")
    (zone_connect 0)
    (options (clearance outline) (anchor rect))
    (primitives
        ; Tooth
        (gr_poly (pts
            (xy -W_tooth/2 -H_tooth/2)
            (xy W_bar_edge -H_tooth/2)
            (xy W_bar_edge H_tooth/2)
            (xy -W_tooth/2 H_tooth/2)
        ) (width 0) (fill yes))
        ; Bar section
        (gr_poly (pts
            (xy W_bar_edge -H_tooth/2)
            (xy W_bar_edge+W_bar -H_tooth/2)
            (xy W_bar_edge+W_bar H_tooth/2)
            (xy W_bar_edge H_tooth/2)
        ) (width 0) (fill yes))
    )
)
```

The middle tooth pad includes bar sections extending both up and down to connect the E-shape.

---

## 7. Silkscreen, Courtyard, and Fab Outline

### Determining Extents

Calculate the bounding box of all copper:

```python
x_min = min(pad.x - pad.w/2 for all pads)
x_max = max(pad.x + pad.w/2 for all pads)
y_min = min(pad.y - pad.h/2 for all pads)
y_max = max(pad.y + pad.h/2 for all pads)
```

### F.Fab (Component Outline)

Use the **silicon/package dimensions** from the datasheet, not the pad extents.

```
(fp_rect (start -W/2 Y_top) (end W/2 Y_bottom) (layer "F.Fab") ...)
```

### F.CrtYd (Courtyard)

Must encompass:
1. All copper pad extents + 0.25mm margin
2. Component body (F.Fab) + 0.25mm margin

Take the larger of the two for each edge:

```python
courtyard_x = max(copper_x_max, silicon_x_max) + 0.25
courtyard_y_top = min(copper_y_min, silicon_y_top) - 0.25
courtyard_y_bot = max(copper_y_max, silicon_y_bot) + 0.25
```

### F.SilkS (Silkscreen)

- Place slightly outside component body
- Do not overlap pads
- Include pin 1 marker (circle or chamfer indicator)

```
; Outline
(fp_line (start x1 y1) (end x2 y1) (layer "F.SilkS") (stroke (width 0.15) (type solid)))
...

; Pin 1 marker
(fp_circle (center X Y) (end X+0.2 Y) (layer "F.SilkS") (stroke (width 0.15) (type solid)) (fill none))
```

---

## 8. File Format Rules

### Critical Syntax Rules

| Rule | Correct | Incorrect |
|------|---------|-----------|
| No comments | (just data) | ; this is a comment |
| Quoted strings | "F.Cu" | F.Cu |
| Decimal values | 1.25 | 1,25 |
| Parentheses matched | (pad ...) | (pad ... |

**KiCad footprint format does NOT support semicolon comments.** All comments must be removed before saving.

### Minimal Valid Footprint Structure

```
(footprint "Name"
    (version 20240108)
    (generator "hand_coded")
    (layer "F.Cu")
    (attr smd)
    (fp_text reference "REF**" (at 0 -3) (layer "F.SilkS")
        (effects (font (size 1 1) (thickness 0.15)))
    )
    (fp_text value "Value" (at 0 3) (layer "F.Fab")
        (effects (font (size 1 1) (thickness 0.15)))
    )
    (pad "1" smd rect (at X Y) (size W H) (layers "F.Cu" "F.Paste" "F.Mask"))
    ...
    (fp_line ...)
    (fp_rect ...)
)
```

---

## 9. Verification Checklist

### Pad Verification

- [ ] Total pad count matches symbol pin count
- [ ] All pad numbers match symbol pin numbers
- [ ] Pad dimensions match datasheet land pattern
- [ ] Pad positions align with silicon edges (for non-protruding pins)
- [ ] Custom polygon pads render correctly

### Layer Verification

- [ ] F.Fab shows actual component body dimensions
- [ ] F.CrtYd encompasses all pads AND component body + margin
- [ ] F.SilkS does not overlap pads
- [ ] Pin 1 marker is visible and correct

### File Verification

- [ ] File loads without errors in KiCad
- [ ] No semicolon comments in file
- [ ] All parentheses balanced

### DRC Verification

- [ ] Run DRC on a test PCB with the footprint
- [ ] No courtyard violations
- [ ] No pad overlap errors

---

## 10. Worked Example: QFN-20 with E-Shaped Pads

### Component: MPM3610AGQV-Z

A 20-pin QFN power module with:
- 6 top pads (pins 13-18): 4 short, 2 long
- 3 left side pads (pins 1-3): chamfered pin 1
- 3 right side pads (pins 10-12)
- 2 center NC pads (pins 19-20)
- Left E-shape (pins 4-6): SW connections
- Right E-shape (pins 7-9): OUT connections

### Step 1: Extract Datasheet Dimensions

**Silicon outline:** 3mm W × 5mm H
- X: -1.5 to +1.5
- Y: -2.5 to +2.5 (but offset: -2.8 top, +2.225 bottom based on pad extents)

**Top pads (pins 13-18):**
- X positions: 0.5mm pitch, centered → ±1.25, ±0.75, ±0.25
- Short pads (outer 4): 0.25W × 0.70H, Y from -2.80 to -2.10, center Y = -2.45
- Long pads (center 2): 0.25W × 1.10H, Y from -2.80 to -1.70, center Y = -2.25

**Side pads:**
- Pin 1: 0.70W × 0.25H with 0.125mm 45° chamfer, outer edge at X = -1.80
- Pins 2, 3: 1.10W × 0.25H, outer edge at X = -1.80
- Pins 10, 11, 12: mirror of left side

**Center pads (pins 19-20):**
- Combined region: 1.15W × 0.79H
- Split into two: each 0.575W × 0.79H
- Y center: -0.575 (from dimensions 0.18 to 0.97 above horizontal datum)

**E-shaped pads:**
- Overall: 1.10W × 1.95H
- Teeth: 0.50W × 0.25H at Y = +0.40, +1.25, +2.10
- Vertical bar: 0.60W
- Left E: teeth from X = -1.80 to -1.30, bar from X = -1.30 to -0.70
- Right E: mirror

### Step 2: Calculate KiCad Coordinates

**Top pads:**
```
Pin 18: at (-1.25, -2.45), size (0.25, 0.70)  ; short
Pin 17: at (-0.75, -2.45), size (0.25, 0.70)  ; short
Pin 16: at (-0.25, -2.25), size (0.25, 1.10)  ; long
Pin 15: at (+0.25, -2.25), size (0.25, 1.10)  ; long
Pin 14: at (+0.75, -2.45), size (0.25, 0.70)  ; short
Pin 13: at (+1.25, -2.45), size (0.25, 0.70)  ; short
```

**Side pads:**
```
Pin 1:  at (-1.45, -1.55), custom with chamfer, effective 0.70W × 0.25H
Pin 2:  at (-1.25, -0.90), size (1.10, 0.25)
Pin 3:  at (-1.25, -0.25), size (1.10, 0.25)
Pin 12: at (+1.45, -1.55), size (0.70, 0.25)
Pin 11: at (+1.25, -0.90), size (1.10, 0.25)
Pin 10: at (+1.25, -0.25), size (1.10, 0.25)
```

**Center NC pads:**
```
Pin 19: at (-0.2875, -0.575), size (0.575, 0.79)
Pin 20: at (+0.2875, -0.575), size (0.575, 0.79)
```

**E-shaped pads (centers at tooth Y positions):**
```
Left E:  pads 4, 5, 6 at X = -1.25, Y = +0.40, +1.25, +2.10
Right E: pads 9, 8, 7 at X = +1.25, Y = +0.40, +1.25, +2.10
```

### Step 3: Define Outlines

**F.Fab (silicon):** (-1.5, -2.8) to (+1.5, +2.5)

**F.CrtYd (courtyard):**
- Copper X extent: -1.80 to +1.80 → add 0.25 → -2.05 to +2.05
- Copper Y extent: -2.80 to +2.225
- Silicon Y extent: -2.5 to +2.5
- Take max + margin: (-2.05, -3.05) to (+2.05, +2.75)

### Step 4: Write Footprint File

See the final output file for complete syntax. Key points:
- No semicolon comments
- Custom pads use gr_poly with coordinates relative to pad center
- E-shape pads split into 3 pads with overlapping bar sections

---

## Appendix A: Quick Reference

### Pad Position from Edge

Given outer edge position E and pad width W:
- Center = E - W/2 (for right/bottom edges)
- Center = E + W/2 (for left/top edges, with sign adjustment)

### Polygon Coordinate Direction

For filled polygons, vertices should be listed in order (clockwise or counter-clockwise). KiCad accepts either direction.

### Common Pitfalls

| Issue | Solution |
|-------|----------|
| Footprint won't load | Remove all semicolon comments |
| Pads in wrong position | Verify quadrant sign conversion |
| Custom pad not visible | Check (fill yes) in gr_poly |
| Courtyard DRC errors | Ensure courtyard covers silicon + margin |

---

*Guide version 1.0 - Created from MPM3610AGQV-Z footprint work session*
