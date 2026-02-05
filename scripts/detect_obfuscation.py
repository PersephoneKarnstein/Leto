#!/usr/bin/env python3
"""
Obfuscation Detection for React Native Apps

Detects common obfuscation techniques used in React Native apps:
- Metro minification
- JavaScript obfuscators (javascript-obfuscator, react-native-obfuscating-transformer)
- Hermes bytecode (inherent obfuscation)
- ProGuard/R8 (Android native code)
- String encryption
- Control flow flattening

Usage:
    python detect_obfuscation.py <apk_or_ipa_or_bundle>
    python detect_obfuscation.py ./extracted_apk/
    python detect_obfuscation.py bundle.js --verbose
"""

import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Optional


class ObfuscationDetector:
    def __init__(self, target_path: str, verbose: bool = False):
        self.target_path = Path(target_path)
        self.verbose = verbose
        self.findings = {
            "target": str(target_path),
            "bundle_type": None,
            "obfuscation_detected": [],
            "obfuscation_level": "unknown",
            "details": {},
            "recommendations": [],
        }

    def run(self) -> Dict[str, Any]:
        """Run obfuscation detection."""
        print(f"[*] Analyzing: {self.target_path}")

        if self.target_path.is_file():
            if self.target_path.suffix.lower() in [".apk", ".ipa", ".zip"]:
                self._analyze_archive()
            else:
                self._analyze_bundle(self.target_path)
        elif self.target_path.is_dir():
            self._analyze_directory()
        else:
            print(f"[!] Target not found: {self.target_path}")
            return self.findings

        self._assess_level()
        self._generate_recommendations()
        self._print_report()

        return self.findings

    def _analyze_archive(self):
        """Analyze APK/IPA archive."""
        print(f"[*] Scanning archive...")

        try:
            with zipfile.ZipFile(self.target_path, 'r') as zf:
                # Find bundle
                bundle_names = [
                    "assets/index.android.bundle",
                    "Payload/*/main.jsbundle",
                    "main.jsbundle",
                ]

                for name in zf.namelist():
                    basename = os.path.basename(name)

                    # Check for bundle
                    if basename in ["index.android.bundle", "main.jsbundle", "index.bundle"]:
                        print(f"    [+] Found bundle: {name}")
                        with zf.open(name) as f:
                            content = f.read()
                            self._analyze_bundle_content(content, name)

                    # Check for ProGuard mapping (Android)
                    if basename == "mapping.txt" or "proguard" in name.lower():
                        self.findings["obfuscation_detected"].append("proguard_mapping_present")
                        self.findings["details"]["proguard_mapping"] = name

                    # Check for native libraries
                    if name.endswith(".so"):
                        self._check_native_lib(zf, name)

        except zipfile.BadZipFile:
            print(f"[!] Invalid archive")

    def _analyze_directory(self):
        """Analyze extracted app directory."""
        print(f"[*] Scanning directory...")

        bundle_names = ["index.android.bundle", "main.jsbundle", "index.bundle", "app.bundle"]

        for root, dirs, files in os.walk(self.target_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]

            for filename in files:
                if filename in bundle_names:
                    filepath = Path(root) / filename
                    print(f"    [+] Found bundle: {filepath.relative_to(self.target_path)}")
                    self._analyze_bundle(filepath)

                if filename == "mapping.txt":
                    self.findings["obfuscation_detected"].append("proguard_mapping_present")

    def _analyze_bundle(self, bundle_path: Path):
        """Analyze a bundle file."""
        content = bundle_path.read_bytes()
        self._analyze_bundle_content(content, str(bundle_path))

    def _analyze_bundle_content(self, content: bytes, name: str):
        """Analyze bundle content for obfuscation indicators."""

        # Check if Hermes bytecode
        if content[:4] == b'\xc6\x1f\xbc\x03':
            self.findings["bundle_type"] = "hermes_bytecode"
            self.findings["obfuscation_detected"].append("hermes_bytecode")
            self.findings["details"]["hermes"] = {
                "version": int.from_bytes(content[4:8], 'little'),
                "note": "Hermes bytecode provides inherent obfuscation - source recovery limited"
            }
            # Can't analyze bytecode further for JS obfuscation
            return

        self.findings["bundle_type"] = "javascript"

        # Decode for text analysis
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            text = content.decode('latin-1', errors='ignore')

        # Check minification level
        self._check_minification(text)

        # Check for javascript-obfuscator patterns
        self._check_js_obfuscator(text)

        # Check for react-native-obfuscating-transformer
        self._check_rn_obfuscator(text)

        # Check for string encoding
        self._check_string_encoding(text)

        # Check for control flow obfuscation
        self._check_control_flow(text)

        # Check for dead code injection
        self._check_dead_code(text)

        # Analyze identifier patterns
        self._analyze_identifiers(text)

    def _check_minification(self, text: str):
        """Check minification level."""
        # Count newlines vs file size
        lines = text.count('\n')
        size = len(text)

        if size > 0:
            chars_per_line = size / max(lines, 1)

            if chars_per_line > 5000:
                self.findings["obfuscation_detected"].append("heavy_minification")
                self.findings["details"]["minification"] = "heavy"
            elif chars_per_line > 1000:
                self.findings["obfuscation_detected"].append("standard_minification")
                self.findings["details"]["minification"] = "standard"
            else:
                self.findings["details"]["minification"] = "light_or_none"

            if self.verbose:
                print(f"    [*] Chars/line: {chars_per_line:.0f}")

    def _check_js_obfuscator(self, text: str):
        """Check for javascript-obfuscator patterns."""
        indicators = []

        # Hex string arrays (common pattern)
        hex_array_pattern = r'\[(["\']0x[0-9a-f]+["\'],?\s*){10,}\]'
        if re.search(hex_array_pattern, text, re.I):
            indicators.append("hex_string_array")

        # Obfuscated function calls like _0x1234()
        obf_func_pattern = r'_0x[0-9a-f]{4,}\s*\('
        matches = re.findall(obf_func_pattern, text)
        if len(matches) > 50:
            indicators.append("obfuscated_function_names")

        # Self-defending code
        if 'selfDefending' in text or 'debugProtection' in text:
            indicators.append("self_defending_code")

        # Domain lock
        if 'domainLock' in text:
            indicators.append("domain_lock")

        if indicators:
            self.findings["obfuscation_detected"].append("javascript_obfuscator")
            self.findings["details"]["javascript_obfuscator"] = {
                "indicators": indicators,
                "tool": "javascript-obfuscator (probable)"
            }

    def _check_rn_obfuscator(self, text: str):
        """Check for react-native-obfuscating-transformer."""
        indicators = []

        # RNOT uses specific patterns
        # Check for string array rotation
        rotation_pattern = r'while\s*\(\s*!!\s*\[\s*\]\s*\)'
        if re.search(rotation_pattern, text):
            indicators.append("string_array_rotation")

        # Check for encoded require paths
        encoded_require = r'require\s*\(\s*["\'][^"\']*\\x[0-9a-f]{2}'
        if re.search(encoded_require, text, re.I):
            indicators.append("encoded_require_paths")

        if indicators:
            self.findings["obfuscation_detected"].append("rn_obfuscating_transformer")
            self.findings["details"]["rn_obfuscator"] = {
                "indicators": indicators,
                "tool": "react-native-obfuscating-transformer (probable)"
            }

    def _check_string_encoding(self, text: str):
        """Check for string encoding techniques."""
        indicators = []

        # Base64 encoded strings (excessive)
        base64_pattern = r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']'
        b64_matches = re.findall(base64_pattern, text)
        if len(b64_matches) > 20:
            indicators.append(f"base64_strings ({len(b64_matches)} found)")

        # Hex encoded strings
        hex_string_pattern = r'["\']\\x[0-9a-f]{2}(?:\\x[0-9a-f]{2}){5,}["\']'
        hex_matches = re.findall(hex_string_pattern, text, re.I)
        if len(hex_matches) > 10:
            indicators.append(f"hex_encoded_strings ({len(hex_matches)} found)")

        # Unicode escape sequences (excessive)
        unicode_pattern = r'\\u[0-9a-f]{4}'
        unicode_count = len(re.findall(unicode_pattern, text, re.I))
        if unicode_count > 500:
            indicators.append(f"unicode_escapes ({unicode_count} found)")

        # String array with decoder function
        if re.search(r'function\s*\w*\s*\(\s*\w+\s*,\s*\w+\s*\)\s*\{[^}]*parseInt', text):
            indicators.append("string_decoder_function")

        if indicators:
            self.findings["obfuscation_detected"].append("string_encoding")
            self.findings["details"]["string_encoding"] = indicators

    def _check_control_flow(self, text: str):
        """Check for control flow obfuscation."""
        indicators = []

        # Switch-based control flow flattening
        switch_pattern = r'switch\s*\([^)]+\)\s*\{(?:[^{}]|\{[^{}]*\})*case\s+["\']?\d+["\']?\s*:'
        switch_matches = re.findall(switch_pattern, text)
        if len(switch_matches) > 20:
            indicators.append(f"switch_flattening ({len(switch_matches)} switches)")

        # While-true with switch (classic CFG flattening)
        cfg_pattern = r'while\s*\(\s*(?:true|!0|1)\s*\)\s*\{[^{}]*switch'
        if re.search(cfg_pattern, text):
            indicators.append("cfg_flattening")

        # Opaque predicates
        opaque_pattern = r'if\s*\(\s*(?:!0|!1|true|false)\s*\)'
        if len(re.findall(opaque_pattern, text)) > 10:
            indicators.append("opaque_predicates")

        if indicators:
            self.findings["obfuscation_detected"].append("control_flow_obfuscation")
            self.findings["details"]["control_flow"] = indicators

    def _check_dead_code(self, text: str):
        """Check for dead code injection."""
        indicators = []

        # Unreachable code patterns
        unreachable_pattern = r'if\s*\(\s*false\s*\)\s*\{[^}]+\}'
        if re.search(unreachable_pattern, text):
            indicators.append("unreachable_blocks")

        # Empty functions (often injected)
        empty_func_pattern = r'function\s+\w+\s*\([^)]*\)\s*\{\s*\}'
        empty_count = len(re.findall(empty_func_pattern, text))
        if empty_count > 50:
            indicators.append(f"empty_functions ({empty_count} found)")

        if indicators:
            self.findings["obfuscation_detected"].append("dead_code_injection")
            self.findings["details"]["dead_code"] = indicators

    def _analyze_identifiers(self, text: str):
        """Analyze identifier naming patterns."""
        # Extract identifiers
        id_pattern = r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)\b'
        identifiers = re.findall(id_pattern, text)

        # Filter common keywords
        keywords = {'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while',
                    'return', 'this', 'new', 'true', 'false', 'null', 'undefined',
                    'require', 'exports', 'module', 'Object', 'Array', 'String'}
        identifiers = [i for i in identifiers if i not in keywords and len(i) > 1]

        if not identifiers:
            return

        # Count patterns
        short_ids = sum(1 for i in identifiers if len(i) <= 2)
        hex_ids = sum(1 for i in identifiers if re.match(r'^_?0x[0-9a-f]+$', i, re.I))
        underscore_ids = sum(1 for i in identifiers if i.startswith('_') and len(i) > 3)

        total = len(identifiers)
        unique = len(set(identifiers))

        analysis = {
            "total_identifiers": total,
            "unique_identifiers": unique,
            "short_identifiers_pct": round(short_ids / total * 100, 1) if total else 0,
            "hex_identifiers_pct": round(hex_ids / total * 100, 1) if total else 0,
        }

        if analysis["short_identifiers_pct"] > 60:
            self.findings["obfuscation_detected"].append("aggressive_identifier_mangling")
        elif analysis["hex_identifiers_pct"] > 20:
            self.findings["obfuscation_detected"].append("hex_identifier_pattern")

        self.findings["details"]["identifiers"] = analysis

    def _check_native_lib(self, zf, name: str):
        """Check native library for obfuscation indicators."""
        # Could analyze with capstone/lief but keeping simple for now
        if "libreactnative" in name.lower():
            # Check file size as rough indicator
            info = zf.getinfo(name)
            if info.file_size < 100000:  # Very small for RN
                self.findings["details"].setdefault("native_libs", []).append({
                    "name": name,
                    "note": "Unusually small - may be stripped"
                })

    def _assess_level(self):
        """Assess overall obfuscation level."""
        detected = self.findings["obfuscation_detected"]

        if "hermes_bytecode" in detected:
            base_level = 2  # Bytecode is moderate obfuscation by default
        else:
            base_level = 0

        # Add points for each technique
        points = {
            "javascript_obfuscator": 3,
            "rn_obfuscating_transformer": 3,
            "control_flow_obfuscation": 2,
            "string_encoding": 2,
            "dead_code_injection": 1,
            "aggressive_identifier_mangling": 2,
            "hex_identifier_pattern": 1,
            "heavy_minification": 1,
            "standard_minification": 0,
        }

        score = base_level + sum(points.get(d, 0) for d in detected)

        if score <= 1:
            self.findings["obfuscation_level"] = "minimal"
        elif score <= 3:
            self.findings["obfuscation_level"] = "light"
        elif score <= 5:
            self.findings["obfuscation_level"] = "moderate"
        elif score <= 7:
            self.findings["obfuscation_level"] = "heavy"
        else:
            self.findings["obfuscation_level"] = "extreme"

        self.findings["details"]["obfuscation_score"] = score

    def _generate_recommendations(self):
        """Generate recommendations based on findings."""
        detected = self.findings["obfuscation_detected"]
        recs = []

        if "hermes_bytecode" in detected:
            recs.append({
                "issue": "Hermes bytecode",
                "approach": "Use hbc-decompiler or r2hermes for disassembly. Full source recovery not possible.",
                "tools": ["hbc-decompiler", "r2hermes", "hbctool"]
            })

        if "javascript_obfuscator" in detected:
            recs.append({
                "issue": "JavaScript obfuscator detected",
                "approach": "Use de4js, synchrony, or manual analysis. Focus on runtime hooking.",
                "tools": ["de4js", "synchrony", "frida"]
            })

        if "string_encoding" in detected:
            recs.append({
                "issue": "Encoded strings",
                "approach": "Use Frida to hook string decoder functions at runtime.",
                "tools": ["frida", "runtime string extraction"]
            })

        if "control_flow_obfuscation" in detected:
            recs.append({
                "issue": "Control flow flattening",
                "approach": "Use symbolic execution or manual CFG reconstruction.",
                "tools": ["Manual analysis", "CFG tools"]
            })

        if not detected or detected == ["standard_minification"]:
            recs.append({
                "issue": "Minimal obfuscation",
                "approach": "Standard analysis should work. Use prettier for formatting.",
                "tools": ["prettier", "js-beautify"]
            })

        self.findings["recommendations"] = recs

    def _print_report(self):
        """Print analysis report."""
        print("\n" + "=" * 60)
        print("OBFUSCATION DETECTION REPORT")
        print("=" * 60)

        print(f"\nTarget: {self.findings['target']}")
        print(f"Bundle Type: {self.findings['bundle_type']}")
        print(f"Obfuscation Level: {self.findings['obfuscation_level'].upper()}")

        if self.findings["obfuscation_detected"]:
            print(f"\nTechniques Detected ({len(self.findings['obfuscation_detected'])}):")
            for technique in self.findings["obfuscation_detected"]:
                print(f"  - {technique}")

                # Show details if available
                key = technique.replace("_detected", "")
                if key in self.findings["details"]:
                    detail = self.findings["details"][key]
                    if isinstance(detail, dict):
                        for k, v in detail.items():
                            print(f"      {k}: {v}")
                    elif isinstance(detail, list):
                        for item in detail[:5]:
                            print(f"      - {item}")
        else:
            print("\nNo significant obfuscation detected.")

        if self.findings["recommendations"]:
            print("\nRecommendations:")
            for rec in self.findings["recommendations"]:
                print(f"\n  [{rec['issue']}]")
                print(f"    Approach: {rec['approach']}")
                print(f"    Tools: {', '.join(rec['tools'])}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Detect obfuscation in React Native apps",
    )
    parser.add_argument("target", help="APK, IPA, bundle file, or directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not Path(args.target).exists():
        print(f"Error: Target not found: {args.target}")
        sys.exit(1)

    detector = ObfuscationDetector(args.target, verbose=args.verbose)
    result = detector.run()

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
