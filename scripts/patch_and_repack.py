#!/usr/bin/env python3
"""
Patch Hermes bundle and repackage APK.

This script automates the workflow:
1. Extract APK with apktool
2. Locate and backup original bundle
3. Replace with patched bundle
4. Fix Hermes hash (via r2hermes)
5. Rebuild and sign APK

Usage:
    # Repack with new bundle
    python patch_and_repack.py original.apk patched.bundle --output patched.apk

    # Just fix hash on a bundle
    python patch_and_repack.py --fix-hash modified.bundle

    # Full workflow with keystore
    python patch_and_repack.py original.apk patched.bundle --keystore debug.keystore --alias debug
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_cmd(cmd: list, description: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run command with error handling."""
    if description:
        print(f"[*] {description}...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(f"Error: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    return result


def check_tool(tool: str) -> bool:
    """Check if tool is available."""
    return shutil.which(tool) is not None


def fix_hermes_hash(bundle_path: str) -> bool:
    """Fix Hermes footer hash using r2hermes."""
    if not check_tool("r2"):
        print("Error: radare2 not found. Cannot fix hash.", file=sys.stderr)
        return False

    # Check if r2hermes is installed
    result = subprocess.run(
        ["r2", "-qc", "pd:h?", "/dev/null"],
        capture_output=True,
        text=True,
    )
    if "Usage" not in result.stdout + result.stderr:
        print("Error: r2hermes not installed. Run: r2pm -ci r2hermes", file=sys.stderr)
        return False

    # Fix hash
    result = run_cmd(
        ["r2", "-wqc", ".(fix-hbc)", bundle_path],
        f"Fixing hash for {bundle_path}",
        check=False,
    )

    if result.returncode != 0:
        print(f"Warning: Hash fix may have failed: {result.stderr}", file=sys.stderr)
        return False

    # Verify
    result = run_cmd(
        ["r2", "-qc", "pd:hi", bundle_path],
        "Verifying hash",
        check=False,
    )
    if "valid" in result.stdout.lower():
        print("[+] Hash verified: valid")
        return True
    else:
        print("[!] Hash status unknown")
        return True  # Continue anyway


def decompile_apk(apk_path: str, output_dir: str) -> bool:
    """Decompile APK using apktool."""
    if not check_tool("apktool"):
        print("Error: apktool not found", file=sys.stderr)
        return False

    run_cmd(
        ["apktool", "d", "-f", "-o", output_dir, apk_path],
        f"Decompiling {apk_path}",
    )
    return True


def build_apk(source_dir: str, output_path: str) -> bool:
    """Build APK from decompiled source."""
    run_cmd(
        ["apktool", "b", "-o", output_path, source_dir],
        f"Building APK",
    )
    return True


def sign_apk(apk_path: str, keystore: str, alias: str, password: str = "android") -> bool:
    """Sign APK with keystore."""
    # Try apksigner first (preferred)
    if check_tool("apksigner"):
        run_cmd(
            [
                "apksigner", "sign",
                "--ks", keystore,
                "--ks-key-alias", alias,
                "--ks-pass", f"pass:{password}",
                apk_path,
            ],
            "Signing APK with apksigner",
        )
        return True

    # Fall back to jarsigner
    if check_tool("jarsigner"):
        run_cmd(
            [
                "jarsigner",
                "-verbose",
                "-keystore", keystore,
                "-storepass", password,
                apk_path,
                alias,
            ],
            "Signing APK with jarsigner",
        )
        return True

    print("Error: Neither apksigner nor jarsigner found", file=sys.stderr)
    return False


def zipalign_apk(input_path: str, output_path: str) -> bool:
    """Align APK for optimal loading."""
    if not check_tool("zipalign"):
        print("Warning: zipalign not found, skipping alignment", file=sys.stderr)
        shutil.copy(input_path, output_path)
        return True

    run_cmd(
        ["zipalign", "-v", "-f", "4", input_path, output_path],
        "Aligning APK",
    )
    return True


def find_bundle_in_extracted(extracted_dir: str) -> str:
    """Find Hermes bundle in extracted APK."""
    assets_dir = os.path.join(extracted_dir, "assets")

    if not os.path.exists(assets_dir):
        return None

    bundle_names = [
        "index.android.bundle",
        "index.bundle",
        "main.jsbundle",
    ]

    for name in bundle_names:
        path = os.path.join(assets_dir, name)
        if os.path.exists(path):
            return path

    # Search for any .bundle file
    for root, dirs, files in os.walk(assets_dir):
        for f in files:
            if f.endswith(".bundle") or f.endswith(".hbc"):
                return os.path.join(root, f)

    return None


def create_debug_keystore(keystore_path: str) -> bool:
    """Create a debug keystore for signing."""
    if os.path.exists(keystore_path):
        return True

    if not check_tool("keytool"):
        print("Error: keytool not found", file=sys.stderr)
        return False

    run_cmd(
        [
            "keytool", "-genkey", "-v",
            "-keystore", keystore_path,
            "-alias", "debug",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=Debug,OU=Debug,O=Debug,L=Debug,S=Debug,C=US",
        ],
        "Creating debug keystore",
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Patch Hermes bundle and repackage APK")
    parser.add_argument("apk", nargs="?", help="Original APK file")
    parser.add_argument("bundle", nargs="?", help="Patched bundle file")
    parser.add_argument("--output", "-o", help="Output APK path")
    parser.add_argument("--keystore", help="Keystore for signing")
    parser.add_argument("--alias", default="debug", help="Key alias (default: debug)")
    parser.add_argument("--password", default="android", help="Keystore password")
    parser.add_argument("--fix-hash", metavar="BUNDLE", help="Just fix hash on a bundle")
    parser.add_argument("--no-sign", action="store_true", help="Skip signing step")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    args = parser.parse_args()

    # Hash fix only mode
    if args.fix_hash:
        if not os.path.exists(args.fix_hash):
            print(f"Error: Bundle not found: {args.fix_hash}", file=sys.stderr)
            sys.exit(1)
        fix_hermes_hash(args.fix_hash)
        sys.exit(0)

    # Full repack mode
    if not args.apk or not args.bundle:
        parser.error("Both APK and bundle arguments required for repacking")

    if not os.path.exists(args.apk):
        print(f"Error: APK not found: {args.apk}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.bundle):
        print(f"Error: Bundle not found: {args.bundle}", file=sys.stderr)
        sys.exit(1)

    # Set output path
    output_path = args.output
    if not output_path:
        base = os.path.splitext(args.apk)[0]
        output_path = f"{base}_patched.apk"

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="hermes_patch_")
    extracted_dir = os.path.join(temp_dir, "extracted")
    unsigned_apk = os.path.join(temp_dir, "unsigned.apk")

    try:
        # Step 1: Decompile APK
        decompile_apk(args.apk, extracted_dir)

        # Step 2: Find original bundle
        original_bundle = find_bundle_in_extracted(extracted_dir)
        if not original_bundle:
            print("Error: Could not find Hermes bundle in APK", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Found bundle: {original_bundle}")

        # Step 3: Backup and replace
        backup_path = original_bundle + ".backup"
        shutil.copy(original_bundle, backup_path)
        print(f"[*] Backed up to: {backup_path}")

        shutil.copy(args.bundle, original_bundle)
        print(f"[*] Replaced with: {args.bundle}")

        # Step 4: Fix hash
        fix_hermes_hash(original_bundle)

        # Step 5: Rebuild APK
        build_apk(extracted_dir, unsigned_apk)

        # Step 6: Sign
        if not args.no_sign:
            keystore = args.keystore
            if not keystore:
                keystore = os.path.join(temp_dir, "debug.keystore")
                create_debug_keystore(keystore)

            # Zipalign then sign
            aligned_apk = os.path.join(temp_dir, "aligned.apk")
            zipalign_apk(unsigned_apk, aligned_apk)
            sign_apk(aligned_apk, keystore, args.alias, args.password)
            shutil.copy(aligned_apk, output_path)
        else:
            shutil.copy(unsigned_apk, output_path)

        print()
        print(f"[+] Patched APK created: {output_path}")
        print()
        print("Install with:")
        print(f"  adb install -r {output_path}")

    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f"[*] Temp files kept at: {temp_dir}")


if __name__ == "__main__":
    main()
