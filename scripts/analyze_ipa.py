#!/usr/bin/env python3
"""
IPA Analysis Workflow Script

Automates the analysis workflow for React Native / Hermes iOS apps:
1. Extract IPA contents
2. Identify Hermes bundle and version
3. Parse Info.plist (ATS, URL schemes)
4. Extract entitlements
5. Parse PrivacyInfo.xcprivacy (iOS 17+)
6. Check binary architecture
7. Extract strings and API endpoints
8. Generate analysis report

Usage:
    python analyze_ipa.py target.ipa [--output-dir ./output]
    python analyze_ipa.py target.ipa --extract-only
    python analyze_ipa.py target.ipa --decompile
"""

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List


class IPAAnalyzer:
    def __init__(self, ipa_path: str, output_dir: Optional[str] = None):
        self.ipa_path = Path(ipa_path).resolve()
        self.output_dir = Path(output_dir) if output_dir else self.ipa_path.parent / f"{self.ipa_path.stem}_analysis"
        self.extracted_dir = self.output_dir / "extracted"
        self.app_bundle = None  # Will be set after extraction
        self.report = {
            "ipa_name": self.ipa_path.name,
            "bundle_id": None,
            "app_name": None,
            "version": None,
            "min_ios_version": None,
            "hermes_detected": False,
            "hermes_version": None,
            "bundle_path": None,
            "bundle_size": 0,
            "architecture": {
                "archs": [],
                "simulator_compatible": False,
                "device_only": False,
            },
            "info_plist": {
                "ats_exceptions": [],
                "allows_arbitrary_loads": False,
                "url_schemes": [],
                "universal_links": [],
                "permissions": [],
            },
            "entitlements": {},
            "privacy_manifest": {
                "accessed_api_types": [],
                "tracking_domains": [],
                "collected_data_types": [],
            },
            "api_endpoints": [],
            "interesting_strings": [],
            "frameworks": [],
        }

    def run(self, extract_only: bool = False, decompile: bool = False, enhanced: bool = False):
        """Run the full analysis workflow."""
        print(f"[*] Analyzing: {self.ipa_path}")
        print(f"[*] Output directory: {self.output_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract IPA
        print("\n[1/9] Extracting IPA...")
        self.extract_ipa()

        if extract_only:
            print(f"\n[*] Extraction complete. Files at: {self.extracted_dir}")
            return

        # Step 2: Check binary architecture
        print("\n[2/9] Checking binary architecture...")
        self.check_architecture()

        # Step 3: Parse Info.plist
        print("\n[3/9] Parsing Info.plist...")
        self.parse_info_plist()

        # Step 4: Extract entitlements
        print("\n[4/9] Extracting entitlements...")
        self.extract_entitlements()

        # Step 5: Parse privacy manifest
        print("\n[5/9] Parsing privacy manifest...")
        self.parse_privacy_manifest()

        # Step 6: Identify Hermes bundle
        print("\n[6/9] Identifying Hermes bundle...")
        self.find_hermes_bundle()

        # Step 7: Extract strings and endpoints
        print("\n[7/9] Extracting strings and endpoints...")
        self.extract_strings()

        # Step 8: Enhanced secret scanning
        if enhanced and self.report["bundle_path"]:
            print("\n[8/9] Running enhanced secret scan...")
            self.run_enhanced_scan()
        else:
            print("\n[8/9] Skipping enhanced scan (use --enhanced to enable)")

        # Step 9: Decompile if requested
        if decompile and self.report["bundle_path"]:
            print("\n[9/9] Decompiling bundle...")
            self.decompile_bundle()
        else:
            print("\n[9/9] Skipping decompilation (use --decompile to enable)")

        # Generate report
        self.generate_report()

        print(f"\n[*] Analysis complete!")
        print(f"[*] Report saved to: {self.output_dir / 'report.json'}")

    def extract_ipa(self):
        """Extract IPA contents."""
        if self.extracted_dir.exists():
            shutil.rmtree(self.extracted_dir)

        with zipfile.ZipFile(self.ipa_path, 'r') as zf:
            zf.extractall(self.extracted_dir)

        # Find the .app bundle
        payload_dir = self.extracted_dir / "Payload"
        if payload_dir.exists():
            for item in payload_dir.iterdir():
                if item.suffix == ".app" and item.is_dir():
                    self.app_bundle = item
                    print(f"    [+] Found app bundle: {item.name}")
                    break

        if not self.app_bundle:
            print("    [!] No .app bundle found in IPA")

    def check_architecture(self):
        """Check binary architecture to determine simulator compatibility."""
        if not self.app_bundle:
            return

        # Find the main binary (same name as app bundle without .app)
        binary_name = self.app_bundle.stem
        binary_path = self.app_bundle / binary_name

        if not binary_path.exists():
            print(f"    [!] Binary not found: {binary_name}")
            return

        try:
            result = subprocess.run(
                ["lipo", "-info", str(binary_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout + result.stderr

            # Parse architectures
            if "Non-fat file" in output:
                # Single architecture
                match = re.search(r"is architecture: (\S+)", output)
                if match:
                    arch = match.group(1)
                    self.report["architecture"]["archs"] = [arch]
            else:
                # Fat binary
                match = re.search(r"are: (.+)$", output, re.MULTILINE)
                if match:
                    archs = match.group(1).split()
                    self.report["architecture"]["archs"] = archs

            # Determine compatibility
            archs = self.report["architecture"]["archs"]
            has_x86 = any("x86" in a for a in archs)
            has_sim_arm = "arm64" in archs and len(archs) > 1  # arm64 simulator is different from device arm64

            # Simple heuristic: App Store apps are device-only (single arm64)
            if archs == ["arm64"] and not has_x86:
                self.report["architecture"]["device_only"] = True
                self.report["architecture"]["simulator_compatible"] = False
                print(f"    [+] Architecture: arm64 (device only)")
                print("    [!] WARNING: This IPA cannot run in iOS Simulator")
            else:
                self.report["architecture"]["simulator_compatible"] = has_x86 or has_sim_arm
                print(f"    [+] Architectures: {', '.join(archs)}")
                if self.report["architecture"]["simulator_compatible"]:
                    print("    [+] Simulator compatible")

        except Exception as e:
            print(f"    [!] Failed to check architecture: {e}")

    def parse_info_plist(self):
        """Parse Info.plist for security-relevant settings."""
        if not self.app_bundle:
            return

        info_plist = self.app_bundle / "Info.plist"
        if not info_plist.exists():
            print("    [!] Info.plist not found")
            return

        try:
            with open(info_plist, 'rb') as f:
                plist = plistlib.load(f)

            # Basic app info
            self.report["bundle_id"] = plist.get("CFBundleIdentifier")
            self.report["app_name"] = plist.get("CFBundleDisplayName") or plist.get("CFBundleName")
            self.report["version"] = plist.get("CFBundleShortVersionString")
            self.report["min_ios_version"] = plist.get("MinimumOSVersion")

            print(f"    [+] Bundle ID: {self.report['bundle_id']}")
            print(f"    [+] App Name: {self.report['app_name']}")
            print(f"    [+] Version: {self.report['version']}")

            # App Transport Security
            ats = plist.get("NSAppTransportSecurity", {})
            if ats.get("NSAllowsArbitraryLoads"):
                self.report["info_plist"]["allows_arbitrary_loads"] = True
                print("    [!] ATS: Allows arbitrary HTTP loads (insecure)")

            exceptions = ats.get("NSExceptionDomains", {})
            for domain, config in exceptions.items():
                if config.get("NSExceptionAllowsInsecureHTTPLoads") or \
                   config.get("NSTemporaryExceptionAllowsInsecureHTTPLoads"):
                    self.report["info_plist"]["ats_exceptions"].append({
                        "domain": domain,
                        "allows_http": True
                    })
                    print(f"    [!] ATS exception: {domain} allows HTTP")

            # URL Schemes
            url_types = plist.get("CFBundleURLTypes", [])
            for url_type in url_types:
                schemes = url_type.get("CFBundleURLSchemes", [])
                for scheme in schemes:
                    self.report["info_plist"]["url_schemes"].append(scheme)
                    print(f"    [+] URL scheme: {scheme}://")

            # Universal Links (Associated Domains in entitlements, but domains here)
            associated_domains = plist.get("com.apple.developer.associated-domains", [])
            for domain in associated_domains:
                if domain.startswith("applinks:"):
                    self.report["info_plist"]["universal_links"].append(domain.replace("applinks:", ""))

            # Privacy permissions
            privacy_keys = {
                "NSCameraUsageDescription": "Camera",
                "NSMicrophoneUsageDescription": "Microphone",
                "NSPhotoLibraryUsageDescription": "Photo Library",
                "NSLocationWhenInUseUsageDescription": "Location (When In Use)",
                "NSLocationAlwaysUsageDescription": "Location (Always)",
                "NSContactsUsageDescription": "Contacts",
                "NSCalendarsUsageDescription": "Calendars",
                "NSFaceIDUsageDescription": "Face ID",
                "NSBluetoothAlwaysUsageDescription": "Bluetooth",
                "NSHealthShareUsageDescription": "Health (Read)",
                "NSHealthUpdateUsageDescription": "Health (Write)",
                "NSMotionUsageDescription": "Motion",
                "NSAppleMusicUsageDescription": "Apple Music",
                "NSSpeechRecognitionUsageDescription": "Speech Recognition",
                "NSLocalNetworkUsageDescription": "Local Network",
                "NSUserTrackingUsageDescription": "Tracking",
            }

            for key, name in privacy_keys.items():
                if key in plist:
                    self.report["info_plist"]["permissions"].append({
                        "name": name,
                        "key": key,
                        "description": plist[key]
                    })

            if self.report["info_plist"]["permissions"]:
                print(f"    [+] Privacy permissions: {len(self.report['info_plist']['permissions'])}")

            # Save full plist for reference
            plist_output = self.output_dir / "Info_parsed.json"
            with open(plist_output, 'w') as f:
                json.dump(self._plist_to_json(plist), f, indent=2)

        except Exception as e:
            print(f"    [!] Failed to parse Info.plist: {e}")

    def _plist_to_json(self, obj):
        """Convert plist types to JSON-serializable types."""
        if isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, dict):
            return {k: self._plist_to_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._plist_to_json(v) for v in obj]
        else:
            return obj

    def extract_entitlements(self):
        """Extract embedded entitlements from the binary."""
        if not self.app_bundle:
            return

        try:
            result = subprocess.run(
                ["codesign", "-d", "--entitlements", ":-", str(self.app_bundle)],
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                try:
                    entitlements = plistlib.loads(result.stdout)
                    self.report["entitlements"] = self._plist_to_json(entitlements)

                    # Save entitlements
                    ent_output = self.output_dir / "entitlements.json"
                    with open(ent_output, 'w') as f:
                        json.dump(self.report["entitlements"], f, indent=2)

                    # Highlight interesting entitlements
                    interesting = [
                        "com.apple.developer.associated-domains",
                        "keychain-access-groups",
                        "com.apple.developer.networking.wifi-info",
                        "com.apple.developer.devicecheck.appattest-environment",
                        "aps-environment",  # Push notifications
                        "com.apple.developer.in-app-payments",
                    ]

                    found = [k for k in interesting if k in entitlements]
                    if found:
                        print(f"    [+] Notable entitlements: {', '.join(found)}")

                    # Check for associated domains (universal links)
                    domains = entitlements.get("com.apple.developer.associated-domains", [])
                    for domain in domains:
                        if domain.startswith("applinks:"):
                            self.report["info_plist"]["universal_links"].append(
                                domain.replace("applinks:", "")
                            )
                            print(f"    [+] Universal link: {domain}")

                except Exception as e:
                    print(f"    [!] Failed to parse entitlements: {e}")
            else:
                print("    [!] No entitlements found (may be unsigned)")

        except Exception as e:
            print(f"    [!] Failed to extract entitlements: {e}")

    def parse_privacy_manifest(self):
        """Parse PrivacyInfo.xcprivacy (iOS 17+ privacy manifest)."""
        if not self.app_bundle:
            return

        # Search for privacy manifest in app bundle and frameworks
        privacy_manifests = list(self.app_bundle.rglob("PrivacyInfo.xcprivacy"))

        if not privacy_manifests:
            print("    [*] No privacy manifest found (optional for iOS <17)")
            return

        for manifest_path in privacy_manifests:
            print(f"    [+] Found privacy manifest: {manifest_path.relative_to(self.app_bundle)}")

            try:
                with open(manifest_path, 'rb') as f:
                    manifest = plistlib.load(f)

                # Privacy Accessed API Types
                accessed_apis = manifest.get("NSPrivacyAccessedAPITypes", [])
                for api in accessed_apis:
                    api_type = api.get("NSPrivacyAccessedAPIType", "")
                    reasons = api.get("NSPrivacyAccessedAPITypeReasons", [])
                    self.report["privacy_manifest"]["accessed_api_types"].append({
                        "api_type": api_type,
                        "reasons": reasons
                    })

                # Tracking Domains
                tracking_domains = manifest.get("NSPrivacyTrackingDomains", [])
                self.report["privacy_manifest"]["tracking_domains"].extend(tracking_domains)

                # Collected Data Types
                collected_data = manifest.get("NSPrivacyCollectedDataTypes", [])
                for data in collected_data:
                    self.report["privacy_manifest"]["collected_data_types"].append({
                        "data_type": data.get("NSPrivacyCollectedDataType", ""),
                        "linked_to_user": data.get("NSPrivacyCollectedDataTypeLinked", False),
                        "used_for_tracking": data.get("NSPrivacyCollectedDataTypeTracking", False),
                    })

            except Exception as e:
                print(f"    [!] Failed to parse privacy manifest: {e}")

        if self.report["privacy_manifest"]["accessed_api_types"]:
            print(f"    [+] Accessed API types: {len(self.report['privacy_manifest']['accessed_api_types'])}")
        if self.report["privacy_manifest"]["tracking_domains"]:
            print(f"    [!] Tracking domains: {self.report['privacy_manifest']['tracking_domains']}")
        if self.report["privacy_manifest"]["collected_data_types"]:
            print(f"    [+] Collected data types: {len(self.report['privacy_manifest']['collected_data_types'])}")

    def find_hermes_bundle(self):
        """Locate the Hermes bytecode bundle."""
        if not self.app_bundle:
            return

        bundle_names = [
            "main.jsbundle",
            "index.ios.bundle",
            "index.bundle",
            "app.bundle"
        ]

        for bundle_name in bundle_names:
            bundle_path = self.app_bundle / bundle_name
            if bundle_path.exists():
                self.report["bundle_path"] = str(bundle_path)
                self.report["bundle_size"] = bundle_path.stat().st_size

                # Check if it's Hermes bytecode
                with open(bundle_path, 'rb') as f:
                    magic = f.read(8)
                    # Hermes magic: 0xc61fbc03
                    if magic[:4] == b'\xc6\x1f\xbc\x03':
                        self.report["hermes_detected"] = True
                        print(f"    [+] Found Hermes bundle: {bundle_name}")
                        print(f"    [+] Size: {self.report['bundle_size']:,} bytes")

                        # Detect version using file command (most reliable)
                        version = self._detect_hermes_version(bundle_path)
                        if version:
                            self.report["hermes_version"] = self._get_hermes_version(version)
                            print(f"    [+] Bytecode version: {version}")
                    else:
                        print(f"    [+] Found JS bundle (not Hermes): {bundle_name}")
                return

        print("    [!] No JavaScript bundle found")

    def _detect_hermes_version(self, bundle_path: Path) -> Optional[int]:
        """Detect Hermes version using multiple methods."""
        version = None

        # Method 1: Use `file` command (most reliable)
        try:
            result = subprocess.run(
                ["file", str(bundle_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            match = re.search(r'Hermes JavaScript bytecode, version (\d+)', result.stdout)
            if match:
                version = int(match.group(1))
                return version
        except Exception:
            pass

        # Method 2: Parse header directly (fallback)
        try:
            with open(bundle_path, 'rb') as f:
                f.read(4)  # Skip magic
                raw_version = int.from_bytes(f.read(4), 'little')
                if raw_version < 200:
                    return raw_version
        except Exception:
            pass

        return version

    def _get_hermes_version(self, bytecode_version: int) -> Dict[str, Any]:
        """Map bytecode version to React Native version."""
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

        return {
            "bytecode_version": bytecode_version,
            "estimated_rn_version": version_map.get(bytecode_version, f"Unknown (bytecode v{bytecode_version})")
        }

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
                                                           'cloudflare', 'cdn', 'analytics', 'apple.com']):
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

    def run_enhanced_scan(self):
        """Run enhanced secret scanning for obfuscated secrets."""
        bundle_path = Path(self.report["bundle_path"])

        # Try to import and run enhanced scanner
        scripts_dir = Path(__file__).parent
        enhanced_scanner_path = scripts_dir / "enhanced_secret_scan.py"

        if enhanced_scanner_path.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(enhanced_scanner_path), str(bundle_path), "--json"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0 and result.stdout:
                    try:
                        enhanced_results = json.loads(result.stdout)

                        # Add to report
                        self.report["enhanced_scan"] = enhanced_results

                        # Count findings
                        total_findings = sum(
                            len(v) for v in enhanced_results.get("findings", {}).values()
                            if isinstance(v, list)
                        )

                        print(f"    [+] Enhanced scan found {total_findings} potential secrets")

                        # Save detailed results
                        enhanced_output = self.output_dir / "enhanced_scan_results.json"
                        with open(enhanced_output, 'w') as f:
                            json.dump(enhanced_results, f, indent=2)
                        print(f"    [+] Detailed results saved to: {enhanced_output}")

                    except json.JSONDecodeError:
                        print("    [!] Failed to parse enhanced scan output")
                else:
                    if result.stderr:
                        print(f"    [!] Enhanced scan error: {result.stderr[:200]}")

            except subprocess.TimeoutExpired:
                print("    [!] Enhanced scan timed out")
            except Exception as e:
                print(f"    [!] Enhanced scan failed: {e}")
        else:
            print("    [!] Enhanced scanner not found. Run: python scripts/enhanced_secret_scan.py --help")

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
        # Find frameworks
        frameworks_dir = self.app_bundle / "Frameworks" if self.app_bundle else None
        if frameworks_dir and frameworks_dir.exists():
            for fw in frameworks_dir.iterdir():
                if fw.suffix == ".framework":
                    self.report["frameworks"].append(fw.name)

        # Save report
        report_path = self.output_dir / "report.json"
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)

        # Print summary
        print("\n" + "=" * 65)
        print("IPA ANALYSIS SUMMARY")
        print("=" * 65)
        print(f"IPA: {self.report['ipa_name']}")
        print(f"Bundle ID: {self.report['bundle_id']}")
        print(f"App Name: {self.report['app_name']}")
        print(f"Version: {self.report['version']}")
        print(f"Min iOS: {self.report['min_ios_version']}")
        print()

        # Architecture
        print("Architecture:")
        archs = self.report['architecture']['archs']
        print(f"  Architectures: {', '.join(archs) if archs else 'Unknown'}")
        if self.report['architecture']['device_only']:
            print("  [!] DEVICE ONLY - Cannot run in iOS Simulator")
        elif self.report['architecture']['simulator_compatible']:
            print("  [+] Simulator compatible")
        print()

        # Hermes
        print("Hermes Analysis:")
        print(f"  Detected: {self.report['hermes_detected']}")
        if self.report['hermes_version']:
            print(f"  Version: {self.report['hermes_version']['estimated_rn_version']}")
        if self.report['bundle_size']:
            print(f"  Bundle Size: {self.report['bundle_size']:,} bytes")
        print()

        # Security findings
        print("Security Analysis:")
        if self.report['info_plist']['allows_arbitrary_loads']:
            print("  [!] ATS allows arbitrary HTTP loads")
        if self.report['info_plist']['ats_exceptions']:
            print(f"  [!] ATS exceptions: {len(self.report['info_plist']['ats_exceptions'])} domains")
        print(f"  URL schemes: {len(self.report['info_plist']['url_schemes'])}")
        print(f"  Universal links: {len(self.report['info_plist']['universal_links'])}")
        print(f"  Privacy permissions: {len(self.report['info_plist']['permissions'])}")
        print(f"  API endpoints found: {len(self.report['api_endpoints'])}")
        print(f"  Interesting strings: {len(self.report['interesting_strings'])}")
        print()

        # URL schemes
        if self.report['info_plist']['url_schemes']:
            print("URL Schemes (potential deep link attack surface):")
            for scheme in self.report['info_plist']['url_schemes']:
                print(f"  - {scheme}://")
            print()

        # Top endpoints
        if self.report['api_endpoints']:
            print("Top API Endpoints:")
            for url in self.report['api_endpoints'][:10]:
                print(f"  - {url}")
            print()

        # Interesting findings
        if self.report['interesting_strings']:
            print("Interesting Strings (review for secrets):")
            for item in self.report['interesting_strings'][:5]:
                print(f"  [{item['type']}] {item['value']}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze React Native / Hermes iOS IPAs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s target.ipa                    # Full analysis
  %(prog)s target.ipa --output-dir ./out # Custom output directory
  %(prog)s target.ipa --extract-only     # Just extract IPA
  %(prog)s target.ipa --decompile        # Include decompilation
  %(prog)s target.ipa --enhanced         # Include enhanced secret scanning
        """
    )
    parser.add_argument("ipa", help="Path to IPA file")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--extract-only", action="store_true", help="Only extract IPA contents")
    parser.add_argument("--decompile", action="store_true", help="Attempt to decompile Hermes bundle")
    parser.add_argument("--enhanced", action="store_true", help="Run enhanced secret scanning (detects obfuscated secrets)")

    args = parser.parse_args()

    if not os.path.exists(args.ipa):
        print(f"Error: IPA not found: {args.ipa}")
        sys.exit(1)

    analyzer = IPAAnalyzer(args.ipa, args.output_dir)
    analyzer.run(extract_only=args.extract_only, decompile=args.decompile, enhanced=args.enhanced)


if __name__ == "__main__":
    main()
