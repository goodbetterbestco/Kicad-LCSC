#!/usr/bin/env python3
"""
KiCad Symbol Pin to Footprint Pad Verification Tool

Verifies that every symbol's pin numbers have matching pad numbers in the
assigned footprint. Reports mismatches to catch errors during symbol editing.

Usage:
    python verify_pins_to_pads.py [options]

Options:
    --symbols PATH      Path to symbol library file(s), comma-separated
    --footprints PATH   Path to footprint library directory (.pretty folder)
    --verbose           Show detailed per-symbol results
    --json              Output results as JSON
"""

import argparse
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Symbol:
    """Represents a KiCad symbol with its pins and footprint reference."""
    name: str
    footprint: str
    pin_numbers: set = field(default_factory=set)
    pin_occurrences: dict = field(default_factory=dict)  # pin -> count (for duplicate detection)
    lcsc: str = ""
    
    def __repr__(self):
        return f"Symbol({self.name}, {len(self.pin_numbers)} pins → {self.footprint})"


@dataclass
class Footprint:
    """Represents a KiCad footprint with its pads."""
    name: str
    pad_numbers: set = field(default_factory=set)
    
    def __repr__(self):
        return f"Footprint({self.name}, {len(self.pad_numbers)} pads)"


@dataclass
class VerificationResult:
    """Result of comparing a symbol against its footprint."""
    symbol_name: str
    footprint_name: str
    symbol_pin_count: int
    footprint_pad_count: int
    pins_without_pads: set
    pads_without_pins: set
    footprint_found: bool = True
    duplicate_pins: dict = field(default_factory=dict)  # pin -> count
    
    @property
    def matches(self) -> bool:
        return self.footprint_found and not self.pins_without_pads and not self.pads_without_pins
    
    @property
    def has_warnings(self) -> bool:
        return bool(self.duplicate_pins)
    
    @property
    def status(self) -> str:
        if not self.footprint_found:
            return "FOOTPRINT_NOT_FOUND"
        elif self.matches:
            return "OK"
        else:
            return "MISMATCH"


def parse_symbol_library(filepath: Path) -> list[Symbol]:
    """Parse a KiCad symbol library file and extract symbols with their pins."""
    symbols = []
    content = filepath.read_text(encoding='utf-8')
    
    # Match top-level symbols (not sub-symbols like "SymbolName_0_1")
    # Pattern: (symbol "NAME" at start, where NAME doesn't contain underscore followed by digits
    symbol_pattern = re.compile(
        r'\(symbol\s+"([^"]+)"\s*\n'
        r'(?:.*?\n)*?'  # Non-greedy match of any lines
        r'(?=\s*\(symbol\s+"[^"]+"|$)',  # Lookahead for next symbol or end
        re.MULTILINE
    )
    
    # Split by top-level symbols more reliably
    lines = content.split('\n')
    current_symbol = None
    current_symbol_content = []
    depth = 0
    in_symbol = False
    
    for line in lines:
        # Track parenthesis depth
        depth += line.count('(') - line.count(')')
        
        # Check for new top-level symbol (after the library header)
        match = re.match(r'\s*\(symbol\s+"([^"]+)"', line)
        if match:
            name = match.group(1)
            # Skip sub-symbols (contain _0_1, _1_1, etc.)
            if not re.search(r'_\d+_\d+$', name):
                # Save previous symbol if exists
                if current_symbol:
                    symbols.append(parse_symbol_block(current_symbol, current_symbol_content))
                current_symbol = name
                current_symbol_content = [line]
                in_symbol = True
                continue
        
        if in_symbol:
            current_symbol_content.append(line)
    
    # Don't forget the last symbol
    if current_symbol:
        symbols.append(parse_symbol_block(current_symbol, current_symbol_content))
    
    return symbols


def parse_symbol_block(name: str, lines: list[str]) -> Symbol:
    """Parse a symbol block to extract footprint and pin numbers."""
    content = '\n'.join(lines)
    symbol = Symbol(name=name, footprint="")
    
    # Extract footprint property
    fp_match = re.search(r'\(property\s+"Footprint"\s+"([^"]*)"', content)
    if fp_match:
        symbol.footprint = fp_match.group(1)
    
    # Extract LCSC property
    lcsc_match = re.search(r'\(property\s+"(?:LCSC|LCSC Part)"\s+"([^"]*)"', content)
    if lcsc_match:
        symbol.lcsc = lcsc_match.group(1)
    
    # Extract all pin numbers and track occurrences
    # Pattern matches: (number "X" where X is the pin number
    pin_pattern = re.compile(r'\(number\s+"([^"]+)"')
    for match in pin_pattern.finditer(content):
        pin = match.group(1)
        symbol.pin_numbers.add(pin)
        symbol.pin_occurrences[pin] = symbol.pin_occurrences.get(pin, 0) + 1
    
    return symbol


