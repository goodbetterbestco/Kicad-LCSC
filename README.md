# KiCad LCSC Library

Personal KiCad 9.0 component library optimized for JLCPCB/LCSC PCB assembly service.

## Features

- **247 parts** with complete metadata (LCSC part numbers, descriptions, keywords)
- **67 active components** (MCUs, power management, interfaces, sensors)
- **180 passive components** (resistors, capacitors, inductors, LEDs, connectors, switches)
- **Database library** for searchable parts with auto-populated fields
- **123 custom footprints** matched to LCSC component specifications
- **110+ 3D models** in STEP format for board visualization
- **13 generic symbols** extracted from KiCad's Device library

## Repository Structure

```
├── 3rdparty/
│   └── LCSC/
│       ├── database/
│       │   ├── parts.csv          # Master parts list (source of truth)
│       │   ├── parts.db           # SQLite database (generated, not tracked)
│       │   ├── parts.kicad_dbl    # KiCad database library config
│       │   ├── rebuild_db.py      # Script to regenerate parts.db
│       │   └── setup_kicad.py     # Automated setup script
│       ├── datasheets/            # PDF datasheets (not distributed, see below)
│       ├── footprints/
│       │   └── LCSC.pretty/       # 123 custom footprints
│       └── symbols/
│           └── LCSC.kicad_sym     # 81 part-specific symbols
├── 3dmodels/                      # 110+ STEP files for 3D visualization
├── symbols/
│   └── Generics.kicad_sym         # 13 generic symbols (R, C, L, D, LED, etc.)
└── template/
    └── standard.kicad_wks         # Custom worksheet template
```

## Installation

### Quick Setup (macOS)

```bash
# 1. Clone the repository
cd ~/Documents/KiCad/9.0
git clone https://github.com/goodbetterbestco/Kicad-LCSC.git .

# 2. Launch KiCad 9.0 once (creates preferences directory), then quit

# 3. Run the setup script
python3 3rdparty/LCSC/database/setup_kicad.py

# 4. Restart KiCad
```

The setup script automatically:
- Installs ODBC drivers via Homebrew (if needed)
- Configures `~/.odbcinst.ini`
- Builds `parts.db` from `parts.csv`
- Adds path variables to KiCad
- Configures symbol and footprint libraries

### Manual Setup

<details>
<summary>Click to expand manual installation steps</summary>

#### Install SQLite ODBC Driver

**macOS (Homebrew):**
```bash
brew install unixodbc sqliteodbc
```

Create/update `~/.odbcinst.ini`:
```ini
[SQLite3]
Description=SQLite3 ODBC Driver
Driver=/opt/homebrew/lib/libsqlite3odbc.dylib
Setup=/opt/homebrew/lib/libsqlite3odbc.dylib
UsageCount=1
```

*Note: Use `/usr/local/lib/libsqlite3odbc.dylib` on Intel Macs.*

**Linux (Debian/Ubuntu):**
```bash
sudo apt install unixodbc libsqliteodbc
```

**Windows:**
Download from http://www.ch-werner.de/sqliteodbc/

#### Build the Database

```bash
cd ~/Documents/KiCad/9.0/3rdparty/LCSC/database
python3 rebuild_db.py
```

#### Configure KiCad Path Variables

1. Open KiCad → **Preferences → Configure Paths**
2. Add variable: `KICAD9_3RD_PARTY` → `/Users/YOUR_USERNAME/Documents/KiCad/9.0/3rdparty`
3. Add variable: `KICAD9_3DMODEL_DIR` → `/Users/YOUR_USERNAME/Documents/KiCad/9.0/3dmodels`

#### Add Symbol Libraries

1. **Preferences → Manage Symbol Libraries**
2. Add `symbols/Generics.kicad_sym` (nickname: `Generics`, check **Hidden**)
3. Add `3rdparty/LCSC/symbols/LCSC.kicad_sym` (nickname: `LCSC`, check **Hidden**)
4. Add `3rdparty/LCSC/database/parts.kicad_dbl` (nickname: `parts`)

#### Add Footprint Library

1. **Preferences → Manage Footprint Libraries**
2. Add `3rdparty/LCSC/footprints/LCSC.pretty` (nickname: `LCSC`)

</details>

### Datasheets

