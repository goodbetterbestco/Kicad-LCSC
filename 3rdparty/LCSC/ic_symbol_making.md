# KiCad IC Symbol Creation Guide

A comprehensive guide for creating professional, well-organized IC symbols from datasheets. This guide covers the complete workflow from datasheet analysis to final symbol verification.

---

## Table of Contents

1. [Philosophy & Goals](#1-philosophy--goals)
2. [Datasheet Analysis](#2-datasheet-analysis)
3. [Pin Naming Conventions](#3-pin-naming-conventions)
4. [Electrical Type Assignment](#4-electrical-type-assignment)
5. [Symbol Layout Planning](#5-symbol-layout-planning)
6. [Coordinate System Reference](#6-coordinate-system-reference)
7. [Calculating Dimensions](#7-calculating-dimensions)
8. [Pin Placement](#8-pin-placement)
9. [Text & Property Positioning](#9-text--property-positioning)
10. [Graphic Styles](#10-graphic-styles)
11. [Verification Checklist](#11-verification-checklist)
12. [Worked Example: RV1106G3](#12-worked-example-rv1106g3)
13. [Automating Symbol Creation](#13-automating-symbol-creation)

---

## 1. Philosophy & Goals

### Why Symbol Quality Matters

A well-designed schematic symbol:
- **Reduces errors** by grouping related pins logically
- **Improves readability** by using clear, consistent naming
- **Speeds up design** by placing pins where they're needed for typical routing
- **Enables ERC** (Electrical Rules Check) through correct electrical types

### Core Principles

1. **Function over form**: The symbol should represent the IC's logical function, not its physical pin arrangement
2. **Consistency**: Follow established conventions for naming, types, and layout
3. **Simplicity**: Prefer clear, short names over verbose manufacturer designations
4. **Schematic-friendly**: Power at top/bottom, signals on left/right, inputs left, outputs right

---

## 2. Datasheet Analysis

### Step 2.1: Gather Pin Information

Extract from the datasheet:
- Total pin count
- Pin numbers (matching the physical package)
- Manufacturer's pin names
- Pin descriptions/functions
- Voltage levels and power domains

### Step 2.2: Categorize Every Pin

Create a spreadsheet or table with columns:

| Pin # | Mfr Name | Category | Simplified Name | Electrical Type | Side |
|-------|----------|----------|-----------------|-----------------|------|

**Categories to identify:**

| Category | Examples | Typical Side |
|----------|----------|--------------|
| Power (digital) | VCC, VDD, VCORE | Top |
| Power (analog) | AVCC, AVDD | Top or Left-top |
| Ground | GND, AGND, VSS | Bottom or Top |
| Reset | RST, RESET, ~{RESET} | Left |
| Clock/Oscillator | XTAL, XIN, XOUT, CLK | Bottom |
| Digital inputs | EN, CS, ADDR | Left |
| Digital outputs | OUT, TX, LED | Right |
| Bidirectional | GPIO, SDA, D+/D- | Left or Right |
| Analog inputs | ADC_IN, MIC+/- | Left |
| Analog outputs | DAC_OUT, LINEOUT | Right |
| Differential pairs | TX+/TX-, RX+/RX- | Right (TX), Left (RX) |
| Passive/External | REXT, ZQ, VREF | Bottom |
| No connect | NC, DNC | Any (or omit) |

### Step 2.3: Identify Pin Groups

Look for natural groupings:
- GPIO banks (GPIO0_x, GPIO1_x, etc.)
- Peripheral interfaces (SPI, I2C, UART)
- Power domains
- Differential pairs

---

## 3. Pin Naming Conventions

### 3.1: General Rules

| Rule | Example |
|------|---------|
| Keep names short (≤12 chars ideal) | `GPIO3_20` not `GPIO3_C4_FUNCTION_MUX` |
| Use underscores for separation | `ADC_IN0` not `ADCIN0` |
| Capitalize consistently | `VCC_CORE` or `Vcc_Core`, not mixed |
| Active-low uses ~{} notation | `~{RST}`, `~{CS}`, `~{OE}` |
| Differential pairs use +/- | `USB_D+`, `USB_D-`, `ETH_TXP`, `ETH_TXN` |

### 3.2: Power Pin Naming

| Type | Convention | Examples |
|------|------------|----------|
| Digital positive | VCC_xxx or VDD_xxx | `VCC_CORE`, `VCC_IO`, `VDD_CPU` |
| Analog positive | AVCC_xxx or AVDD_xxx | `AVCC_PLL`, `AVCC_ADC` |
| Digital ground | GND | `GND` (can have multiple with same name) |
| Analog ground | AGND | `AGND` |
| Exposed pad | PAD or EP | `PAD` |

### 3.3: GPIO Naming Simplification

**Problem**: Manufacturer names like `VI_CIF_CLKO_M0/MIPI_CLK0_OUT/GPIO3_C4_d` are unusable.

**Solution**: Use GPIO bank + number notation.

**Letter-to-number conversion** (common in Rockchip, Allwinner, etc.):
- A = 0-7
- B = 8-15
- C = 16-23
- D = 24-31

**Examples**:
| Manufacturer Name | Simplified |
|-------------------|------------|
| GPIO3_A0 | GPIO3_0 |
| GPIO3_C4 | GPIO3_20 |
| GPIO1_D7 | GPIO1_31 |

### 3.4: Dedicated Function Pins

Keep descriptive names for pins with a single, dedicated function:

| Type | Examples |
|------|----------|
| USB | `USB_D+`, `USB_D-`, `USB_DET` |
| Ethernet | `ETH_TXP`, `ETH_TXN`, `ETH_RXP`, `ETH_RXN`, `ETH_REXT` |
| Audio | `LINEOUT`, `MIC0P`, `MIC0N`, `MICBIAS` |
| Oscillator | `OSC_XIN`, `OSC_XOUT`, `RTC_XIN`, `RTC_XOUT` |
| DDR | `DRAM_ZQ` |
| ADC | `ADC_IN0`, `ADC_IN1` |

---

## 4. Electrical Type Assignment

### 4.1: Type Definitions

| Type | Symbol | Use For |
|------|--------|---------|
| Input | → | Signals that only receive (EN, CLK_IN, ADC inputs) |
| Output | ← | Signals that only drive (TX, LED, status) |
| Bidirectional | ↔ | Signals that can be both (GPIO, SDA, USB data) |
| Passive | ─ | No electrical direction (crystals on connectors, test points) |
| Power input | ⊥ | Power supply pins (VCC, GND) |
| Power output | ⊤ | Voltage regulators, charge pumps |
| Open collector | ◇ | Pins that can only sink current (I2C on some ICs) |
| Open emitter | ◇ | Pins that can only source current |
| Tri-state | ≡ | Outputs with high-Z state |
| Unspecified | ? | When uncertain (avoid if possible) |

### 4.2: Decision Framework

```
Is it a power/ground pin?
├─ Yes → power_in (or power_out for regulators)
│
Is it a GPIO or can be configured as input OR output?
├─ Yes → bidirectional
│
Does it connect to external passive component? (crystal, resistor)
├─ Yes, on a connector symbol → passive
├─ Yes, on an IC symbol → Use functional type (input for XIN, output for XOUT)
│
Is it dedicated input only? (EN, RESET, ADC_IN)
├─ Yes → input
│
Is it dedicated output only? (TX, status LED)
├─ Yes → output
│
Can it only pull low? (open drain)
├─ Yes → open_collector
│
Default → bidirectional (safe choice for uncertain pins)
```

### 4.3: Common Pin Type Assignments

| Pin Type | Electrical Type | Notes |
|----------|-----------------|-------|
| VCC, VDD, AVCC | power_in | |
| GND, AGND, VSS | power_in | |
| PAD (exposed) | power_in | Usually ground |
| ~{RST}, RESET | input | |
| OSC_XIN, RTC_XIN | input | Crystal input |
| OSC_XOUT, RTC_XOUT | output | Crystal output |
| GPIO_x | bidirectional | |
| USB_D+, USB_D- | bidirectional | |
| SDA, SDB | bidirectional | I2C data |
| SCL | bidirectional | I2C clock (can be stretched) |
| ETH_TXP/TXN | output | Transmit differential |
| ETH_RXP/RXN | input | Receive differential |
| ETH_REXT | passive | External bias resistor |
| DRAM_ZQ | passive | Impedance calibration |
| ADC_INx | input | |
| LINEOUT | output | Audio output |
| MICxP, MICxN | input | Microphone differential |
| MICBIAS | output | Bias voltage for mics |
| VCM (audio) | passive | Common mode reference |

---

## 5. Symbol Layout Planning

### 5.1: Standard IC Layout Convention

```
                    ┌─────────────────────┐
     Power In ──────┤ TOP: VCC, AVCC      │
                    │                     │
   Inputs ──────────┤ LEFT          RIGHT ├────────── Outputs
   Bidirectional ───┤                     ├─── Bidirectional
                    │                     │
     Ground ────────┤ BOTTOM: GND, Xtals  │
                    └─────────────────────┘
```

### 5.2: Pin Side Assignment Strategy

**Step 1**: Count pins by category

| Category | Count | Preferred Side |
|----------|-------|----------------|
| Digital VCC | 20 | Top |
| Analog AVCC | 8 | Left-top |
| Ground | 3 | Bottom |
| Oscillators | 4 | Bottom |
| Passive | 3 | Bottom |
| Inputs | 10 | Left |
| Outputs | 8 | Right |
| GPIO | 75 | Left/Right (split) |

**Step 2**: Determine optimal dimensions

For a rectangular symbol (typical for large ICs):
- Find the natural width based on power pin count
- Calculate height based on remaining pins ÷ 2

**Step 3**: Balance left and right sides

- Keep GPIO banks together when possible
- Split the largest bank if needed to balance

### 5.3: Grouping Principles

**Within each side, order pins by:**
1. Power pins first (top of left side if AVCC on left)
2. Dedicated function pins grouped by peripheral
3. GPIO banks in numerical order
4. Higher-numbered GPIO toward bottom

**Separate groups visually** (in your mental model; KiCad doesn't have visual separators in symbols).

---

## 6. Coordinate System Reference

### 6.1: KiCad Symbol Coordinate System

```
                     -Y (top of screen)
                          ↑
                          │
       -X (left) ←────────┼────────→ +X (right)
                          │
                          ↓
                     +Y (bottom of screen)
```

**Key insight**: +Y goes DOWN on screen (opposite of standard math coordinates).

### 6.2: Pin Orientation Angles

The angle specifies **which direction the pin wire points FROM the connection point**:

| Angle | Wire Points | Use For | Pin connects to |
|-------|-------------|---------|-----------------|
| 0° | → Right | Left-side pins | Left of symbol |
| 90° | ↑ Up | Bottom-side pins | Below symbol |
| 180° | ← Left | Right-side pins | Right of symbol |
| 270° | ↓ Down | Top-side pins | Above symbol |

**Visual representation**:
```
                    270° (wire points down)
                          │
                          ●  ← connection point above symbol
                          │
                    ┌─────┴─────┐
                    │           │
    0° ───●─────────┤   BODY    ├─────────●─── 180°
   (right)          │           │        (left)
                    └─────┬─────┘
                          │
                          ●  ← connection point below symbol
                          │
                    90° (wire points up)
```

### 6.3: Pin Position = Connection Point

**Critical**: The (X, Y) coordinate of a pin is where the **wire connects** (outside the rectangle), not where the pin meets the body.

```
Pin at X=-1250, angle=0°:

    Connection point      Body edge        Inside body
          ●─────────────────┼───────────────────
       X=-1250           X=-1150
       
    ←── pin length ──→
        (100 mils)
```

---

## 7. Calculating Dimensions

### 7.1: Standard Grid and Sizing (in mils)

| Element | Value | Notes |
|---------|-------|-------|
| Pin spacing | 100 | Adjacent pins |
| Pin length | 100 | Standard for ICs |
| Border offset | 200 | First pin from corner |
| Text size | 50 | Pin name and number |
| Grid snap | 50 | KiCad default |

### 7.2: Dimension Formulas

**Width** (horizontal dimension):
```
width = (max_horizontal_pins - 1) × 100 + 2 × 200
      = (max_horizontal_pins - 1) × 100 + 400

Example: 20 pins on top
width = (20 - 1) × 100 + 400 = 1900 + 400 = 2300 mils
```

**Height** (vertical dimension):
```
height = (max_vertical_pins - 1) × 100 + 2 × 200
       = (max_vertical_pins - 1) × 100 + 400

Example: 49 pins on left/right
height = (49 - 1) × 100 + 400 = 4800 + 400 = 5200 mils
```

### 7.3: Rectangle Coordinates

For a symbol centered at origin:
```
x1 = -width/2    (left edge)
x2 = +width/2    (right edge)
y1 = depends on layout (see below)
y2 = depends on layout (see below)
```

**Asymmetric adjustment**: If top and bottom have different pin counts, extend the rectangle to accommodate text overlap:

| Scenario | Adjustment |
|----------|------------|
| Text overlapping corner | Extend that edge 100-400 mils |
| Fewer pins on one side | Align pins to left (top/bottom) or top (left/right) |

---

## 8. Pin Placement

### 8.1: Position Calculation

**Top pins** (wire connects above, angle 270°):
```
X: start at -width/2 + 200, increment by 100
Y: -height/2 - pin_length (above top edge)
Angle: 270
```

**Bottom pins** (wire connects below, angle 90°):
```
X: start at -width/2 + 200, increment by 100  
Y: +height/2 + pin_length (below bottom edge)
Angle: 90
```

**Left pins** (wire connects left, angle 0°):
```
X: -width/2 - pin_length (left of left edge)
Y: start at -height/2 + 200, increment by 100
Angle: 0
```

**Right pins** (wire connects right, angle 180°):
```
X: +width/2 + pin_length (right of right edge)
Y: start at -height/2 + 200, increment by 100
Angle: 180
```

### 8.2: Example Pin Placement

For a 2300×5750 mil symbol:
- Rectangle: X = ±1150, Y = -2850 to +2900
- Left pins: X = -1250, Y from -2400 to +2400
- Right pins: X = +1250, Y from -2400 to +2400
- Top pins: Y = +3000, X from -950 to +950
- Bottom pins: Y = -2950, X from -950 to +50

---

## 9. Text & Property Positioning

### 9.1: Required Properties

| Property | Position | Visibility |
|----------|----------|------------|
| Reference (U?) | Above symbol | Visible |
| Value (part name) | Below symbol | Visible |
| Footprint | Below Value | Usually visible |
| Datasheet | Below Footprint | Often hidden |
| LCSC/MPN | Below Footprint | Optional |

### 9.2: Spacing Guidelines

Properties below the symbol should be spaced to avoid overlap:
```
Bottom pins end at: Y_bottom_pin + text_extent (~400 mils)
Value: Y_bottom_pin - 500 to 600 mils
Footprint: Value_Y - 100 mils
LCSC: Footprint_Y - 100 mils
```

### 9.3: Avoiding Corner Overlap

Pin names on left/right sides render inside the rectangle. Long names near corners can overlap with top/bottom pin numbers.

**Solutions**:
1. Extend top/bottom edges outward (adds 100-300 mils)
2. Use shorter pin names
3. Accept minor overlap (common in dense symbols)

---

## 10. Graphic Styles

### 10.1: Pin Graphic Styles

| Style | KiCad Name | Use For |
|-------|------------|---------|
| Line | `line` | Most pins |
| Inverted | `inverted` | Active-low inputs (~{RST}) |
| Clock | `clock` | Clock inputs |
| Inverted Clock | `inverted_clock` | Active-low clock |
| Input Low | `input_low` | Active-low with line |
| Output Low | `output_low` | Active-low output |
| Edge Clock Low | `edge_clock_high` | Rising edge clock |
| Non-logic | `non_logic` | Analog, power |

### 10.2: Standard Settings

| Setting | Value |
|---------|-------|
| Pin length | 100 mils (2.54 mm) |
| Name text size | 50 mils (1.27 mm) |
| Number text size | 50 mils (1.27 mm) |
| Line width | 10 mils (0.254 mm) |

---

## 11. Verification Checklist

### Before Finalizing

- [ ] **Pin count matches datasheet**
- [ ] **All pin numbers match physical package**
- [ ] **No duplicate pin numbers**
- [ ] **Pin names are readable and consistent**
- [ ] **Electrical types are appropriate for ERC**
- [ ] **Active-low pins use ~{} notation and inverted style**
- [ ] **Power pins are type power_in**
- [ ] **All pins visible (unless intentionally hidden)**

### Visual Inspection

- [ ] **No text overlaps**
- [ ] **Pins align to 50-mil grid**
- [ ] **Reference visible above symbol**
- [ ] **Value visible below symbol**
- [ ] **Logical grouping of related pins**
- [ ] **Adequate spacing at corners**

### Functional Test

- [ ] **Place symbol in schematic**
- [ ] **Connect power symbols (VCC, GND)**
- [ ] **Run ERC - no unexpected errors**
- [ ] **Assign footprint and verify pin mapping**

---

## 12. Worked Example: RV1106G3

### 12.1: Chip Overview

- **Part**: Rockchip RV1106G3 (Camera/Display SoC)
- **Package**: QFN-128 + exposed pad = 129 pins
- **Function**: Embedded processor with camera input, display output, Ethernet, USB, audio

### 12.2: Pin Categorization Results

| Category | Count | Assignment |
|----------|-------|------------|
| Digital VCC (VCC_CORE, VCC_CPU, VCC_DDR, VCC_PLL, VCC_PMU, VCC_GPIO) | 20 | Top |
| Analog VCC (AVCC_*) | 8 | Left-top |
| Ground (GND, AGND, PAD) | 3 | Bottom |
| Oscillator (OSC, RTC) | 4 | Bottom |
| Passive (DRAM_ZQ, ETH_REXT) | 2 | Bottom |
| ADC inputs | 2 | Bottom |
| Reset, USB_DET, MIC inputs | 7 | Left |
| GPIO Bank 0 | 7 | Right |
| GPIO Bank 1 (split) | 22 | 5 Left, 17 Right |
| GPIO Bank 2 | 10 | Left |
| GPIO Bank 3 (split) | 27 | 10 Left, 17 Right |
| GPIO Bank 4 | 10 | Left |
| USB, Audio out, Ethernet | 11 | Right |

### 12.3: Naming Simplification

**Before** (manufacturer):
```
VI_CIF_CLKO_M0/MIPI_CLK0_OUT/GPIO3_C4_d
```

**After** (simplified):
```
GPIO3_20
```

**Conversion**: C = 16-23, so C4 = 16+4 = 20

### 12.4: Final Dimensions

| Parameter | Value |
|-----------|-------|
| Width | 2300 mils (20 pins × 100 + 400) |
| Height | 5750 mils (adjusted for text) |
| Top pins | 20 at Y = +3000 |
| Bottom pins | 11 at Y = -2950 |
| Left pins | 49 at X = -1250 |
| Right pins | 49 at X = +1250 |
| Rectangle | (-1150, -2850) to (+1150, +2900) |

### 12.5: Property Positions

| Property | Y Position |
|----------|------------|
| Reference | +3500 mils |
| Value | -3500 mils |
| Footprint | -3600 mils |
| LCSC | -3700 mils |
| Datasheet | -3800 mils |

---

## 13. Automating Symbol Creation

### 13.1: Script Workflow Overview

```
1. Define pin layout data structure
2. Read KiCad symbol library file
3. Find target symbol block
4. Parse and update each pin block
5. Update rectangle coordinates  
6. Update property positions
7. Create backup of original file
8. Write modified content
9. Verify pin count matches expected
```

### 13.2: KiCad Symbol Library Structure

A `.kicad_sym` file is an S-expression format:

```lisp
(kicad_symbol_lib
    (version 20231120)
    (generator "kicad_symbol_editor")
    (symbol "PART_NAME"
        (property "Reference" "U" (at X Y angle) ...)
        (property "Value" "PART_NAME" (at X Y angle) ...)
        (property "Footprint" "..." (at X Y angle) ...)
        (property "Datasheet" "..." (at X Y angle) ...)
        (symbol "PART_NAME_1_1"
            (rectangle (start X1 Y1) (end X2 Y2) ...)
            (pin type style (at X Y angle) (length L) (name "N" ...) (number "1" ...))
            (pin type style (at X Y angle) (length L) (name "N" ...) (number "2" ...))
            ...
        )
    )
    (symbol "ANOTHER_PART" ...)
)
```

**Key observations:**
- Symbols are nested inside the library
- Properties (Reference, Value, etc.) are at the symbol level
- Graphics (rectangle, pins) are in the `PART_NAME_1_1` sub-symbol
- All coordinates are in millimeters

### 13.3: Pin Data Structure

Define pins as a dictionary mapping pin number to attributes:

```python
# pin_number -> (name, electrical_type, graphic_style, x_mils, y_mils, angle)
PIN_LAYOUT = {
    "1": ("VCC_GPIO7", "power_in", "line", 950, 3000, 270),
    "2": ("GPIO3_20", "bidirectional", "line", 1250, 1700, 180),
    "57": ("GND", "power_in", "line", -950, -2950, 90),
    "66": ("~{RST}", "input", "inverted", -1250, -1600, 0),
    # ... all 129 pins
}
```

**Electrical type keywords:**
```python
ELECTRICAL_TYPES = {
    "input", "output", "bidirectional", "passive",
    "power_in", "power_out", "open_collector", 
    "open_emitter", "tri_state", "unspecified"
}
```

**Graphic style keywords:**
```python
GRAPHIC_STYLES = {
    "line", "inverted", "clock", "inverted_clock",
    "input_low", "output_low", "edge_clock_high", 
    "edge_clock_low", "non_logic"
}
```

### 13.4: Unit Conversion

KiCad uses millimeters internally; design is easier in mils:

```python
def mils_to_mm(mils):
    """Convert mils to mm, rounded to 2 decimal places."""
    return round(mils * 0.0254, 2)

# Constants in mils
PIN_LENGTH = 100
TEXT_SIZE = 50
PIN_SPACING = 100
BORDER_OFFSET = 200
```

### 13.5: Finding Symbol Block

Use regex to locate a symbol within the library:

```python
import re

def find_symbol_block(content, symbol_name):
    """Find start and end indices of a symbol in library content."""
    # Pattern matches (symbol "NAME" and tracks parenthesis depth
    pattern = rf'\(symbol\s+"{re.escape(symbol_name)}"'
    match = re.search(pattern, content)
    
    if not match:
        return None, None
    
    start = match.start()
    depth = 0
    
    for i, char in enumerate(content[start:], start):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return start, i + 1
    
    return None, None
```

### 13.6: Finding Pin Blocks

Extract individual pin definitions:

```python
def find_pin_blocks(symbol_text):
    """Find all (pin ...) blocks in symbol text."""
    blocks = []
    i = 0
    
    while True:
        # Find next pin block start
        match = re.search(r'\(pin\s+', symbol_text[i:])
        if not match:
            break
        
        start = i + match.start()
        depth = 0
        
        # Find matching closing paren
        for j, char in enumerate(symbol_text[start:], start):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    blocks.append((start, j + 1))
                    i = j + 1
                    break
        else:
            break
    
    return blocks

def extract_pin_number(pin_block):
    """Extract pin number from a pin block."""
    match = re.search(r'\(number\s+"(\d+)"', pin_block)
    return match.group(1) if match else None
```

### 13.7: Updating Pin Block

Replace pin attributes using regex substitution:

```python
def update_pin_block(pin_block, name, pin_type, style, x_mils, y_mils, angle):
    """Update all attributes of a pin block."""
    
    x_mm = mils_to_mm(x_mils)
    y_mm = mils_to_mm(y_mils)
    length_mm = mils_to_mm(PIN_LENGTH)
    text_mm = mils_to_mm(TEXT_SIZE)
    
    # Update pin type and style (first line)
    # (pin input line  ->  (pin bidirectional line
    pin_block = re.sub(
        r'\(pin\s+\w+\s+\w+',
        f'(pin {pin_type} {style}',
        pin_block
    )
    
    # Update position and angle
    # (at -12.7 5.08 0)  ->  (at -31.75 -40.64 0)
    pin_block = re.sub(
        r'\(at\s+[-\d.]+\s+[-\d.]+\s+\d+\)',
        f'(at {x_mm} {y_mm} {angle})',
        pin_block
    )
    
    # Update length
    pin_block = re.sub(
        r'\(length\s+[-\d.]+\)',
        f'(length {length_mm})',
        pin_block
    )
    
    # Update pin name
    pin_block = re.sub(
        r'\(name\s+"[^"]*"',
        f'(name "{name}"',
        pin_block
    )
    
    # Update name font size
    pin_block = re.sub(
        r'(\(name\s+"[^"]*"\s*\(effects\s*\(font\s*\(size\s+)[\d.]+\s+[\d.]+',
        rf'\g<1>{text_mm} {text_mm}',
        pin_block
    )
    
    # Update number font size
    pin_block = re.sub(
        r'(\(number\s+"\d+"\s*\(effects\s*\(font\s*\(size\s+)[\d.]+\s+[\d.]+',
        rf'\g<1>{text_mm} {text_mm}',
        pin_block
    )
    
    return pin_block
```

### 13.8: Updating Rectangle

```python
def update_rectangle(symbol_text, x1_mils, y1_mils, x2_mils, y2_mils):
    """Update symbol rectangle coordinates."""
    x1 = mils_to_mm(x1_mils)
    y1 = mils_to_mm(y1_mils)
    x2 = mils_to_mm(x2_mils)
    y2 = mils_to_mm(y2_mils)
    
    pattern = r'\(rectangle\s+\(start\s+[-\d.]+\s+[-\d.]+\)\s+\(end\s+[-\d.]+\s+[-\d.]+\)'
    replacement = f'(rectangle (start {x1} {y1}) (end {x2} {y2})'
    
    return re.sub(pattern, replacement, symbol_text)
```

### 13.9: Updating Property Positions

```python
def update_property_positions(symbol_text, positions):
    """
    Update property text positions.
    
    positions = {
        "Reference": (x_mils, y_mils),
        "Value": (x_mils, y_mils),
        "Footprint": (x_mils, y_mils),
        ...
    }
    """
    for prop_name, (x_mils, y_mils) in positions.items():
        x_mm = mils_to_mm(x_mils)
        y_mm = mils_to_mm(y_mils)
        
        pattern = rf'(\(property\s+"{prop_name}"\s+"[^"]*"\s*\(at\s+)[-\d.]+\s+[-\d.]+(\s+\d+\))'
        replacement = rf'\g<1>{x_mm} {y_mm}\2'
        
        symbol_text = re.sub(pattern, replacement, symbol_text)
    
    return symbol_text
```

### 13.10: Complete Script Structure

```python
#!/usr/bin/env python3
"""
KiCad Symbol Layout Updater

Usage: python3 update_symbol.py
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
LIBRARY_PATH = Path.home() / "Documents/KiCad/9.0/3rdparty/LCSC/symbols/LCSC.kicad_sym"
SYMBOL_NAME = "RV1106G3"

# Unit conversion
def mils_to_mm(mils):
    return round(mils * 0.0254, 2)

# Pin layout definition
PIN_LAYOUT = {
    # pin_number: (name, type, style, x_mils, y_mils, angle)
    "1": ("VCC_GPIO7", "power_in", "line", 950, 3000, 270),
    # ... define all pins ...
}

# Rectangle dimensions
RECT_X1, RECT_Y1 = -1150, -2850  # mils
RECT_X2, RECT_Y2 = 1150, 2900    # mils

# Property positions
PROPERTY_POSITIONS = {
    "Reference": (0, 3500),
    "Value": (0, -3500),
    "Footprint": (0, -3600),
    "LCSC": (0, -3700),
    "Datasheet": (0, -3800),
}

def find_symbol_block(content, name): ...
def find_pin_blocks(text): ...
def extract_pin_number(block): ...
def update_pin_block(block, name, type, style, x, y, angle): ...
def update_rectangle(text, x1, y1, x2, y2): ...
def update_property_positions(text, positions): ...

def main():
    # Read library
    content = LIBRARY_PATH.read_text()
    
    # Find symbol
    start, end = find_symbol_block(content, SYMBOL_NAME)
    if start is None:
        print(f"Symbol '{SYMBOL_NAME}' not found")
        return 1
    
    symbol_text = content[start:end]
    
    # Update pins
    pin_blocks = find_pin_blocks(symbol_text)
    for block_start, block_end in reversed(pin_blocks):
        block = symbol_text[block_start:block_end]
        pin_num = extract_pin_number(block)
        
        if pin_num in PIN_LAYOUT:
            name, ptype, style, x, y, angle = PIN_LAYOUT[pin_num]
            new_block = update_pin_block(block, name, ptype, style, x, y, angle)
            symbol_text = symbol_text[:block_start] + new_block + symbol_text[block_end:]
    
    # Update rectangle
    symbol_text = update_rectangle(symbol_text, RECT_X1, RECT_Y1, RECT_X2, RECT_Y2)
    
    # Update properties
    symbol_text = update_property_positions(symbol_text, PROPERTY_POSITIONS)
    
    # Backup original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = LIBRARY_PATH.with_suffix(f".kicad_sym.{timestamp}.bak")
    shutil.copy(LIBRARY_PATH, backup)
    
    # Write modified
    new_content = content[:start] + symbol_text + content[end:]
    LIBRARY_PATH.write_text(new_content)
    
    print(f"Updated {len(PIN_LAYOUT)} pins")
    print(f"Backup: {backup.name}")
    return 0

if __name__ == "__main__":
    exit(main())
```

### 13.11: Generating PIN_LAYOUT from Datasheet

To create the PIN_LAYOUT dictionary:

1. **Export pin table from datasheet PDF** (or manually transcribe)

2. **Create CSV with columns:**
   ```
   pin_number,mfr_name,simplified_name,category
   1,VCC_IO7,VCC_GPIO7,power
   2,GPIO3_C4_xxx,GPIO3_20,gpio
   ...
   ```

3. **Process CSV to assign positions:**
   ```python
   def assign_positions(pins_by_category):
       layout = {}
       
       # Top side: power pins
       top_pins = pins_by_category['vcc']
       x = -950  # starting X
       for pin in top_pins:
           layout[pin.number] = (pin.name, "power_in", "line", x, 3000, 270)
           x += 100
       
       # Left side: AVCC, inputs, GPIO banks
       left_pins = pins_by_category['avcc'] + pins_by_category['input'] + ...
       y = -2400  # starting Y
       for pin in left_pins:
           layout[pin.number] = (pin.name, pin.type, "line", -1250, y, 0)
           y += 100
       
       # ... similar for right and bottom
       
       return layout
   ```

4. **Verify counts:**
   ```python
   assert len([p for p in layout.values() if p[5] == 270]) == expected_top_count
   assert len([p for p in layout.values() if p[5] == 90]) == expected_bottom_count
   # etc.
   ```

### 13.12: Error Handling Considerations

```python
# Verify all pins were updated
updated = set()
for block_start, block_end in pin_blocks:
    pin_num = extract_pin_number(symbol_text[block_start:block_end])
    if pin_num in PIN_LAYOUT:
        updated.add(pin_num)

missing = set(PIN_LAYOUT.keys()) - updated
if missing:
    print(f"WARNING: Pins not found in symbol: {missing}")

extra = updated - set(PIN_LAYOUT.keys())  
if extra:
    print(f"WARNING: Pins in symbol not in layout: {extra}")
```

### 13.13: Testing Strategy

1. **Create test symbol** with known pins to verify coordinate system
2. **Run script on backup** before modifying production library
3. **Visual inspection in KiCad** after each major change
4. **Compare pin counts** before and after
5. **Run ERC** on test schematic with updated symbol

---

## Appendix A: KiCad Symbol File Format

### Pin Syntax
```
(pin <type> <style>
    (at <x_mm> <y_mm> <angle>)
    (length <length_mm>)
    (name "<name>"
        (effects (font (size <h> <w>)))
    )
    (number "<num>"
        (effects (font (size <h> <w>)))
    )
)
```

### Rectangle Syntax
```
(rectangle
    (start <x1_mm> <y1_mm>)
    (end <x2_mm> <y2_mm>)
    (stroke (width 0.254) (type default))
    (fill (type background))
)
```

### Unit Conversion
```
mm = mils × 0.0254
mils = mm ÷ 0.0254
```

---

## Appendix B: Quick Reference Card

### Pin Angles
| Side | Angle |
|------|-------|
| Left | 0° |
| Bottom | 90° |
| Right | 180° |
| Top | 270° |

### Electrical Types
| Type | Keyword |
|------|---------|
| Input | `input` |
| Output | `output` |
| Bidirectional | `bidirectional` |
| Passive | `passive` |
| Power In | `power_in` |
| Power Out | `power_out` |
| Open Collector | `open_collector` |
| Open Emitter | `open_emitter` |
| Tri-state | `tri_state` |

### Standard Sizes (mils)
| Element | Size |
|---------|------|
| Pin spacing | 100 |
| Pin length | 100 |
| Text size | 50 |
| Border offset | 200 |
| Property spacing | 100 |

---

*Guide version 1.0 - Created based on RV1106G3 symbol development session*
