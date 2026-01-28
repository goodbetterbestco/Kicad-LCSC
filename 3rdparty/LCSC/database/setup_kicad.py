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
8. Mouse/touchpad settings (auto-pan enabled, center-on-zoom disabled)
9. Schematic editor display options (dots grid, full crosshairs, Helvetica font)
10. Custom dark color theme for schematic editor (colors/user.json)
11. Project template defaults (40 mil text size for labels)

Run from any directory:
    python3 setup_kicad.py                      # Full setup
    python3 setup_kicad.py --patch-project .    # Patch current project only

Requirements:
    - macOS with Homebrew
    - KiCad 9.0 installed (launch once before running this script)
    - LCSC library cloned to ~/Documents/KiCad/9.0/

The JLCPCB_4Layer project template should be placed in:
    ~/Documents/KiCad/9.0/template/JLCPCB_4Layer/
"""

import argparse
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
EESCHEMA_JSON = KICAD_PREFS_DIR / "eeschema.json"
COLORS_DIR = KICAD_PREFS_DIR / "colors"

# Hotkey bindings for 4-layer workflow
# Set to "" to remove/clear a hotkey
HOTKEY_CHANGES = {
    "pcbnew.Control.layerTop": "1",       # F.Cu
    "pcbnew.Control.layerBottom": "2",    # B.Cu
    "pcbnew.Control.layerInner1": "3",    # In1.Cu (GND)
    "pcbnew.Control.layerInner2": "4",    # In2.Cu (Power)
    "common.Interactive.measureTool": "M",
    "common.Control.highContrastModeCycle": "",  # Remove H (conflicts with macOS hide)
}

# Library paths (absolute)
LCSC_DIR = KICAD_LIB_DIR / "3rdparty" / "LCSC"
GENERICS_SYM = KICAD_LIB_DIR / "symbols" / "Generics.kicad_sym"
LCSC_SYM = LCSC_DIR / "symbols" / "LCSC.kicad_sym"
PARTS_DBL = LCSC_DIR / "database" / "parts.kicad_dbl"
LCSC_FP = LCSC_DIR / "footprints" / "LCSC.pretty"
MODELS_DIR = KICAD_LIB_DIR / "3dmodels"
DATABASE_DIR = LCSC_DIR / "database"
TEMPLATE_DIR = KICAD_LIB_DIR / "template" / "JLCPCB_4Layer"

# Default schematic text size: 40 mil (KiCad 9 stores as mils directly)
DEFAULT_TEXT_SIZE = 40.0


def print_step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def print_ok(msg):
    print(f"  [OK] {msg}")


def print_warn(msg):
    print(f"  [WARN] {msg}")


def print_err(msg):
    print(f"  [ERROR] {msg}")


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
    
    # Ensure environment.vars exists (handle both missing key and null value)
    if "environment" not in config or config["environment"] is None:
        config["environment"] = {}
    if "vars" not in config["environment"] or config["environment"]["vars"] is None:
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
    """Apply power-user hotkey bindings and remove conflicting hotkeys."""
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
            
            if new_hotkey == "":
                # Remove this hotkey (clear binding)
                new_lines.append(action)  # No tab, no hotkey
                if old_hotkey != "(none)":
                    changes_made.append((action.split(".")[-1], old_hotkey, "(removed)"))
            else:
                new_lines.append(f"{action}\t{new_hotkey}")
                if old_hotkey != new_hotkey:
                    changes_made.append((action.split(".")[-1], old_hotkey, new_hotkey))
        else:
            new_lines.append(line)
    
    # Write
    HOTKEYS_FILE.write_text("\n".join(new_lines) + "\n")
    
    if changes_made:
        for action, old, new in changes_made:
            print_ok(f"{action}: {old} -> {new}")
    else:
        print_ok("Hotkeys already configured")
    
    return True


def configure_mouse_settings():
    """Configure mouse and touchpad pan/zoom settings in kicad_common.json."""
    print_step("Configuring mouse and touchpad settings")
    
    if not KICAD_COMMON.exists():
        print_err(f"kicad_common.json not found: {KICAD_COMMON}")
        return False
    
    try:
        with open(KICAD_COMMON, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print_err(f"Invalid JSON in kicad_common.json: {e}")
        return False
    
    # Ensure input section exists
    if "input" not in config or config["input"] is None:
        config["input"] = {}
    
    input_section = config["input"]
    changes = []
    
    # Uncheck "Center and warp cursor on zoom"
    if input_section.get("center_on_zoom") != False:
        input_section["center_on_zoom"] = False
        changes.append("center_on_zoom = false")
    
    # Check "Automatically pan while moving object"
    if input_section.get("auto_pan") != True:
        input_section["auto_pan"] = True
        changes.append("auto_pan = true")
    
    # Set "Auto Pan Speed" to 3 of 9 (KiCad uses integer 1-9 scale)
    auto_pan_speed = 3
    if input_section.get("auto_pan_acceleration") != auto_pan_speed:
        input_section["auto_pan_acceleration"] = auto_pan_speed
        changes.append(f"auto_pan_acceleration = {auto_pan_speed} (3 of 9)")
    
    if changes:
        with open(KICAD_COMMON, 'w') as f:
            json.dump(config, f, indent=2)
        for change in changes:
            print_ok(change)
    else:
        print_ok("Mouse settings already configured")
    
    return True


def configure_eeschema_settings():
    """Configure schematic editor display options in eeschema.json."""
    print_step("Configuring schematic editor settings")
    
    # Load existing config or create new
    if EESCHEMA_JSON.exists():
        try:
            with open(EESCHEMA_JSON, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print_warn(f"Invalid JSON in eeschema.json, creating new: {e}")
            config = {}
    else:
        config = {}
    
    changes = []
    
    # Ensure nested structures exist
    if "appearance" not in config or config["appearance"] is None:
        config["appearance"] = {}
    if "annotation" not in config or config["annotation"] is None:
        config["annotation"] = {}
    if "window" not in config or config["window"] is None:
        config["window"] = {}
    if "grid" not in config["window"] or config["window"]["grid"] is None:
        config["window"]["grid"] = {}
    if "cursor" not in config["window"] or config["window"]["cursor"] is None:
        config["window"]["cursor"] = {}
    
    appearance = config["appearance"]
    annotation = config["annotation"]
    window_grid = config["window"]["grid"]
    window_cursor = config["window"]["cursor"]
    
    # Grid Display: dots (style 0 = dots, 1 = lines, 2 = small crosses)
    if window_grid.get("style") != 0:
        window_grid["style"] = 0
        changes.append("grid style = dots")
    
    # Cursor: select full window crosshairs
    if window_cursor.get("fullscreen_cursor") != True:
        window_cursor["fullscreen_cursor"] = True
        changes.append("fullscreen_cursor = true")
    
    # Default font: Helvetica
    if appearance.get("default_font") != "Helvetica":
        appearance["default_font"] = "Helvetica"
        changes.append("default_font = Helvetica")
    
    # Annotation: Use first free number (method 0)
    if annotation.get("method") != 0:
        annotation["method"] = 0
        changes.append("annotation method = first free number")
    
    # Annotation: start number 0 (sort_order 0 means start from 0)
    if annotation.get("sort_order") != 0:
        annotation["sort_order"] = 0
        changes.append("annotation sort_order = 0")
    
    # Color theme: use "user" theme (colors/user.json)
    if appearance.get("color_theme") != "user":
        appearance["color_theme"] = "user"
        changes.append("color_theme = user")
    
    if changes:
        with open(EESCHEMA_JSON, 'w') as f:
            json.dump(config, f, indent=2)
        for change in changes:
            print_ok(change)
    else:
        print_ok("Schematic editor settings already configured")
    
    return True


def configure_color_theme():
    """Create or update user color theme for schematic editor."""
    print_step("Configuring schematic color theme")
    
    # Create colors directory if needed
    COLORS_DIR.mkdir(parents=True, exist_ok=True)
    
    theme_file = COLORS_DIR / "user.json"
    
    # Default color for all unspecified items (white)
    default_color = "rgb(255, 255, 255)"
    
    # Custom schematic colors as specified
    # KiCad uses "rgb(r, g, b)" format or "rgba(r, g, b, a)" for colors
    schematic_colors = {
        "anchor": default_color,
        "aux_items": default_color,
        "background": "rgb(0, 0, 0)",              # #000000FF
        "brightened": "rgb(72, 72, 72)",             # #484848FF (Highlighted items)
        "bus": default_color,
        "bus_junction": default_color,
        "component_body": "rgb(32, 0, 0)",         # #200000FF (Symbol body fills)
        "component_outline": "rgb(194, 0, 0)",     # #C20000FF (Symbol body outlines)
        "cursor": "rgb(0, 255, 0)",                # #00FF00FF
        "dnp_marker": default_color,
        "erc_error": default_color,
        "erc_exclusion": default_color,
        "erc_warning": default_color,
        "excluded_from_sim": default_color,
        "fields": default_color,
        "grid": "rgb(72, 72, 72)",                 # #484848FF
        "grid_axes": default_color,
        "hidden": default_color,
        "hovered": default_color,
        "junction": "rgb(0, 132, 0)",              # #008400FF (Junctions)
        "label_global": "rgb(255, 255, 0)",        # #FFFF00FF (Labels - global)
        "label_hier": "rgb(255, 255, 0)",          # #FFFF00FF (Labels - hierarchical)
        "label_local": "rgb(255, 255, 0)",         # #FFFF00FF (Labels - local)
        "netclass_flag": default_color,
        "no_connect": default_color,
        "note": "rgb(0, 255, 0)",                  # #00FF00FF (Schematic text & graphics)
        "note_background": "rgba(0, 0, 0, 0.000)", # Transparent
        "op_currents": default_color,
        "op_voltages": default_color,
        "override_item_colors": True,
        "page_limits": default_color,
        "pin": "rgb(194, 0, 0)",                   # #C20000FF (Pins)
        "pin_name": "rgb(194, 194, 194)",          # #C2C2C2FF (Pin names)
        "pin_number": "rgb(194, 194, 194)",        # #C2C2C2FF (Pin numbers)
        "private_note": default_color,
        "reference": "rgb(0, 255, 255)",           # #00FFFFFF (Symbol references)
        "rule_area": "rgb(194, 0, 0)",             # #C20000FF (Rule areas)
        "shadow": "rgb(72, 72, 72)",               # #484848FF (Selection highlight)
        "sheet": "rgb(255, 0, 0)",                 # #FF0000FF (Sheet borders)
        "sheet_background": "rgb(0, 0, 0)",        # #000000FF (Sheet backgrounds)
        "sheet_fields": default_color,
        "sheet_filename": default_color,
        "sheet_label": default_color,
        "sheet_name": default_color,
        "value": "rgb(0, 255, 255)",               # #00FFFFFF (Symbol values)
        "wire": "rgb(0, 132, 0)",                  # #008400FF (Wires)
        "worksheet": default_color
    }
    
    # Load existing theme or create new
    if theme_file.exists():
        try:
            with open(theme_file, 'r') as f:
                theme = json.load(f)
        except json.JSONDecodeError:
            theme = {}
    else:
        theme = {}
    
    # Ensure structure exists
    if "meta" not in theme:
        theme["meta"] = {"name": "User", "version": 5}
    if "schematic" not in theme:
        theme["schematic"] = {}
    
    # Update schematic colors
    changes = []
    for key, value in schematic_colors.items():
        if theme["schematic"].get(key) != value:
            theme["schematic"][key] = value
            if key in ["background", "cursor", "wire", "junction", "reference", "value", 
                       "label_global", "label_hier", "label_local", "component_body", 
                       "component_outline", "pin", "sheet", "brightened", "shadow"]:
                changes.append(key)
    
    # Write theme file
    with open(theme_file, 'w') as f:
        json.dump(theme, f, indent=2)
    
    if changes:
        print_ok(f"Updated color theme: {theme_file.name}")
        print_ok("Background: black")
        print_ok("Cursor/Text: green")
        print_ok("Wires/Junctions: dark green")
        print_ok("Symbols: red outlines, dark red fills")
        print_ok("References/Values: cyan")
        print_ok("Labels: yellow")
        print_ok("Selection/Highlight: dark gray (#484848)")
    else:
        print_ok(f"Color theme already configured: {theme_file.name}")
    
    return True


def patch_project_file(project_path):
    """Patch a .kicad_pro file to set default text size to 40 mil.
    
    Args:
        project_path: Path to .kicad_pro file or directory containing one
        
    Returns:
        True on success, False on error
    """
    project_path = Path(project_path).expanduser().resolve()
    
    # If directory given, find .kicad_pro file
    if project_path.is_dir():
        pro_files = list(project_path.glob("*.kicad_pro"))
        if not pro_files:
            print_err(f"No .kicad_pro file found in: {project_path}")
            return False
        if len(pro_files) > 1:
            print_warn(f"Multiple .kicad_pro files found, using: {pro_files[0].name}")
        project_path = pro_files[0]
    
    if not project_path.exists():
        print_err(f"Project file not found: {project_path}")
        return False
    
    if project_path.suffix != ".kicad_pro":
        print_err(f"Not a .kicad_pro file: {project_path}")
        return False
    
    print_step(f"Patching project: {project_path.name}")
    
    try:
        with open(project_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print_err(f"Invalid JSON: {e}")
        return False
    
    # Ensure schematic.drawing structure exists
    if "schematic" not in config or config["schematic"] is None:
        config["schematic"] = {}
    if "drawing" not in config["schematic"] or config["schematic"]["drawing"] is None:
        config["schematic"]["drawing"] = {}
    
    drawing = config["schematic"]["drawing"]
    old_size = drawing.get("default_text_size")
    
    if old_size == DEFAULT_TEXT_SIZE:
        print_ok(f"Already set to {DEFAULT_TEXT_SIZE:.0f} mil")
        return True
    
    drawing["default_text_size"] = DEFAULT_TEXT_SIZE
    
    with open(project_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    if old_size:
        print_ok(f"Changed default_text_size: {old_size} → {DEFAULT_TEXT_SIZE:.0f} mil")
    else:
        print_ok(f"Set default_text_size: {DEFAULT_TEXT_SIZE:.0f} mil")
    
    return True


def configure_project_template():
    """Configure default schematic settings in the JLCPCB_4Layer project template."""
    print_step("Configuring project template defaults")
    
    template_pro = TEMPLATE_DIR / "JLCPCB_4Layer.kicad_pro"
    
    if not template_pro.exists():
        print_warn(f"Project template not found: {template_pro}")
        print_warn("Skipping template configuration")
        return True  # Non-fatal
    
    try:
        with open(template_pro, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print_err(f"Invalid JSON in template: {e}")
        return False
    
    changes = []
    
    # Ensure schematic.drawing structure exists
    if "schematic" not in config or config["schematic"] is None:
        config["schematic"] = {}
    if "drawing" not in config["schematic"] or config["schematic"]["drawing"] is None:
        config["schematic"]["drawing"] = {}
    
    drawing = config["schematic"]["drawing"]
    
    # Default text size: 40 mil (affects labels, text, and text boxes)
    if drawing.get("default_text_size") != DEFAULT_TEXT_SIZE:
        drawing["default_text_size"] = DEFAULT_TEXT_SIZE
        changes.append(f"default_text_size = {DEFAULT_TEXT_SIZE:.0f} mil")
    
    if changes:
        with open(template_pro, 'w') as f:
            json.dump(config, f, indent=2)
        for change in changes:
            print_ok(change)
    else:
        print_ok("Project template already configured")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="KiCad LCSC Library Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 setup_kicad.py                    # Full setup
  python3 setup_kicad.py --patch-project .  # Patch current directory's project
  python3 setup_kicad.py --patch-project ~/Projects/flipdots/hardware/flipdots
"""
    )
    parser.add_argument(
        "--patch-project", "-p",
        metavar="PATH",
        help="Patch an existing project's .kicad_pro to use 40 mil text (skips full setup)"
    )
    args = parser.parse_args()
    
    # If --patch-project specified, just patch and exit
    if args.patch_project:
        success = patch_project_file(args.patch_project)
        return 0 if success else 1
    
    print("\n" + "="*60)
    print("  KiCad LCSC Library Setup")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nSetup failed: missing prerequisites")
        return 1
    
    # Check/install ODBC
    if not check_odbc_installed():
        response = input("\nInstall ODBC drivers via Homebrew? [Y/n]: ").strip().lower()
        if response in ('', 'y', 'yes'):
            if not install_odbc():
                print("\nSetup failed: could not install ODBC")
                return 1
        else:
            print("\nSetup cancelled: ODBC drivers required")
            return 1
    
    # Configure ODBC
    if not configure_odbcinst():
        print("\nSetup failed: could not configure ODBC")
        return 1
    
    # Rebuild database
    if not rebuild_database():
        print("\nSetup failed: could not rebuild database")
        return 1
    
    # Configure KiCad
    if not configure_path_variables():
        print("\nSetup failed: could not configure path variables")
        return 1
    
    if not configure_symbol_libraries():
        print("\nSetup failed: could not configure symbol libraries")
        return 1
    
    if not configure_footprint_libraries():
        print("\nSetup failed: could not configure footprint libraries")
        return 1
    
    if not configure_hotkeys():
        print("\nSetup failed: could not configure hotkeys")
        return 1
    
    if not configure_mouse_settings():
        print("\nSetup failed: could not configure mouse settings")
        return 1
    
    if not configure_eeschema_settings():
        print("\nSetup failed: could not configure schematic editor settings")
        return 1
    
    if not configure_color_theme():
        print("\nSetup failed: could not configure color theme")
        return 1
    
    if not configure_project_template():
        print("\nSetup failed: could not configure project template")
        return 1
    
    print("\n" + "="*60)
    print("  Setup complete!")
    print("="*60)
    print("\nPlease restart KiCad for changes to take effect.")
    print("\nConfigured:")
    print("  Libraries:")
    print("    - Generics - Generic symbols (R, C, L, D, LED, etc.)")
    print("    - LCSC - Atomic symbols with pre-filled fields")
    print("    - parts - Searchable database library")
    print("    - LCSC (footprints) - Custom footprints")
    print("  Hotkeys:")
    print("    - 1/2/3/4 - Layer switching (F.Cu/B.Cu/In1/In2)")
    print("    - M - Measure tool")
    print("    - H - Removed (was High Contrast Mode Cycle)")
    print("  Mouse/Touchpad:")
    print("    - Auto-pan enabled, speed 3/9")
    print("    - Center on zoom disabled")
    print("  Schematic Editor:")
    print("    - Grid: dots")
    print("    - Cursor: full window crosshairs")
    print("    - Font: Helvetica")
    print("    - Annotation: first free number after 0")
    print("    - Theme: user (black bg, green/red/cyan, dark gray selection)")
    print("\nTemplate (JLCPCB_4Layer):")
    print("    - Default text size: 40 mil (labels, text)")
    print("    - Available in File -> New Project from Template")
    print("\nTo patch an existing project:")
    print("    python3 setup_kicad.py --patch-project /path/to/project")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
