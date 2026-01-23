#!/usr/bin/env python3
"""
KiCad LCSC Library Setup Script

This script configures a fresh KiCad 9.0 installation to use the LCSC parts library.
It handles:
1. ODBC driver installation check
2. ~/.odbcinst.ini configuration
3. Rebuilding parts.db from parts.csv
4. Configuring KiCad path variables
5. Adding symbol libraries (Generics, LCSC, parts database)
6. Adding footprint library (LCSC.pretty)
7. Configuring power-user hotkeys (1-4 layer switching, M for measure)

Run from any directory:
    python3 setup_kicad.py

Requirements:
    - macOS with Homebrew
    - KiCad 9.0 installed (launch once before running this script)
    - LCSC library cloned to ~/Documents/KiCad/9.0/

The JLCPCB_4Layer project template should be placed in:
    ~/Documents/KiCad/9.0/template/JLCPCB_4Layer/
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Paths
HOME = Path.home()
KICAD_LIB_DIR = HOME / "Documents" / "KiCad" / "9.0"
KICAD_PREFS_DIR = HOME / "Library" / "Preferences" / "kicad" / "9.0"
ODBCINST_PATH = HOME / ".odbcinst.ini"

# KiCad config files
SYM_LIB_TABLE = KICAD_PREFS_DIR / "sym-lib-table"
FP_LIB_TABLE = KICAD_PREFS_DIR / "fp-lib-table"
KICAD_COMMON = KICAD_PREFS_DIR / "kicad_common.json"
HOTKEYS_FILE = KICAD_PREFS_DIR / "user.hotkeys"

# Hotkey bindings for 4-layer workflow
HOTKEY_CHANGES = {
    "pcbnew.Control.layerTop": "1",       # F.Cu
    "pcbnew.Control.layerBottom": "2",    # B.Cu
    "pcbnew.Control.layerInner1": "3",    # In1.Cu (GND)
    "pcbnew.Control.layerInner2": "4",    # In2.Cu (Power)
    "common.Interactive.measureTool": "M",
}

# Library paths (absolute)
LCSC_DIR = KICAD_LIB_DIR / "3rdparty" / "LCSC"
GENERICS_SYM = KICAD_LIB_DIR / "symbols" / "Generics.kicad_sym"
LCSC_SYM = LCSC_DIR / "symbols" / "LCSC.kicad_sym"
PARTS_DBL = LCSC_DIR / "database" / "parts.kicad_dbl"
LCSC_FP = LCSC_DIR / "footprints" / "LCSC.pretty"
MODELS_DIR = KICAD_LIB_DIR / "3dmodels"
DATABASE_DIR = LCSC_DIR / "database"


def print_step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def print_ok(msg):
    print(f"  ✓ {msg}")


def print_warn(msg):
    print(f"  ⚠ {msg}")


def print_err(msg):
    print(f"  ✗ {msg}")


def check_prerequisites():
    """Verify required files and directories exist."""
    print_step("Checking prerequisites")
    
    errors = []
    
    if not KICAD_LIB_DIR.exists():
        errors.append(f"KiCad library directory not found: {KICAD_LIB_DIR}")
    
    if not KICAD_PREFS_DIR.exists():
        errors.append(f"KiCad preferences directory not found: {KICAD_PREFS_DIR}")
        errors.append("Have you launched KiCad 9.0 at least once?")
    
    if not GENERICS_SYM.exists():
        errors.append(f"Generics symbol library not found: {GENERICS_SYM}")
    
    if not LCSC_SYM.exists():
        errors.append(f"LCSC symbol library not found: {LCSC_SYM}")
    
    if not PARTS_DBL.exists():
        errors.append(f"Parts database config not found: {PARTS_DBL}")
    
    if not LCSC_FP.exists():
        errors.append(f"LCSC footprint library not found: {LCSC_FP}")
    
    parts_csv = DATABASE_DIR / "parts.csv"
    if not parts_csv.exists():
        errors.append(f"Parts CSV not found: {parts_csv}")
    
    if errors:
        for e in errors:
            print_err(e)
        return False
    
    print_ok("All required files found")
    return True


def check_odbc_installed():
    """Check if unixodbc and sqliteodbc are installed via Homebrew."""
    print_step("Checking ODBC installation")
    
    try:
        result = subprocess.run(
            ["brew", "list", "unixodbc"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_warn("unixodbc not installed")
            return False
        print_ok("unixodbc installed")
        
        result = subprocess.run(
            ["brew", "list", "sqliteodbc"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print_warn("sqliteodbc not installed")
            return False
        print_ok("sqliteodbc installed")
        
        return True
    except FileNotFoundError:
        print_err("Homebrew not found. Please install Homebrew first.")
        return False


def install_odbc():
    """Install ODBC drivers via Homebrew."""
    print_step("Installing ODBC drivers")
    
    try:
        print("  Installing unixodbc...")
        subprocess.run(["brew", "install", "unixodbc"], check=True)
        print_ok("unixodbc installed")
        
        print("  Installing sqliteodbc...")
        subprocess.run(["brew", "install", "sqliteodbc"], check=True)
        print_ok("sqliteodbc installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print_err(f"Failed to install ODBC: {e}")
        return False


def configure_odbcinst():
    """Create or update ~/.odbcinst.ini for SQLite3 ODBC driver."""
    print_step("Configuring ODBC driver")
    
    # Determine driver path based on architecture
    if Path("/opt/homebrew/lib/libsqlite3odbc.dylib").exists():
        driver_path = "/opt/homebrew/lib/libsqlite3odbc.dylib"
    elif Path("/usr/local/lib/libsqlite3odbc.dylib").exists():
        driver_path = "/usr/local/lib/libsqlite3odbc.dylib"
    else:
        print_err("Could not find libsqlite3odbc.dylib")
        print_warn("Checked /opt/homebrew/lib/ and /usr/local/lib/")
        return False
    
    odbcinst_content = f"""[SQLite3]
