#!/usr/bin/env python3
"""
APK Analysis Workflow Script

Automates the analysis workflow for React Native / Hermes APKs:
1. Extract APK contents
2. Identify Hermes bundle and version
3. Decompile/disassemble the bundle
4. Extract strings and API endpoints
5. Generate analysis report

Usage:
    python analyze_apk.py target.apk [--output-dir ./output]
    python analyze_apk.py target.apk --extract-only
    python analyze_apk.py target.apk --decompile
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional


class APKAnalyzer:
    def __init__(self, apk_path: str, output_dir: Optional[str] = None):
        self.apk_path = Path(apk_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.apk_path.parent / f"{self.apk_path.stem}_analysis"
        self.extracted_dir = self.output_dir / "extracted"
        self.report = {
            "apk_name": self.apk_path.name,
            "hermes_detected": False,
            "hermes_version": None,
            "bundle_path": None,
            "bundle_size": 0,
            "api_endpoints": [],
            "interesting_strings": [],
            "native_libs": [],
            "permissions": [],
        }

    def run(self, extract_only: bool = False, decompile: bool = False):
        """Run the full analysis workflow."""
        print(f"[*] Analyzing: {self.apk_path}")
        print(f"[*] Output directory: {self.output_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract APK
        print("\n[1/5] Extracting APK...")
        self.extract_apk()

        if extract_only:
            print(f"\n[*] Extraction complete. Files at: {self.extracted_dir}")
            return

        # Step 2: Identify Hermes bundle
        print("\n[2/5] Identifying Hermes bundle...")
        self.find_hermes_bundle()

        # Step 3: Detect Hermes version
        print("\n[3/5] Detecting Hermes version...")
        self.detect_hermes_version()

        # Step 4: Extract strings and endpoints
        print("\n[4/5] Extracting strings and endpoints...")
        self.extract_strings()

        # Step 5: Decompile if requested
        if decompile and self.report["bundle_path"]:
            print("\n[5/5] Decompiling bundle...")
            self.decompile_bundle()
        else:
            print("\n[5/5] Skipping decompilation (use --decompile to enable)")

        # Generate report
        self.generate_report()

        print(f"\n[*] Analysis complete!")
        print(f"[*] Report saved to: {self.output_dir / 'report.json'}")

    def extract_apk(self):
        """Extract APK contents."""
        if self.extracted_dir.exists():
            shutil.rmtree(self.extracted_dir)

        with zipfile.ZipFile(self.apk_path, 'r') as zf:
            zf.extractall(self.extracted_dir)

        # Also run apktool for manifest parsing if available
        if shutil.which("apktool"):
            apktool_dir = self.output_dir / "apktool"
            try:
                subprocess.run(
                    ["apktool", "d", "-f", "-o", str(apktool_dir), str(self.apk_path)],
                    capture_output=True,
                    timeout=120
                )
                # Extract permissions from decoded manifest
                manifest = apktool_dir / "AndroidManifest.xml"
                if manifest.exists():
                    self.parse_manifest(manifest)
            except Exception as e:
                print(f"    [!] apktool failed: {e}")

    def parse_manifest(self, manifest_path: Path):
        """Parse AndroidManifest.xml for permissions."""
        content = manifest_path.read_text(errors='ignore')
        permissions = re.findall(r'android:name="android\.permission\.([^"]+)"', content)
        self.report["permissions"] = list(set(permissions))

    def find_hermes_bundle(self):
        """Locate the Hermes bytecode bundle."""
        bundle_names = [
            "index.android.bundle",
            "index.bundle",
            "main.jsbundle",
            "app.bundle"
        ]

        assets_dir = self.extracted_dir / "assets"
        if not assets_dir.exists():
            print("    [!] No assets directory found")
            return

        for bundle_name in bundle_names:
            bundle_path = assets_dir / bundle_name
            if bundle_path.exists():
                self.report["bundle_path"] = str(bundle_path)
                self.report["bundle_size"] = bundle_path.stat().st_size

                # Check if it's Hermes bytecode
                with open(bundle_path, 'rb') as f:
                    magic = f.read(8)
                    # Hermes magic: 0xc61fbc03 0x19840401
                    if magic[:4] == b'\xc6\x1f\xbc\x03':
                        self.report["hermes_detected"] = True
                        print(f"    [+] Found Hermes bundle: {bundle_name}")
                        print(f"    [+] Size: {self.report['bundle_size']:,} bytes")
                    else:
                        print(f"    [+] Found JS bundle (not Hermes): {bundle_name}")
                return

        print("    [!] No bundle found")

    def detect_hermes_version(self):
        """Detect Hermes bytecode version."""
        if not self.report["hermes_detected"]:
            return

        bundle_path = Path(self.report["bundle_path"])

        # Read header to get version
        with open(bundle_path, 'rb') as f:
            magic = f.read(4)
            version = int.from_bytes(f.read(4), 'little')

            # Hermes bytecode versions
            version_map = {
                59: "0.1.0",
                62: "0.4.0",
                74: "0.7.0",
                76: "0.8.0",
                84: "0.11.0",
                85: "0.12.0",
                89: "React Native 0.64+",
                90: "React Native 0.65+",
                93: "React Native 0.70+",
                94: "React Native 0.71+",
                95: "React Native 0.72+",
                96: "React Native 0.73+",
            }

            self.report["hermes_version"] = {
                "bytecode_version": version,
                "estimated_rn_version": version_map.get(version, f"Unknown (bytecode v{version})")
            }

            print(f"    [+] Bytecode version: {version}")
            print(f"    [+] Estimated version: {self.report['hermes_version']['estimated_rn_version']}")

    def extract_strings(self):
        """Extract interesting strings from the bundle."""
        if not self.report["bundle_path"]:
            return

        bundle_path = Path(self.report["bundle_path"])

        # Read file in chunks to handle large bundles
        chunk_size = 2 * 1024 * 1024  # 2MB chunks
        strings_found = set()

        # Patterns to look for
        patterns = {
            'api_endpoints': re.compile(rb'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+'),
            'api_keys': re.compile(rb'(?:api[_-]?key|apikey|api_secret|secret_key)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', re.I),
            'aws': re.compile(rb'(?:AKIA|ABIA|ACCA)[A-Z0-9]{16}'),
            'jwt': re.compile(rb'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'),
            'firebase': re.compile(rb'[a-z0-9-]+\.firebaseio\.com'),
            'graphql': re.compile(rb'(?:query|mutation|subscription)\s+\w+'),
        }

        with open(bundle_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                # Find URLs
                for match in patterns['api_endpoints'].finditer(chunk):
                    url = match.group().decode('utf-8', errors='ignore')
                    # Filter out common CDN/tracking URLs
                    if not any(x in url.lower() for x in ['facebook.com', 'google.com', 'googleapis.com',
                                                           'cloudflare', 'cdn', 'analytics']):
                        strings_found.add(('url', url))

                # Find potential API keys
                for match in patterns['api_keys'].finditer(chunk):
                    strings_found.add(('api_key', match.group(1).decode('utf-8', errors='ignore')))

                # Find AWS keys
                for match in patterns['aws'].finditer(chunk):
                    strings_found.add(('aws_key', match.group().decode('utf-8', errors='ignore')))

                # Find JWTs
                for match in patterns['jwt'].finditer(chunk):
                    jwt = match.group().decode('utf-8', errors='ignore')
                    strings_found.add(('jwt', jwt[:50] + '...'))

                # Find Firebase URLs
                for match in patterns['firebase'].finditer(chunk):
                    strings_found.add(('firebase', match.group().decode('utf-8', errors='ignore')))

        # Categorize findings
        for category, value in strings_found:
            if category == 'url':
                self.report["api_endpoints"].append(value)
            else:
                self.report["interesting_strings"].append({
                    "type": category,
                    "value": value
                })

        # Deduplicate and limit
        self.report["api_endpoints"] = list(set(self.report["api_endpoints"]))[:100]

        print(f"    [+] Found {len(self.report['api_endpoints'])} unique endpoints")
        print(f"    [+] Found {len(self.report['interesting_strings'])} interesting strings")

    def decompile_bundle(self):
        """Decompile the Hermes bundle using available tools."""
        bundle_path = Path(self.report["bundle_path"])
        decompiled_dir = self.output_dir / "decompiled"
        decompiled_dir.mkdir(exist_ok=True)

        # Try hbctool first
        if shutil.which("hbctool"):
            print("    [*] Using hbctool for disassembly...")
            try:
                subprocess.run(
                    ["hbctool", "disasm", str(bundle_path), str(decompiled_dir / "hbctool_output")],
                    capture_output=True,
                    timeout=300
                )
                print("    [+] hbctool disassembly complete")
            except Exception as e:
                print(f"    [!] hbctool failed: {e}")

        # Try hermes-dec
        if shutil.which("hbc-decompiler"):
            print("    [*] Using hermes-dec for decompilation...")
            try:
                result = subprocess.run(
                    ["hbc-decompiler", str(bundle_path)],
                    capture_output=True,
                    timeout=600
                )
                output_file = decompiled_dir / "hermes_dec_output.js"
                output_file.write_bytes(result.stdout)
                print(f"    [+] hermes-dec output saved to {output_file}")
            except Exception as e:
                print(f"    [!] hermes-dec failed: {e}")

        # Try r2hermes
        if shutil.which("r2"):
            print("    [*] Using radare2 + r2hermes...")
            try:
                result = subprocess.run(
                    ["r2", "-qc", "pd 100", str(bundle_path)],
                    capture_output=True,
                    timeout=60
                )
                output_file = decompiled_dir / "r2_disasm_sample.txt"
                output_file.write_bytes(result.stdout)
                print(f"    [+] r2 sample disassembly saved")
            except Exception as e:
                print(f"    [!] r2 analysis failed: {e}")

    def generate_report(self):
        """Generate the final analysis report."""
        # Find native libraries
        lib_dir = self.extracted_dir / "lib"
        if lib_dir.exists():
            for arch_dir in lib_dir.iterdir():
                if arch_dir.is_dir():
                    for lib in arch_dir.glob("*.so"):
                        self.report["native_libs"].append({
                            "name": lib.name,
                            "arch": arch_dir.name,
                            "size": lib.stat().st_size
                        })

        # Save report
        report_path = self.output_dir / "report.json"
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"APK: {self.report['apk_name']}")
        print(f"Hermes Detected: {self.report['hermes_detected']}")
        if self.report['hermes_version']:
            print(f"Hermes Version: {self.report['hermes_version']['estimated_rn_version']}")
        if self.report['bundle_size']:
            print(f"Bundle Size: {self.report['bundle_size']:,} bytes")
        print(f"API Endpoints Found: {len(self.report['api_endpoints'])}")
        print(f"Interesting Strings: {len(self.report['interesting_strings'])}")
        print(f"Native Libraries: {len(self.report['native_libs'])}")
        print(f"Permissions: {len(self.report['permissions'])}")

        # Show top endpoints
        if self.report['api_endpoints']:
            print("\nTop API Endpoints:")
            for url in self.report['api_endpoints'][:10]:
                print(f"  - {url}")

        # Show interesting findings
        if self.report['interesting_strings']:
            print("\nInteresting Strings:")
            for item in self.report['interesting_strings'][:5]:
                print(f"  [{item['type']}] {item['value']}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze React Native / Hermes APKs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s target.apk                    # Full analysis
  %(prog)s target.apk --output-dir ./out # Custom output directory
  %(prog)s target.apk --extract-only     # Just extract APK
  %(prog)s target.apk --decompile        # Include decompilation
        """
    )
    parser.add_argument("apk", help="Path to APK file")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--extract-only", action="store_true", help="Only extract APK contents")
    parser.add_argument("--decompile", action="store_true", help="Attempt to decompile Hermes bundle")

    args = parser.parse_args()

    if not os.path.exists(args.apk):
        print(f"Error: APK not found: {args.apk}")
        sys.exit(1)

    analyzer = APKAnalyzer(args.apk, args.output_dir)
    analyzer.run(extract_only=args.extract_only, decompile=args.decompile)


if __name__ == "__main__":
    main()