Datasheets are not tracked in git. If migrating from another workstation, manually copy:
```
~/Documents/KiCad/9.0/3rdparty/LCSC/datasheets/
```

## Usage

### Adding Parts

1. Press **A** in schematic editor
2. Search by value (e.g., "10k"), description ("LDO 3.3V"), or keywords ("esp32 wifi")
3. Select part from **parts** library
4. All fields auto-populate: LCSC number, footprint, datasheet, MPN, manufacturer

### Viewing Datasheets

Press **D** on any component to open its datasheet (if you've downloaded it locally).

### BOM Export

The LCSC column exports directly for JLCPCB assembly orders.

## Datasheets

**Datasheets are not distributed with this repository** due to licensing considerations.

The `Datasheet` column in `parts.csv` references local paths in the format:
```
datasheets/CLCSC_MPN.pdf
```

To enable datasheet linking:

1. Create the folder: `3rdparty/LCSC/datasheets/`
2. Download datasheets from LCSC or manufacturer sites
3. Name files to match the pattern: `C12345_PartNumber.pdf`
4. Press **D** on any component to open its datasheet

The datasheets folder is gitignored.

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
| Datasheet | Local path | datasheets/C25804_xxx.pdf |
| Type | Classification | Active, Passive |

## Component Categories

### Active Components (67)

| Category | Count | Examples |
|----------|-------|----------|
| MCUs/SoCs | 10 | STM32F072, ATMEGA328PB, ESP32-S3, RV1106G3 |
| Power Management | 20 | LDOs, DC-DC converters, chargers, load switches |
| Transistors/MOSFETs | 10 | MMBT3904, DMG3415U, AO3401A |
| Interface ICs | 8 | MAX485, CH340N, TS3USB221, USBLC6 |
| Logic ICs | 6 | 74HC595, ULN2803A, 74HC4017D |
| LED/Motor Drivers | 4 | IS31FL3731, DRV8313, TLC5952 |
| Sensors | 2 | BMX055 IMU, ICS-43434 MEMS mic |
| Memory | 1 | W25N01GVZEIG NAND flash |
| WiFi Modules | 2 | ESP32-C3-MINI, RTL8189FTV |
| Connectors | 4 | USB-C THT, RJ12 jack |

### Passive Components (180)

| Category | Count |
|----------|-------|
| Resistors | 60 |
| Capacitors | 55 |
| Inductors | 13 |
| LEDs | 16 |
| Diodes/TVS | 10 |
| Connectors | 12 |
| Switches | 11 |
| Crystals | 3 |

## Regenerating the Database

After modifying `parts.csv`, run:

```bash
cd ~/Documents/KiCad/9.0/3rdparty/LCSC/database
python3 rebuild_db.py
```

The script:
- Backs up existing `parts.db` (timestamped)
- Creates fresh database from `parts.csv`
- Reports part count

Restart KiCad to see changes.

## Adding New Parts

1. Add row to `parts.csv` with all fields
2. Ensure Symbol exists in `Generics.kicad_sym` or `LCSC.kicad_sym`
3. Ensure Footprint exists in `LCSC.pretty/`
4. Optionally download datasheet to `datasheets/` (naming: `CLCSC_MPN.pdf`)
5. Optionally add 3D model to `3dmodels/` (STEP format)
6. Run `python3 rebuild_db.py`
7. Restart KiCad

### Using easyeda2kicad

For parts with EasyEDA/LCSC footprints:

```bash
pip install easyeda2kicad
easyeda2kicad --lcsc_id C12345 --symbol --footprint --3d --output ~/Documents/KiCad/9.0/3rdparty/LCSC/
```

Then merge generated files into existing libraries and update `parts.csv`.

## Gitignore

The following are not tracked (machine-specific or not distributed):

```
*.db           # SQLite databases (regenerate with rebuild_db.py)
*.bak          # Backup files
datasheets/    # PDF datasheets (download yourself)
```

## License

Personal use library. Component symbols derived from KiCad's Device library (CC-BY-SA 4.0).

## Links

- [JLCPCB Assembly Service](https://jlcpcb.com/smt-assembly)
- [LCSC Parts Search](https://www.lcsc.com/)
- [KiCad Database Libraries Documentation](https://docs.kicad.org/master/en/eeschema/eeschema.html#database-libraries)
- [easyeda2kicad](https://github.com/uPesy/easyeda2kicad.py)