def parse_footprint_library(dirpath: Path) -> dict[str, Footprint]:
    """Parse all footprint files in a .pretty directory."""
    footprints = {}
    
    if not dirpath.exists():
        print(f"Warning: Footprint directory not found: {dirpath}", file=sys.stderr)
        return footprints
    
    for fp_file in dirpath.glob("*.kicad_mod"):
        footprint = parse_footprint_file(fp_file)
        if footprint:
            footprints[footprint.name] = footprint
    
    return footprints


def parse_footprint_file(filepath: Path) -> Optional[Footprint]:
    """Parse a single footprint file to extract pad numbers."""
    content = filepath.read_text(encoding='utf-8')
    
    # Use filename (without extension) as the footprint name
    # This is what KiCad uses for resolution: LCSC:U_smd_LQFP_48P -> U_smd_LQFP_48P.kicad_mod
    footprint = Footprint(name=filepath.stem)
    
    # Extract all pad numbers
    # Pattern: (pad "X" or (pad X where X is the pad number/name
    pad_pattern = re.compile(r'\(pad\s+"?([^"\s\)]+)"?')
    for match in pad_pattern.finditer(content):
        footprint.pad_numbers.add(match.group(1))
    
    return footprint


def resolve_footprint_reference(fp_ref: str, footprint_libs: dict[str, dict[str, Footprint]]) -> Optional[Footprint]:
    """Resolve a footprint reference like 'LCSC:U_smd_LQFP_48P' to actual footprint."""
    if ':' in fp_ref:
        lib_name, fp_name = fp_ref.split(':', 1)
    else:
        lib_name = None
        fp_name = fp_ref
    
    # Search in the appropriate library or all libraries
    if lib_name and lib_name in footprint_libs:
        return footprint_libs[lib_name].get(fp_name)
    else:
        # Search all libraries
        for lib in footprint_libs.values():
            if fp_name in lib:
                return lib[fp_name]
    
    return None


def verify_symbol(symbol: Symbol, footprint_libs: dict[str, dict[str, Footprint]]) -> VerificationResult:
    """Verify a symbol's pins match its footprint's pads."""
    footprint = resolve_footprint_reference(symbol.footprint, footprint_libs)
    
    # Find duplicate pins (expected for power pins like VCC, GND)
    duplicates = {pin: count for pin, count in symbol.pin_occurrences.items() if count > 1}
    
    if footprint is None:
        return VerificationResult(
            symbol_name=symbol.name,
            footprint_name=symbol.footprint,
            symbol_pin_count=len(symbol.pin_numbers),
            footprint_pad_count=0,
            pins_without_pads=symbol.pin_numbers.copy(),
            pads_without_pins=set(),
            footprint_found=False,
            duplicate_pins=duplicates
        )
    
    pins_without_pads = symbol.pin_numbers - footprint.pad_numbers
    pads_without_pins = footprint.pad_numbers - symbol.pin_numbers
    
    return VerificationResult(
        symbol_name=symbol.name,
        footprint_name=symbol.footprint,
        symbol_pin_count=len(symbol.pin_numbers),
        footprint_pad_count=len(footprint.pad_numbers),
        pins_without_pads=pins_without_pads,
        pads_without_pins=pads_without_pins,
        footprint_found=True,
        duplicate_pins=duplicates
    )


