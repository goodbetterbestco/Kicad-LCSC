# KiCad IC Symbol Creation Guide

A practical guide for creating professional IC symbols from datasheets.

---

## Quick Start Checklist

1. **Generate baseline** with `easyeda2kicad --lcsc_id CXXXXXX`
2. **Categorize all pins** by function (power, ground, input, output, etc.)
3. **Assign electrical types** using the decision framework
4. **Layout pins:**
   - Left side: power inputs, control inputs, grounds at bottom
   - Right side: power outputs, signal outputs, NC at bottom
   - Align bottom pins on both sides (grounds left ↔ NC right)
   - Flexible whitespace goes in the middle, not at top/bottom
5. **Draw rectangle:** one pin spacing (2.54mm) border beyond outermost pins on all sides
6. **Position properties:** Reference above rectangle, Value below

---

## Table of Contents

0. [Initial Symbol Generation](#0-initial-symbol-generation)
1. [Datasheet Analysis](#1-datasheet-analysis)
2. [Pin Naming Conventions](#2-pin-naming-conventions)
3. [Electrical Type Assignment](#3-electrical-type-assignment)
4. [Symbol Layout Rules](#4-symbol-layout-rules)
5. [Coordinate System](#5-coordinate-system)
6. [Verification Checklist](#6-verification-checklist)
7. [Worked Example: MPM3610AGQV-Z](#7-worked-example-mpm3610agqv-z)

---

## 0. Initial Symbol Generation

Generate baseline assets from LCSC/EasyEDA:

```bash
pip install easyeda2kicad --break-system-packages
easyeda2kicad --lcsc_id C5173872 --output ~/Documents/KiCad/9.0/3rdparty/LCSC
```

**What typically needs refinement:**
- Pin names (often verbose manufacturer designations)
- Electrical types (often all set to `unspecified`)
- Pin layout (usually matches physical package, not logical function)
- Symbol dimensions

---

## 1. Datasheet Analysis

### 1.1: Gather Pin Information

Extract from the datasheet:
- Total pin count
- Pin numbers (matching physical package)
- Pin names and functions
- Voltage levels and power domains

### 1.2: Categorize Every Pin

Create a table:

| Pin # | Mfr Name | Simplified Name | Category | Electrical Type | Side |
|-------|----------|-----------------|----------|-----------------|------|

**Standard categories:**

| Category | Examples | Typical Side |
|----------|----------|--------------|
| Power (positive) | VCC, VDD, VIN | Left-top |
| Power (analog) | AVCC, AVDD | Left-top |
| Ground | GND, AGND, PGND | Left-bottom |
| Control inputs | EN, RST, CS | Left |
| Signal inputs | RX, ADC_IN | Left |
| Power outputs | VOUT, OUT | Right-top |
| Signal outputs | TX, LED, PG | Right |
| Bidirectional | GPIO, SDA, USB_D± | Left or Right |
| Switching nodes | SW, LX | Right |
| Passive/External | BST, REXT, XTAL | Left or Bottom |
| No connect | NC | Right-bottom |

---

## 2. Pin Naming Conventions

### 2.1: General Rules

| Rule | Example |
|------|---------|
| Keep names short (≤12 chars) | `GPIO3_20` not `GPIO3_C4_FUNCTION_MUX` |
| Use underscores for separation | `ADC_IN0` not `ADCIN0` |
| Active-low uses ~{} notation | `~{RST}`, `~{CS}`, `~{OE}` |
| Differential pairs use +/- | `USB_D+`, `USB_D-` |

### 2.2: Power Pin Naming

| Type | Convention | Examples |
|------|------------|----------|
| Digital positive | VCC_xxx or VDD_xxx | `VCC`, `VCC_CORE` |
| Analog positive | AVCC_xxx | `AVCC`, `AVCC_PLL` |
| Ground | GND, AGND, PGND | Multiple pins can share names |

### 2.3: GPIO Naming Simplification

**Problem**: Manufacturer names like `GPIO3_C4_FUNCTION_MUX` are unusable.

**Solution**: Use GPIO bank + number notation.

**Letter-to-number conversion** (Rockchip, Allwinner, etc.):
- A = 0-7, B = 8-15, C = 16-23, D = 24-31

| Manufacturer Name | Simplified |
|-------------------|------------|
| GPIO3_A0 | GPIO3_0 |
| GPIO3_C4 | GPIO3_20 |
| GPIO1_D7 | GPIO1_31 |

---

## 3. Electrical Type Assignment

### 3.1: Type Definitions

| Type | Use For |
|------|---------|
| `input` | Signals that only receive (EN, CLK_IN, ADC inputs) |
| `output` | Signals that only drive (TX, LED, status, SW nodes) |
| `bidirectional` | Signals that can be both (GPIO, SDA, USB data) |
| `passive` | External components (crystals, bias resistors) |
| `power_in` | Power supply pins (VCC, VIN, GND) |
| `power_out` | Regulated outputs (VOUT, OUT) |
| `open_collector` | Pins that only sink current (PG, INT) |
| `no_connect` | NC pins |

### 3.2: Decision Framework

```
Is it a power/ground pin?
├─ Supply input (VCC, VIN, GND) → power_in
├─ Regulated output (VOUT) → power_out
│
Is it a GPIO or configurable?
├─ Yes → bidirectional
│
Does it connect to external passive? (crystal, resistor)
├─ Yes → passive (or input for XIN, output for XOUT)
│
Is it dedicated input only? (EN, RESET, FB)
├─ Yes → input
│
Is it dedicated output only? (TX, SW, status)
├─ Yes → output
│
Can it only pull low? (open drain PG, INT)
├─ Yes → open_collector
│
Is it NC?
├─ Yes → no_connect
│
Default → bidirectional
```

---

## 4. Symbol Layout Rules

### 4.1: Pin Placement by Side

| Left Side | Right Side |
|-----------|------------|
| Power inputs (VCC, VIN) | Power outputs (VOUT, OUT) |
| Control inputs (EN, FB) | Status outputs (PG) |
| Passive (BST) | Switching nodes (SW) |
| Grounds (AGND, PGND) | No connects (NC) |

### 4.2: Vertical Alignment Rules

**Critical:** Bottom pins on left and right must align vertically.

```
Left                          Right
─────────────────────────────────────
VCC          top              OUT
VIN                           OUT
                              OUT
EN           ← flexible →
FB           ← whitespace →   PG
BST                          
                              SW
                              SW
                              SW
AGND         bottom aligned   NC    ← same Y
PGND         with right →     NC    ← same Y
PGND                          NC
PGND                          NC
─────────────────────────────────────
```

**Rules:**
- Grounds go at bottom of left side
- NC pins go at bottom of right side
- Bottom-most pins on both sides share the same Y coordinate
- Flexible whitespace (visual grouping gaps) goes in the middle, never at top or bottom edges

### 4.3: Rectangle Border

The IC outline rectangle extends **one pin spacing (2.54mm / 100mil)** beyond the outermost pins on all sides.

| Edge | Calculation |
|------|-------------|
| Top | Topmost pin Y + 2.54mm |
| Bottom | Bottommost pin Y - 2.54mm |
| Left | -10.16mm typical (allows for pin length + name) |
| Right | +10.16mm typical |

### 4.4: Property Positions

| Property | Position |
|----------|----------|
| Reference | Centered above rectangle |
| Value | Centered below rectangle |
| Footprint, Datasheet, etc. | Below Value (hidden) |

---

## 5. Coordinate System

### 5.1: KiCad Symbol Coordinates

| Axis | Direction |
|------|-----------|
| X | Positive = Right |
| Y | Positive = Up |
| Origin | Center of symbol |

### 5.2: Pin Angles

| Side | Angle | Pin points toward... |
|------|-------|---------------------|
| Left | 0° | Right (into symbol) |
| Right | 180° | Left (into symbol) |
| Top | 270° | Down (into symbol) |
| Bottom | 90° | Up (into symbol) |

### 5.3: Standard Dimensions

| Element | Size |
|---------|------|
| Pin spacing | 2.54mm (100mil) |
| Pin length | 2.54mm (100mil) |
| Text size | 1.27mm (50mil) |
| Border offset | 2.54mm (100mil) |

---

## 6. Verification Checklist

### Pin Verification
- [ ] Total pin count matches datasheet
- [ ] All pin numbers match physical package
- [ ] Pin names are clear and consistent
- [ ] Electrical types are correct
- [ ] Duplicate names allowed only for power/ground

### Layout Verification
- [ ] Inputs on left, outputs on right
- [ ] Power at top, grounds at bottom-left, NC at bottom-right
- [ ] Bottom pins aligned on both sides
- [ ] Flexible whitespace in middle, not at edges
- [ ] Rectangle has one pin spacing border on all sides

### File Verification
- [ ] Symbol loads without errors
- [ ] Properties positioned correctly
- [ ] Footprint association correct
- [ ] ERC passes on test schematic

---

## 7. Worked Example: MPM3610AGQV-Z

A 20-pin QFN power module (DC-DC converter).

### 7.1: Pin Categorization

| Pin | Name | Category | Type | Side |
|-----|------|----------|------|------|
| 2 | VCC | Power in | power_in | Left-top |
| 16 | IN | Power in | power_in | Left-top |
| 17 | EN | Control | input | Left |
| 1 | FB | Control | input | Left |
| 11 | BST | Passive | passive | Left |
| 3 | AGND | Ground | power_in | Left-bottom |
| 12-14 | PGND | Ground | power_in | Left-bottom |
| 7-9 | OUT | Power out | power_out | Right-top |
| 18 | PG | Status | open_collector | Right |
| 4-6 | SW | Switching | output | Right |
| 10,15,19,20 | NC | No connect | no_connect | Right-bottom |

### 7.2: Layout Planning

```
Left (9 pins)                Right (11 pins)
────────────────────────────────────────────
VCC (2)       Y=15.24        OUT (7)
IN (16)       Y=12.7         OUT (8)
                             OUT (9)
EN (17)       Y=7.62         
FB (1)        Y=5.08         PG (18)
BST (11)      Y=2.54         
                             SW (4)
                             SW (5)
                             SW (6)
AGND (3)      Y=-10.16       NC (10)   ← aligned
PGND (12)     Y=-12.7        NC (15)   ← aligned
PGND (13)     Y=-15.24       NC (19)   ← aligned
PGND (14)     Y=-17.78       NC (20)   ← aligned
────────────────────────────────────────────
```

### 7.3: Rectangle Dimensions

- Top pin: Y = 15.24 → Rectangle top: 15.24 + 2.54 = **17.78**
- Bottom pin: Y = -17.78 → Rectangle bottom: -17.78 - 2.54 = **-20.32**
- Left/Right edges: **±10.16** (standard width for pin names)

### 7.4: Final Symbol Structure

```
(symbol "MPM3610AGQV-Z"
    (property "Reference" "U" (at 0 20.32 0) ...)
    (property "Value" "MPM3610AGQV-Z" (at 0 -22.86 0) ...)
    (property "Footprint" "LCSC:U_smd_QFN_20P" (at 0 -25.4 0) (hide yes) ...)
    
    (symbol "MPM3610AGQV-Z_0_1"
        (rectangle (start -10.16 17.78) (end 10.16 -20.32) ...)
    )
    
    (symbol "MPM3610AGQV-Z_1_1"
        ; Left side pins (angle 0)
        (pin power_in line (at -12.7 15.24 0) ... (name "VCC") (number "2"))
        (pin power_in line (at -12.7 12.7 0) ... (name "IN") (number "16"))
        (pin input line (at -12.7 7.62 0) ... (name "EN") (number "17"))
        (pin input line (at -12.7 5.08 0) ... (name "FB") (number "1"))
        (pin passive line (at -12.7 2.54 0) ... (name "BST") (number "11"))
        (pin power_in line (at -12.7 -10.16 0) ... (name "AGND") (number "3"))
        (pin power_in line (at -12.7 -12.7 0) ... (name "PGND") (number "12"))
        (pin power_in line (at -12.7 -15.24 0) ... (name "PGND") (number "13"))
        (pin power_in line (at -12.7 -17.78 0) ... (name "PGND") (number "14"))
        
        ; Right side pins (angle 180)
        (pin power_out line (at 12.7 15.24 180) ... (name "OUT") (number "7"))
        (pin power_out line (at 12.7 12.7 180) ... (name "OUT") (number "8"))
        (pin power_out line (at 12.7 10.16 180) ... (name "OUT") (number "9"))
        (pin open_collector line (at 12.7 5.08 180) ... (name "PG") (number "18"))
        (pin output line (at 12.7 0 180) ... (name "SW") (number "4"))
        (pin output line (at 12.7 -2.54 180) ... (name "SW") (number "5"))
        (pin output line (at 12.7 -5.08 180) ... (name "SW") (number "6"))
        (pin no_connect line (at 12.7 -10.16 180) ... (name "NC") (number "10"))
        (pin no_connect line (at 12.7 -12.7 180) ... (name "NC") (number "15"))
        (pin no_connect line (at 12.7 -15.24 180) ... (name "NC") (number "19"))
        (pin no_connect line (at 12.7 -17.78 180) ... (name "NC") (number "20"))
    )
)
```

### 7.5: Key Observations

1. **Bottom alignment**: AGND/PGND (left) and NC (right) share Y coordinates -10.16 through -17.78
2. **Flexible whitespace**: Gap between BST (Y=2.54) and AGND (Y=-10.16) on left; gap between SW and NC on right
3. **Rectangle border**: One pin spacing (2.54mm) beyond top pin (15.24→17.78) and bottom pin (-17.78→-20.32)
4. **Pin X positions**: ±12.7mm (rectangle edge ± pin length)

---

## Appendix: Quick Reference

### Pin Syntax
```
(pin <type> <style>
    (at <x> <y> <angle>)
    (length 2.54)
    (name "<name>" (effects (font (size 1.27 1.27))))
    (number "<num>" (effects (font (size 1.27 1.27))))
)
```

### Common Electrical Types
| Type | Keyword |
|------|---------|
| Input | `input` |
| Output | `output` |
| Bidirectional | `bidirectional` |
| Passive | `passive` |
| Power In | `power_in` |
| Power Out | `power_out` |
| Open Collector | `open_collector` |
| No Connect | `no_connect` |

### Standard Y Positions (100mil grid)
```
Pin 1:  15.24   (top)
Pin 2:  12.7
Pin 3:  10.16
Pin 4:   7.62
Pin 5:   5.08
Pin 6:   2.54
Pin 7:   0
Pin 8:  -2.54
Pin 9:  -5.08
Pin 10: -7.62
Pin 11: -10.16
Pin 12: -12.7
Pin 13: -15.24
Pin 14: -17.78  (bottom)
```

---

*Guide version 2.0 - Streamlined with explicit layout rules and practical example*
