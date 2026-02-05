#!/usr/bin/env python3
"""
Quick Hermes bundle analyzer.
Detects version, extracts basic info, and runs available analysis tools.

Usage:
    python analyze_bundle.py <bundle_file> [--output DIR] [--json] [--strings] [--functions]
"""

import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path


def read_hermes_header(filepath: str) -> dict:
    """Read Hermes bytecode header to extract version and basic info."""
    info = {
        "file": filepath,
        "is_hermes": False,
        "version": None,
        "error": None,
    }

    try:
        with open(filepath, "rb") as f:
            magic = f.read(8)

            # Hermes magic: 0xc61fbc03 or variations
            if len(magic) >= 8:
                # Check for Hermes magic bytes
                if magic[0:4] == b"\xc6\x1f\xbc\x03" or magic[0:4] == b"\x1f\xc6\x03\xbc":
                    info["is_hermes"] = True
                    # Version is typically at offset 4-7 (little endian)
                    info["version"] = struct.unpack("<I", magic[4:8])[0]

            # Alternative: check for "HermesB" signature
            f.seek(0)
            header = f.read(64)
            if b"Hermes" in header:
                info["is_hermes"] = True

            # Get file size
            f.seek(0, 2)
            info["size_bytes"] = f.tell()

    except Exception as e:
        info["error"] = str(e)

    return info


def run_r2hermes_info(filepath: str) -> dict:
    """Get detailed info using r2hermes."""
    result = {"available": False, "info": None, "function_count": None}

    try:
        proc = subprocess.run(
            ["r2", "-qc", "pd:hi", filepath],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            result["available"] = True
            result["info"] = proc.stdout.strip()

            # Try to get function count
            proc2 = subprocess.run(
                ["r2", "-qc", "pd:hf~?", filepath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc2.returncode == 0:
                try:
                    result["function_count"] = int(proc2.stdout.strip())
                except ValueError:
                    pass

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return result


def run_r2hermes_functions(filepath: str, limit: int = 50) -> list:
    """Get function list using r2hermes."""
    functions = []

    try:
        proc = subprocess.run(
            ["r2", "-qc", "pd:hf", filepath],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode == 0:
            for line in proc.stdout.strip().split("\n")[:limit]:
                if line.strip():
                    functions.append(line.strip())

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return functions


def run_hermes_rs_strings(filepath: str, limit: int = 100) -> list:
    """Extract strings using hermes_rs - DISABLED for large bundles."""
    # hermes_rs processes entire file and will hang on large bundles
    # Return empty and use safe_extract_strings instead
    return []


def safe_extract_strings(filepath: str, limit: int = 100, chunk_size: int = 2_000_000) -> list:
    """
    Safely extract strings from large bundles by reading in chunks.
    Only reads first and last chunks to avoid hanging.
    """
    import re
    strings = set()
    file_size = os.path.getsize(filepath)

    # String pattern: printable ASCII sequences of 6+ chars
    string_pattern = re.compile(rb'[\x20-\x7e]{6,}')

    try:
        with open(filepath, 'rb') as f:
            # Read first chunk
            data = f.read(chunk_size)
            for match in string_pattern.findall(data):
                try:
                    strings.add(match.decode('utf-8', errors='ignore'))
                except:
                    pass

            # Read last chunk if file is large enough
            if file_size > chunk_size * 2:
                f.seek(-chunk_size, 2)
                data = f.read(chunk_size)
                for match in string_pattern.findall(data):
                    try:
                        strings.add(match.decode('utf-8', errors='ignore'))
                    except:
                        pass
    except Exception as e:
        pass

    # Filter and sort
    result = sorted([s for s in strings if len(s) >= 6])[:limit]
    return result


def find_interesting_patterns(strings: list) -> dict:
    """Analyze strings for security-relevant patterns."""
    patterns = {
        "urls": [],
        "api_endpoints": [],
        "potential_secrets": [],
        "auth_related": [],
    }

    keywords_auth = ["auth", "login", "token", "jwt", "bearer", "session", "password"]
    keywords_secret = ["key", "secret", "private", "api_key", "apikey"]

    for s in strings:
        s_lower = s.lower()

        if s.startswith("http://") or s.startswith("https://"):
            patterns["urls"].append(s)
            if "/api" in s_lower or "/v1" in s_lower or "/v2" in s_lower:
                patterns["api_endpoints"].append(s)

        if any(kw in s_lower for kw in keywords_auth):
            patterns["auth_related"].append(s)

        if any(kw in s_lower for kw in keywords_secret):
            # Filter out common false positives
            if len(s) > 10 and not s.startswith("function"):
                patterns["potential_secrets"].append(s)

    return patterns


def main():
    parser = argparse.ArgumentParser(description="Analyze Hermes bytecode bundle")
    parser.add_argument("bundle", help="Path to Hermes bytecode file")
    parser.add_argument("--output", "-o", help="Output directory for results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strings", action="store_true", help="Extract strings")
    parser.add_argument("--functions", action="store_true", help="List functions")
    parser.add_argument(
        "--limit", type=int, default=50, help="Limit results (default: 50)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.bundle):
        print(f"Error: File not found: {args.bundle}", file=sys.stderr)
        sys.exit(1)

    # Gather analysis results
    results = {
        "header": read_hermes_header(args.bundle),
        "r2hermes": run_r2hermes_info(args.bundle),
    }

    if args.functions:
        results["functions"] = run_r2hermes_functions(args.bundle, args.limit)

    if args.strings:
        # Use safe extraction for large bundles (>5MB)
        file_size = os.path.getsize(args.bundle)
        if file_size > 5_000_000:
            print(f"Note: Large bundle ({file_size:,} bytes) - using chunked string extraction", file=sys.stderr)
        strings = safe_extract_strings(args.bundle, args.limit * 2)
        results["strings"] = strings[:args.limit]
        results["patterns"] = find_interesting_patterns(strings)

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Pretty print
        h = results["header"]
        print(f"Hermes Bundle Analysis: {h['file']}")
        print("=" * 60)

        if h["is_hermes"]:
            print(f"  Format:    Hermes Bytecode")
            print(f"  Version:   {h.get('version', 'unknown')}")
            print(f"  Size:      {h.get('size_bytes', 0):,} bytes")
        else:
            print("  WARNING: File may not be Hermes bytecode")

        r2 = results["r2hermes"]
        if r2["available"]:
            print()
            print("r2hermes Info:")
            print("-" * 40)
            print(r2["info"])
            if r2["function_count"]:
                print(f"\nTotal functions: {r2['function_count']}")

        if args.functions and results.get("functions"):
            print()
            print(f"Functions (first {args.limit}):")
            print("-" * 40)
            for f in results["functions"]:
                print(f"  {f}")

        if args.strings and results.get("patterns"):
            p = results["patterns"]
            print()
            print("Interesting Patterns Found:")
            print("-" * 40)

            if p["api_endpoints"]:
                print(f"\nAPI Endpoints ({len(p['api_endpoints'])}):")
                for s in p["api_endpoints"][:10]:
                    print(f"  {s}")

            if p["auth_related"]:
                print(f"\nAuth-related ({len(p['auth_related'])}):")
                for s in p["auth_related"][:10]:
                    print(f"  {s}")

            if p["potential_secrets"]:
                print(f"\nPotential Secrets ({len(p['potential_secrets'])}):")
                for s in p["potential_secrets"][:5]:
                    print(f"  {s[:50]}...")

    # Save to output directory if specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        output_file = Path(args.output) / "analysis.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
