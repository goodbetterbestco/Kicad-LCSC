# KiCad LCSC Library

Personal KiCad 9.0 component library optimized for JLCPCB/LCSC PCB assembly service.

## Features

- **230 parts** with complete metadata (LCSC part numbers, datasheets, descriptions)
- **57 active components** with verified datasheets from manufacturer sources
- **173 passive components** (resistors, capacitors, inductors, LEDs, connectors, switches)
- **Database library** for searchable parts with auto-populated fields
- **Custom footprints** matched to LCSC component specifications
- **Generic symbols** extracted from KiCad's Device library

## Repository Structure

```
├── 3rdparty/
│   └── LCSC/
│       ├── database/
│       │   ├── parts.csv          # Master parts list (source of truth)
│       │   ├── parts.db           # SQLite database (generated)
│       │   └── parts.kicad_dbl    # KiCad database library config
│       ├── datasheets/            # 57 PDF datasheets for active components
│       ├── footprints/
│       │   └── LCSC.pretty/       # 90+ custom footprints
│       └── symbols/
│           └── LCSC.kicad_sym     # Part-specific symbols
├── symbols/
│   └── Generics.kicad_sym         # Generic symbols (R, C, L, LED, etc.)
└── template/
    └── standard.kicad_wks         # Custom worksheet template
```

## Installation

### 1. Clone the repository

```bash
cd ~/Documents/KiCad/9.0
git clone https://github.com/goodbetterbestco/Kicad-LCSC.git .
```

Or clone elsewhere and symlink.

### 2. Install SQLite ODBC Driver

The database library requires an ODBC driver:

**macOS (Homebrew):**
```bash
brew install sqliteodbc
```

**Linux:**
```bash
sudo apt install libsqliteodbc
```

**Windows:**
Download from http://www.ch-werner.de/sqliteodbc/

### 3. Add Database Library to KiCad

1. Open KiCad → **Preferences → Manage Symbol Libraries**
2. Click **Add** (folder icon)
3. Navigate to: `3rdparty/LCSC/database/parts.kicad_dbl`
4. Click **OK**

### 4. Add Footprint Library

1. **Preferences → Manage Footprint Libraries**
2. Click **Add** (folder icon)  
3. Navigate to: `3rdparty/LCSC/footprints/LCSC.pretty`
4. Set nickname to `LCSC`

### 5. Add Symbol Libraries

1. **Preferences → Manage Symbol Libraries**
2. Add `symbols/Generics.kicad_sym` (nickname: `Generics`)
3. Add `3rdparty/LCSC/symbols/LCSC.kicad_sym` (nickname: `LCSC`)

## Usage

### Adding Parts

1. Press **A** in schematic editor
2. Search by value (e.g., "10k"), description ("LDO 3.3V"), or keywords ("esp32 wifi")
3. Select part from LCSC library
4. All fields auto-populate: LCSC number, footprint, datasheet, MPN, manufacturer

### Viewing Datasheets

Press **D** on any component to open its datasheet.

### BOM Export

The LCSC column exports directly for JLCPCB assembly orders.

## Parts Database Schema

| Column | Description | Example |
|--------|-------------|---------|
| LCSC | JLCPCB part number | C25804 |
| Reference | Schematic designator | R, C, U, Q |
| Value | Display value | 10kΩ, 100nF, ESP32-S3 |
| MPN | Manufacturer part number | 0603WAF1002T5E |
| Manufacturer | Component manufacturer | UniOhm, TI, Espressif |
| Symbol | KiCad symbol reference | Generics:R, LCSC:ESP32-S3 |
| Footprint | KiCad footprint reference | LCSC:R_smd_chip_0603 |
| Description | Human-readable description | 0603 ±1% 100mW |
| Keywords | Search terms | resistor res 10k smd 0603 |
| Datasheet | Direct PDF URL | https://... |
| Type | Classification | Active, Passive |

## Component Categories

### Active Components (57)

| Category | Count | Examples |
|----------|-------|----------|
| MCUs | 9 | STM32F072, ATMEGA328PB, ESP32-S3 |
| Power Management | 18 | LDOs, DC-DC converters, chargers |
| Transistors/MOSFETs | 10 | MMBT3904, DMG3415U, AO3401A |
| Interface ICs | 6 | MAX485, CH340N, TS3USB221 |
| Logic ICs | 6 | 74HC595, ULN2803A, 74HC4017D |
| LED/Motor Drivers | 4 | IS31FL3731, DRV8313, TLC5952 |
| Sensors | 2 | BMX055 IMU, ICS-43434 MEMS mic |
| Memory | 1 | W25N01GVZEIG NAND flash |
| Other | 1 | RV1106G3 camera SoC |

### Passive Components (173)

| Category | Count |
|----------|-------|
| Resistors | 58 |
| Capacitors | 51 |
| Inductors | 13 |
| LEDs | 16 |
| Diodes | 8 |
| Connectors | 12 |
| Switches | 11 |
| Crystals | 4 |

## Regenerating the Database

After modifying `parts.csv`:

```bash
cd 3rdparty/LCSC/database
rm -f parts.db
sqlite3 parts.db << EOF
.mode csv
.import parts.csv parts
EOF
```

## Adding New Parts

1. Add row to `parts.csv` with all fields
2. Ensure Symbol exists in `Generics.kicad_sym` or `LCSC.kicad_sym`
3. Ensure Footprint exists in `LCSC.pretty/`
4. Download datasheet to `datasheets/` folder (naming: `LCSC_PartName.pdf`)
5. Regenerate database (see above)
6. Restart KiCad

## License

Personal use library. Component symbols derived from KiCad's Device library (CC-BY-SA 4.0).

## Links

- [JLCPCB Assembly Service](https://jlcpcb.com/smt-assembly)
- [LCSC Parts Search](https://www.lcsc.com/)
- [KiCad Database Libraries Documentation](https://docs.kicad.org/master/en/eeschema/eeschema.html#database-libraries)