def format_result(result: VerificationResult, verbose: bool = False) -> str:
    """Format a verification result for display."""
    if result.status == "OK":
        line = f"✓ {result.symbol_name} ({result.symbol_pin_count} pins) → {result.footprint_name}"
        if result.duplicate_pins and verbose:
            dups = ', '.join(f"{p}×{c}" for p, c in sorted(result.duplicate_pins.items()))
            line += f"\n    (repeated pin numbers: {dups})"
        return line
    elif result.status == "FOOTPRINT_NOT_FOUND":
        return f"? {result.symbol_name} → {result.footprint_name} (footprint not found)"
    else:
        lines = [f"✗ {result.symbol_name} ({result.symbol_pin_count} pins) → {result.footprint_name} ({result.footprint_pad_count} pads)"]
        if result.pins_without_pads:
            sorted_pins = sorted(result.pins_without_pads, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
            lines.append(f"    Pins without matching pads: {', '.join(sorted_pins)}")
        if result.pads_without_pins:
            sorted_pads = sorted(result.pads_without_pins, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
            lines.append(f"    Pads without matching pins: {', '.join(sorted_pads)}")
        if result.duplicate_pins:
            dups = ', '.join(f"{p}×{c}" for p, c in sorted(result.duplicate_pins.items()))
            lines.append(f"    (repeated pin numbers: {dups})")
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Verify KiCad symbol pins match footprint pads"
    )
    parser.add_argument(
        '--symbols', '-s',
        required=True,
        help='Path to symbol library file(s), comma-separated'
    )
    parser.add_argument(
        '--footprints', '-f',
        required=True,
        help='Path to footprint library directory (.pretty folder)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show all results including matches'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Parse symbol libraries
    symbol_files = [Path(p.strip()) for p in args.symbols.split(',')]
    all_symbols = []
    for sym_file in symbol_files:
        if not sym_file.exists():
            print(f"Error: Symbol file not found: {sym_file}", file=sys.stderr)
            sys.exit(1)
        symbols = parse_symbol_library(sym_file)
        print(f"Loaded {len(symbols)} symbols from {sym_file.name}", file=sys.stderr)
        all_symbols.extend(symbols)
    
    # Parse footprint libraries
    footprint_dirs = [Path(p.strip()) for p in args.footprints.split(',')]
    footprint_libs = {}
    for fp_dir in footprint_dirs:
        if not fp_dir.exists():
            print(f"Error: Footprint directory not found: {fp_dir}", file=sys.stderr)
            sys.exit(1)
        # Use directory name (minus .pretty) as library name
        lib_name = fp_dir.stem.replace('.pretty', '')
        if fp_dir.suffix == '.pretty':
            lib_name = fp_dir.stem
        else:
            # If it's a parent dir, look for .pretty subdirs
            for subdir in fp_dir.glob("*.pretty"):
                lib_name = subdir.stem
                footprint_libs[lib_name] = parse_footprint_library(subdir)
                print(f"Loaded {len(footprint_libs[lib_name])} footprints from {subdir.name}", file=sys.stderr)
            if not footprint_libs:
                footprint_libs[lib_name] = parse_footprint_library(fp_dir)
                print(f"Loaded {len(footprint_libs.get(lib_name, {}))} footprints from {fp_dir.name}", file=sys.stderr)
            continue
        footprint_libs[lib_name] = parse_footprint_library(fp_dir)
        print(f"Loaded {len(footprint_libs[lib_name])} footprints from {fp_dir.name}", file=sys.stderr)
    
    # Verify all symbols
    results = []
    for symbol in all_symbols:
        if not symbol.footprint:
            continue  # Skip symbols without footprint assigned
        result = verify_symbol(symbol, footprint_libs)
        results.append(result)
    
    # Output results
    if args.json:
        json_results = []
        for r in results:
            json_results.append({
                'symbol': r.symbol_name,
                'footprint': r.footprint_name,
                'status': r.status,
                'symbol_pins': r.symbol_pin_count,
                'footprint_pads': r.footprint_pad_count,
                'pins_without_pads': sorted(r.pins_without_pads),
                'pads_without_pins': sorted(r.pads_without_pins),
                'duplicate_pins': dict(sorted(r.duplicate_pins.items()))
            })
        print(json.dumps(json_results, indent=2))
    else:
        ok_count = sum(1 for r in results if r.status == "OK")
        mismatch_count = sum(1 for r in results if r.status == "MISMATCH")
        not_found_count = sum(1 for r in results if r.status == "FOOTPRINT_NOT_FOUND")
        
        print(f"\n{'='*60}")
        print(f"Pin-to-Pad Verification Results")
        print(f"{'='*60}\n")
        
        # Show mismatches first
        mismatches = [r for r in results if r.status == "MISMATCH"]
        if mismatches:
            print("MISMATCHES:\n")
            for r in mismatches:
                print(format_result(r, args.verbose))
                print()
        
        # Show not found
        not_found = [r for r in results if r.status == "FOOTPRINT_NOT_FOUND"]
        if not_found:
            print("FOOTPRINTS NOT FOUND:\n")
            for r in not_found:
                print(format_result(r, args.verbose))
                print()
        
        # Show OK if verbose
        if args.verbose:
            ok_results = [r for r in results if r.status == "OK"]
            if ok_results:
                print("VERIFIED OK:\n")
                for r in ok_results:
                    print(format_result(r, args.verbose))
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Summary: {ok_count} OK, {mismatch_count} mismatches, {not_found_count} footprints not found")
        print(f"{'='*60}")
        
        # Exit with error code if mismatches found
        if mismatch_count > 0:
            sys.exit(1)


if __name__ == '__main__':
    main()