Description=SQLite3 ODBC Driver
Driver={driver_path}
Setup={driver_path}
UsageCount=1
"""
    
    # Check if already configured correctly
    if ODBCINST_PATH.exists():
        existing = ODBCINST_PATH.read_text()
        if "[SQLite3]" in existing and driver_path in existing:
            print_ok(f"ODBC already configured in {ODBCINST_PATH}")
            return True
    
    # Write config
    ODBCINST_PATH.write_text(odbcinst_content)
    print_ok(f"Created {ODBCINST_PATH}")
    print(f"  Driver: {driver_path}")
    
    return True


def rebuild_database():
    """Run rebuild_db.py to create parts.db from parts.csv."""
    print_step("Rebuilding parts database")
    
    rebuild_script = DATABASE_DIR / "rebuild_db.py"
    if not rebuild_script.exists():
        print_err(f"rebuild_db.py not found: {rebuild_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(rebuild_script)],
            cwd=str(DATABASE_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_err("Failed to rebuild database")
            print(result.stderr)
            return False
        
        # Show output
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                print(f"  {line}")
        
        return True
    except Exception as e:
        print_err(f"Error running rebuild_db.py: {e}")
        return False


def configure_path_variables():
    """Add required path variables to kicad_common.json."""
    print_step("Configuring KiCad path variables")
    
    if not KICAD_COMMON.exists():
        print_err(f"kicad_common.json not found: {KICAD_COMMON}")
        return False
    
    try:
        with open(KICAD_COMMON, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print_err(f"Invalid JSON in kicad_common.json: {e}")
        return False
    
    # Ensure environment.vars exists
    if "environment" not in config:
        config["environment"] = {}
    if "vars" not in config["environment"]:
        config["environment"]["vars"] = {}
    
    vars_section = config["environment"]["vars"]
    
    # Add/update path variables
    changes = []
    
    # KICAD9_3RD_PARTY - points to 3rdparty folder
    new_3rdparty = str(KICAD_LIB_DIR / "3rdparty")
    if vars_section.get("KICAD9_3RD_PARTY") != new_3rdparty:
        vars_section["KICAD9_3RD_PARTY"] = new_3rdparty
        changes.append(f"KICAD9_3RD_PARTY = {new_3rdparty}")
    
    # KICAD9_3DMODEL_DIR - points to 3dmodels folder
    new_3dmodel = str(MODELS_DIR)
    if vars_section.get("KICAD9_3DMODEL_DIR") != new_3dmodel:
        vars_section["KICAD9_3DMODEL_DIR"] = new_3dmodel
        changes.append(f"KICAD9_3DMODEL_DIR = {new_3dmodel}")
    
    if changes:
        with open(KICAD_COMMON, 'w') as f:
            json.dump(config, f, indent=2)
        
        for change in changes:
            print_ok(change)
    else:
        print_ok("Path variables already configured")
    
    return True


def configure_symbol_libraries():
    """Configure sym-lib-table with Generics, LCSC, and parts database."""
    print_step("Configuring symbol libraries")
    
    # Use absolute paths for reliability
    # Generics is visible (power symbols, mounting holes, etc.)
    # LCSC is hidden - only referenced by the parts database
    sym_lib_content = f"""(sym_lib_table
  (version 7)
  (lib (name "Generics")(type "KiCad")(uri "{GENERICS_SYM}")(options "")(descr "Generic symbols and power"))
  (lib (name "LCSC")(type "KiCad")(uri "{LCSC_SYM}")(options "")(descr "LCSC atomic symbols")(hidden))
  (lib (name "parts")(type "Database")(uri "{PARTS_DBL}")(options "")(descr "LCSC parts database"))
)
"""
    
    SYM_LIB_TABLE.write_text(sym_lib_content)
    print_ok(f"Generics: {GENERICS_SYM}")
    print_ok(f"LCSC: {LCSC_SYM} (hidden)")
    print_ok(f"parts: {PARTS_DBL}")
    
    return True


def configure_footprint_libraries():
    """Configure fp-lib-table with LCSC footprints."""
    print_step("Configuring footprint libraries")
    
    # Use absolute path
    fp_lib_content = f"""(fp_lib_table
  (version 7)
  (lib (name "LCSC")(type "KiCad")(uri "{LCSC_FP}")(options "")(descr "LCSC footprints"))
)
"""
    
    FP_LIB_TABLE.write_text(fp_lib_content)
    print_ok(f"LCSC: {LCSC_FP}")
    
    return True


def configure_hotkeys():
    """Apply power-user hotkey bindings."""
    print_step("Configuring hotkeys")
    
    if not HOTKEYS_FILE.exists():
        print_warn(f"Hotkeys file not found: {HOTKEYS_FILE}")
        print_warn("Skipping hotkey configuration (launch KiCad once first)")
        return True  # Non-fatal
    
    # Read and parse
    lines = HOTKEYS_FILE.read_text().splitlines()
    new_lines = []
    changes_made = []
    
    for line in lines:
        if "\t" in line:
            action, hotkey = line.split("\t", 1)
        else:
            action = line
            hotkey = ""
        
        if action in HOTKEY_CHANGES:
            old_hotkey = hotkey if hotkey else "(none)"
            new_hotkey = HOTKEY_CHANGES[action]
            new_lines.append(f"{action}\t{new_hotkey}")
            if old_hotkey != new_hotkey:
                changes_made.append((action.split(".")[-1], old_hotkey, new_hotkey))
        else:
            new_lines.append(line)
    
    # Write
    HOTKEYS_FILE.write_text("\n".join(new_lines) + "\n")
    
    if changes_made:
        for action, old, new in changes_made:
            print_ok(f"{action}: {old} → {new}")
    else:
        print_ok("Hotkeys already configured")
    
    return True


def main():
    print("\n" + "="*60)
    print("  KiCad LCSC Library Setup")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Setup failed: missing prerequisites")
        return 1
    
    # Check/install ODBC
    if not check_odbc_installed():
        response = input("\nInstall ODBC drivers via Homebrew? [Y/n]: ").strip().lower()
        if response in ('', 'y', 'yes'):
            if not install_odbc():
                print("\n❌ Setup failed: could not install ODBC")
                return 1
        else:
            print("\n❌ Setup cancelled: ODBC drivers required")
            return 1
    
    # Configure ODBC
    if not configure_odbcinst():
        print("\n❌ Setup failed: could not configure ODBC")
        return 1
    
    # Rebuild database
    if not rebuild_database():
        print("\n❌ Setup failed: could not rebuild database")
        return 1
    
    # Configure KiCad
    if not configure_path_variables():
        print("\n❌ Setup failed: could not configure path variables")
        return 1
    
    if not configure_symbol_libraries():
        print("\n❌ Setup failed: could not configure symbol libraries")
        return 1
    
    if not configure_footprint_libraries():
        print("\n❌ Setup failed: could not configure footprint libraries")
        return 1
    
    if not configure_hotkeys():
        print("\n❌ Setup failed: could not configure hotkeys")
        return 1
    
    print("\n" + "="*60)
    print("  ✓ Setup complete!")
    print("="*60)
    print("\nPlease restart KiCad for changes to take effect.")
    print("\nConfigured:")
    print("  Libraries:")
    print("    • Generics - Generic symbols (R, C, L, D, LED, etc.)")
    print("    • LCSC - Atomic symbols with pre-filled fields")
    print("    • parts - Searchable database library")
    print("    • LCSC (footprints) - Custom footprints")
    print("  Hotkeys:")
    print("    • 1/2/3/4 - Layer switching (F.Cu/B.Cu/In1/In2)")
    print("    • M - Measure tool")
    print("\nTemplate:")
    print("  JLCPCB_4Layer template available in File → New Project from Template")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
