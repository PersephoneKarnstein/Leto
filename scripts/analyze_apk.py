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

    def run(self, extract_only: bool = False, decompile: bool = False, enhanced: bool = False):
        """Run the full analysis workflow."""
        print(f"[*] Analyzing: {self.apk_path}")
        print(f"[*] Output directory: {self.output_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract APK
        print("\n[1/6] Extracting APK...")
        self.extract_apk()

        if extract_only:
            print(f"\n[*] Extraction complete. Files at: {self.extracted_dir}")
            return

        # Step 2: Identify Hermes bundle
        print("\n[2/6] Identifying Hermes bundle...")
        self.find_hermes_bundle()

        # Step 3: Detect Hermes version
        print("\n[3/6] Detecting Hermes version...")
        self.detect_hermes_version()

        # Step 4: Extract strings and endpoints
        print("\n[4/6] Extracting strings and endpoints...")
        self.extract_strings()

        # Step 5: Enhanced secret scan if requested
        if enhanced and self.report["bundle_path"]:
            print("\n[5/6] Running enhanced secret scan...")
            self.run_enhanced_scan()
        else:
            print("\n[5/6] Skipping enhanced scan (use --enhanced to enable)")

        # Step 6: Decompile if requested
        if decompile and self.report["bundle_path"]:
            print("\n[6/6] Decompiling bundle...")
            self.decompile_bundle()
        else:
            print("\n[6/6] Skipping decompilation (use --decompile to enable)")

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
        """Detect Hermes bytecode version using multiple methods."""
        if not self.report["hermes_detected"]:
            return

        bundle_path = Path(self.report["bundle_path"])

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

        version = None

        # Method 1: Use `file` command (most reliable)
        try:
            result = subprocess.run(
                ["file", str(bundle_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse: "Hermes JavaScript bytecode, version 96"
            match = re.search(r'Hermes JavaScript bytecode, version (\d+)', result.stdout)
            if match:
                version = int(match.group(1))
                print(f"    [+] Version detected via file command: {version}")
        except Exception as e:
            print(f"    [!] file command failed: {e}")

        # Method 2: Parse header directly (fallback)
        if version is None:
            try:
                with open(bundle_path, 'rb') as f:
                    # Skip magic bytes (4 bytes)
                    f.read(4)
                    # Read version - Hermes header format varies by version
                    # For newer versions, version is at offset 4
                    raw_version = int.from_bytes(f.read(4), 'little')
                    # Check if it looks like a valid version (< 200)
                    if raw_version < 200:
                        version = raw_version
                    else:
                        # Try parsing as older format
                        f.seek(8)
                        raw_version = int.from_bytes(f.read(4), 'little')
                        if raw_version < 200:
                            version = raw_version
                print(f"    [+] Version from header parsing: {version}")
            except Exception as e:
                print(f"    [!] Header parsing failed: {e}")

        if version:
            self.report["hermes_version"] = {
                "bytecode_version": version,
                "estimated_rn_version": version_map.get(version, f"Unknown (bytecode v{version})")
            }
            print(f"    [+] Bytecode version: {version}")
            print(f"    [+] Estimated version: {self.report['hermes_version']['estimated_rn_version']}")
        else:
            print("    [!] Could not determine Hermes version")
            print("    [!] Use 'file <bundle>' manually to verify")

    def extract_strings(self):
        """Extract interesting strings from the bundle including encoded secrets."""
        if not self.report["bundle_path"]:
            return

        bundle_path = Path(self.report["bundle_path"])

        # Read entire file for string analysis
        with open(bundle_path, 'rb') as f:
            content_bytes = f.read()
        content = content_bytes.decode('utf-8', errors='ignore')

        strings_found = set()

        # Direct pattern matching
        patterns = {
            'api_endpoints': re.compile(r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+'),
            'aws_key': re.compile(r'AKIA[0-9A-Z]{16}'),
            'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'),
            'firebase_key': re.compile(r'AIza[a-zA-Z0-9_-]{35}'),
            'github_token': re.compile(r'gh[pousr]_[a-zA-Z0-9]{36,}'),
            'stripe_key': re.compile(r'sk_(?:test|live)_[a-zA-Z0-9]{24,}'),
            'sendgrid_key': re.compile(r'SG\.[a-zA-Z0-9_-]{22,}'),
            'oauth_secret': re.compile(r'GOCSPX-[a-zA-Z0-9_-]{28}'),
            'database_url': re.compile(r'(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s"\'<>]+'),
            'private_key': re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'),
        }

        # Run direct pattern matching
        for name, pattern in patterns.items():
            for match in pattern.finditer(content):
                value = match.group()
                if name == 'api_endpoints':
                    # Filter common CDN/tracking URLs
                    skip = ['facebook.com', 'google.com', 'googleapis.com', 'cloudflare',
                            'cdn', 'analytics', 'react.dev', 'github.com/react-native']
                    if not any(x in value.lower() for x in skip):
                        strings_found.add(('url', value))
                else:
                    strings_found.add((name, value[:100] + '...' if len(value) > 100 else value))

        # Base64 encoded secrets detection
        import base64
        b64_pattern = re.compile(r'["\']([A-Za-z0-9+/]{20,}={0,2})["\']')
        interesting_keywords = ['api', 'key', 'secret', 'password', 'token', 'http', 'admin', 'aws', 'slack']

        for match in b64_pattern.finditer(content):
            b64_str = match.group(1)
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                if any(kw in decoded.lower() for kw in interesting_keywords):
                    strings_found.add(('base64_decoded', f"[B64] {decoded[:80]}..."))
            except Exception:
                pass

        # Hex encoded secrets detection
        hex_pattern = re.compile(r'["\']([0-9a-fA-F]{20,})["\']')
        for match in hex_pattern.finditer(content):
            hex_str = match.group(1)
            if len(hex_str) % 2 == 0:
                try:
                    decoded = bytes.fromhex(hex_str).decode('utf-8', errors='ignore')
                    if decoded and len(decoded) > 5 and decoded.isprintable():
                        strings_found.add(('hex_decoded', f"[HEX] {decoded[:80]}..."))
                except Exception:
                    pass

        # Anti-tampering detection
        anti_tamper_indicators = [
            'checkRoot', 'isRooted', 'checkFrida', 'checkDebugger', 'checkEmulator',
            'checkIntegrity', 'SSL_PINS', 'certificatePinning', 'jailbreakCheck'
        ]
        for indicator in anti_tamper_indicators:
            if indicator in content:
                strings_found.add(('anti_tamper', indicator))

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

        # Report anti-tampering if found
        anti_tamper = [s for s in self.report['interesting_strings'] if s['type'] == 'anti_tamper']
        if anti_tamper:
            print(f"    [!] Anti-tampering code detected: {len(anti_tamper)} indicators")

    def run_enhanced_scan(self):
        """Run the enhanced secret scanner for obfuscated secrets."""
        bundle_path = Path(self.report["bundle_path"])

        # Try to import the enhanced scanner
        try:
            script_dir = Path(__file__).parent
            sys.path.insert(0, str(script_dir))
            from enhanced_secret_scan import EnhancedSecretScanner

            scanner = EnhancedSecretScanner(str(bundle_path))
            findings = scanner.scan_all()
            summary = scanner.get_summary()

            # Add to report
            self.report["enhanced_scan"] = {
                "summary": summary,
                "base64_secrets": findings['base64_encoded'][:20],
                "hex_secrets": findings['hex_encoded'][:20],
                "char_arrays": findings['char_code_arrays'][:10],
                "split_fragments": findings['split_fragments'][:20],
                "anti_tampering": findings['anti_tampering'],
            }

            print(f"    [+] Total findings: {summary['total_findings']}")
            print(f"    [+] Base64 encoded secrets: {summary['base64_encoded']}")
            print(f"    [+] Hex encoded secrets: {summary['hex_encoded']}")
            print(f"    [+] Character code arrays: {summary['char_code_arrays']}")
            print(f"    [+] Split string fragments: {summary['split_fragments']}")
            print(f"    [+] Anti-tampering indicators: {summary['anti_tampering_indicators']}")

            # Save detailed enhanced scan results
            enhanced_report_path = self.output_dir / "enhanced_scan.json"
            with open(enhanced_report_path, 'w') as f:
                json.dump(findings, f, indent=2)
            print(f"    [+] Detailed scan saved to: {enhanced_report_path}")

        except ImportError as e:
            print(f"    [!] Enhanced scanner not available: {e}")
            print("    [!] Run: python scripts/enhanced_secret_scan.py <bundle> manually")

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
    parser.add_argument("--enhanced", action="store_true", help="Run enhanced secret scan (detects obfuscated secrets)")

    args = parser.parse_args()

    if not os.path.exists(args.apk):
        print(f"Error: APK not found: {args.apk}")
        sys.exit(1)

    analyzer = APKAnalyzer(args.apk, args.output_dir)
    analyzer.run(extract_only=args.extract_only, decompile=args.decompile, enhanced=args.enhanced)


if __name__ == "__main__":
    main()
