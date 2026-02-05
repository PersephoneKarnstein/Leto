#!/usr/bin/env python3
"""
Extract Hermes bundle from APK or installed Android app.

Usage:
    # From APK file
    python extract_bundle.py app.apk --output ./extracted/

    # From installed app (via ADB)
    python extract_bundle.py --package com.example.app --output ./extracted/

    # Just locate bundle without extracting
    python extract_bundle.py app.apk --locate-only
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


BUNDLE_NAMES = [
    "index.android.bundle",
    "index.bundle",
    "main.jsbundle",
    "hermes.bundle",
]

BUNDLE_EXTENSIONS = [".hbc", ".bundle", ".jsbundle"]


def find_bundles_in_apk(apk_path: str) -> list:
    """Find Hermes bundle files in APK."""
    bundles = []

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            for name in zf.namelist():
                # Check known bundle names
                basename = os.path.basename(name)
                if basename in BUNDLE_NAMES:
                    bundles.append(name)
                    continue

                # Check extensions
                if any(name.endswith(ext) for ext in BUNDLE_EXTENSIONS):
                    bundles.append(name)
                    continue

                # Check in assets folder
                if name.startswith("assets/") and "bundle" in name.lower():
                    bundles.append(name)

    except zipfile.BadZipFile:
        print(f"Error: Invalid APK file: {apk_path}", file=sys.stderr)

    return bundles


def is_hermes_bytecode(data: bytes) -> bool:
    """Check if data is Hermes bytecode by magic bytes."""
    if len(data) < 8:
        return False

    # Hermes magic variations
    if data[0:4] == b"\xc6\x1f\xbc\x03":
        return True
    if data[0:4] == b"\x1f\xc6\x03\xbc":
        return True

    # Check for "Hermes" string in header
    if b"Hermes" in data[:64]:
        return True

    return False


def extract_from_apk(apk_path: str, output_dir: str, bundle_path: str = None) -> list:
    """Extract bundle(s) from APK to output directory."""
    extracted = []

    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(apk_path, "r") as zf:
        if bundle_path:
            # Extract specific bundle
            bundles = [bundle_path]
        else:
            # Find all bundles
            bundles = find_bundles_in_apk(apk_path)

        for bundle in bundles:
            try:
                data = zf.read(bundle)
                is_hermes = is_hermes_bytecode(data)

                out_name = os.path.basename(bundle)
                out_path = os.path.join(output_dir, out_name)

                with open(out_path, "wb") as f:
                    f.write(data)

                extracted.append({
                    "source": bundle,
                    "output": out_path,
                    "size": len(data),
                    "is_hermes": is_hermes,
                })

            except KeyError:
                print(f"Warning: Bundle not found in APK: {bundle}", file=sys.stderr)

    return extracted


def pull_apk_from_device(package_name: str, output_path: str) -> bool:
    """Pull APK from installed app via ADB."""
    try:
        # Get APK path
        result = subprocess.run(
            ["adb", "shell", "pm", "path", package_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"Error: Package not found: {package_name}", file=sys.stderr)
            return False

        # Parse path (format: "package:/data/app/.../base.apk")
        apk_path = result.stdout.strip()
        if apk_path.startswith("package:"):
            apk_path = apk_path[8:]

        # Pull APK
        result = subprocess.run(
            ["adb", "pull", apk_path, output_path],
            capture_output=True,
            text=True,
            timeout=60,
        )

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Error: ADB command timed out", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: ADB not found. Is Android SDK installed?", file=sys.stderr)
        return False


def check_for_hermes_lib(apk_path: str) -> dict:
    """Check if APK contains Hermes native library."""
    libs = {"arm64-v8a": False, "armeabi-v7a": False, "x86": False, "x86_64": False}

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            for name in zf.namelist():
                if "libhermes" in name.lower():
                    for arch in libs:
                        if arch in name:
                            libs[arch] = True

    except zipfile.BadZipFile:
        pass

    return libs


def main():
    parser = argparse.ArgumentParser(
        description="Extract Hermes bundle from APK or device"
    )
    parser.add_argument("apk", nargs="?", help="Path to APK file")
    parser.add_argument("--package", "-p", help="Package name to pull from device")
    parser.add_argument("--output", "-o", default="./extracted", help="Output directory")
    parser.add_argument(
        "--locate-only", action="store_true", help="Only locate bundles, don't extract"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.apk and not args.package:
        parser.error("Either APK path or --package is required")

    apk_path = args.apk
    temp_apk = None

    # Pull from device if package specified
    if args.package:
        temp_apk = tempfile.NamedTemporaryFile(suffix=".apk", delete=False)
        temp_apk.close()
        apk_path = temp_apk.name

        print(f"Pulling APK for {args.package}...")
        if not pull_apk_from_device(args.package, apk_path):
            if temp_apk:
                os.unlink(temp_apk.name)
            sys.exit(1)
        print(f"APK saved to: {apk_path}")

    # Check APK exists
    if not os.path.exists(apk_path):
        print(f"Error: File not found: {apk_path}", file=sys.stderr)
        sys.exit(1)

    # Find bundles
    bundles = find_bundles_in_apk(apk_path)
    hermes_libs = check_for_hermes_lib(apk_path)

    if args.locate_only:
        print(f"APK: {apk_path}")
        print()
        print("Hermes Libraries:")
        for arch, present in hermes_libs.items():
            status = "YES" if present else "no"
            print(f"  {arch}: {status}")
        print()
        print(f"Found {len(bundles)} bundle(s):")
        for b in bundles:
            print(f"  {b}")

        if temp_apk:
            os.unlink(temp_apk.name)
        return

    # Extract bundles
    if not bundles:
        print("No Hermes bundles found in APK", file=sys.stderr)
        if temp_apk:
            os.unlink(temp_apk.name)
        sys.exit(1)

    extracted = extract_from_apk(apk_path, args.output)

    if args.json:
        import json

        print(json.dumps(extracted, indent=2))
    else:
        print(f"Extracted {len(extracted)} bundle(s) to {args.output}/")
        for e in extracted:
            hermes_tag = " [Hermes]" if e["is_hermes"] else " [JS?]"
            print(f"  {e['output']} ({e['size']:,} bytes){hermes_tag}")

    # Cleanup temp file
    if temp_apk:
        os.unlink(temp_apk.name)


if __name__ == "__main__":
    main()
