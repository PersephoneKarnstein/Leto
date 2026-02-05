#!/usr/bin/env python3
"""
Source Map Recovery Tool for React Native Apps

Detects and extracts source maps from React Native bundles.
Source maps can significantly improve reverse engineering by mapping
minified/bundled code back to original source files.

Usage:
    python sourcemap_recovery.py <bundle_or_directory>
    python sourcemap_recovery.py app.ipa --extract
    python sourcemap_recovery.py ./extracted_apk/ --extract --output ./sourcemaps/
"""

import argparse
import base64
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Optional, Dict, List, Any


class SourceMapRecovery:
    # React Native bundle names
    BUNDLE_NAMES = [
        "index.android.bundle",
        "index.ios.bundle",
        "main.jsbundle",
        "index.bundle",
        "app.bundle",
    ]

    # Source map file extensions
    SOURCEMAP_EXTENSIONS = [".map", ".js.map", ".bundle.map"]

    # Patterns for detecting source map references
    SOURCEMAP_URL_PATTERN = re.compile(
        rb'//[#@]\s*sourceMappingURL\s*=\s*(\S+)',
        re.MULTILINE
    )

    # Pattern for inline base64 source maps
    INLINE_SOURCEMAP_PATTERN = re.compile(
        rb'//[#@]\s*sourceMappingURL\s*=\s*data:application/json;(?:charset=[^;]+;)?base64,([A-Za-z0-9+/=]+)',
        re.MULTILINE
    )

    def __init__(self, target_path: str, output_dir: Optional[str] = None):
        self.target_path = Path(target_path)
        self.output_dir = Path(output_dir) if output_dir else self.target_path.parent / "sourcemaps"
        self.findings = {
            "bundles": [],
            "sourcemaps": [],
            "inline_maps": [],
            "external_refs": [],
            "debug_info": [],
        }

    def run(self, extract: bool = False) -> Dict[str, Any]:
        """Run source map detection and optional extraction."""
        print(f"[*] Scanning: {self.target_path}")

        if self.target_path.is_file():
            if self.target_path.suffix.lower() in [".apk", ".ipa", ".zip"]:
                self._scan_archive(self.target_path)
            else:
                self._scan_file(self.target_path)
        elif self.target_path.is_dir():
            self._scan_directory(self.target_path)
        else:
            print(f"[!] Target not found: {self.target_path}")
            return self.findings

        self._print_findings()

        if extract:
            self._extract_sourcemaps()

        return self.findings

    def _scan_archive(self, archive_path: Path):
        """Scan APK/IPA archive for source maps."""
        print(f"[*] Scanning archive: {archive_path.name}")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for name in zf.namelist():
                    # Check for bundle files
                    basename = os.path.basename(name)
                    if basename in self.BUNDLE_NAMES:
                        print(f"    [+] Found bundle: {name}")
                        self.findings["bundles"].append({
                            "path": name,
                            "archive": str(archive_path),
                            "size": zf.getinfo(name).file_size,
                        })

                        # Check bundle content for source map references
                        with zf.open(name) as f:
                            content = f.read()
                            self._check_bundle_content(content, name, str(archive_path))

                    # Check for standalone source map files
                    if any(name.endswith(ext) for ext in self.SOURCEMAP_EXTENSIONS):
                        info = zf.getinfo(name)
                        print(f"    [+] Found source map: {name} ({info.file_size:,} bytes)")
                        self.findings["sourcemaps"].append({
                            "path": name,
                            "archive": str(archive_path),
                            "size": info.file_size,
                        })

                    # Check for debug/development indicators
                    if any(x in name.lower() for x in ["debug", "dev", ".map", "sourcemap"]):
                        if name not in [s["path"] for s in self.findings["sourcemaps"]]:
                            self.findings["debug_info"].append({
                                "path": name,
                                "archive": str(archive_path),
                            })

        except zipfile.BadZipFile:
            print(f"[!] Invalid archive: {archive_path}")

    def _scan_directory(self, dir_path: Path):
        """Recursively scan directory for source maps."""
        print(f"[*] Scanning directory: {dir_path}")

        for root, dirs, files in os.walk(dir_path):
            # Skip common non-relevant directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]

            for filename in files:
                filepath = Path(root) / filename

                # Check for bundle files
                if filename in self.BUNDLE_NAMES:
                    print(f"    [+] Found bundle: {filepath.relative_to(dir_path)}")
                    self.findings["bundles"].append({
                        "path": str(filepath),
                        "size": filepath.stat().st_size,
                    })

                    # Check bundle content
                    try:
                        content = filepath.read_bytes()
                        self._check_bundle_content(content, str(filepath))
                    except Exception as e:
                        print(f"    [!] Failed to read {filepath}: {e}")

                # Check for standalone source map files
                if any(filename.endswith(ext) for ext in self.SOURCEMAP_EXTENSIONS):
                    size = filepath.stat().st_size
                    print(f"    [+] Found source map: {filepath.relative_to(dir_path)} ({size:,} bytes)")
                    self.findings["sourcemaps"].append({
                        "path": str(filepath),
                        "size": size,
                    })

    def _scan_file(self, file_path: Path):
        """Scan a single file for source map references."""
        print(f"[*] Scanning file: {file_path}")

        try:
            content = file_path.read_bytes()
            self._check_bundle_content(content, str(file_path))

            self.findings["bundles"].append({
                "path": str(file_path),
                "size": file_path.stat().st_size,
            })
        except Exception as e:
            print(f"[!] Failed to read {file_path}: {e}")

    def _check_bundle_content(self, content: bytes, path: str, archive: Optional[str] = None):
        """Check bundle content for source map references."""

        # Check for inline base64 source maps
        inline_matches = self.INLINE_SOURCEMAP_PATTERN.findall(content)
        for match in inline_matches:
            try:
                decoded_size = len(base64.b64decode(match))
                print(f"    [+] Found INLINE source map in {os.path.basename(path)} ({decoded_size:,} bytes)")
                self.findings["inline_maps"].append({
                    "bundle_path": path,
                    "archive": archive,
                    "encoded_size": len(match),
                    "decoded_size": decoded_size,
                    "data": match.decode('ascii'),
                })
            except Exception:
                pass

        # Check for external source map URLs
        url_matches = self.SOURCEMAP_URL_PATTERN.findall(content)
        for match in url_matches:
            url = match.decode('utf-8', errors='ignore').strip()
            # Skip if it's an inline map (already handled)
            if url.startswith('data:'):
                continue

            print(f"    [+] Found source map reference: {url}")
            self.findings["external_refs"].append({
                "bundle_path": path,
                "archive": archive,
                "url": url,
            })

        # Check for React Native debug mode indicators
        debug_indicators = [
            b'__DEV__',
            b'__BUNDLE_START_TIME__',
            b'sourceMapUrl',
            b'debuggerWorker',
            b'HMRClient',  # Hot Module Replacement
            b'localhost:8081',  # Metro bundler
        ]

        for indicator in debug_indicators:
            if indicator in content:
                if not any(d.get("indicator") == indicator.decode()
                          for d in self.findings["debug_info"]
                          if d.get("bundle_path") == path):
                    self.findings["debug_info"].append({
                        "bundle_path": path,
                        "archive": archive,
                        "indicator": indicator.decode(),
                    })

    def _print_findings(self):
        """Print summary of findings."""
        print("\n" + "=" * 60)
        print("SOURCE MAP RECOVERY SUMMARY")
        print("=" * 60)

        print(f"\nBundles found: {len(self.findings['bundles'])}")
        for b in self.findings['bundles']:
            print(f"  - {b['path']} ({b['size']:,} bytes)")

        if self.findings['sourcemaps']:
            print(f"\nStandalone source maps: {len(self.findings['sourcemaps'])}")
            for s in self.findings['sourcemaps']:
                print(f"  - {s['path']} ({s['size']:,} bytes)")

        if self.findings['inline_maps']:
            print(f"\nInline source maps: {len(self.findings['inline_maps'])}")
            for m in self.findings['inline_maps']:
                print(f"  - In {os.path.basename(m['bundle_path'])} ({m['decoded_size']:,} bytes)")

        if self.findings['external_refs']:
            print(f"\nExternal source map references: {len(self.findings['external_refs'])}")
            for r in self.findings['external_refs']:
                print(f"  - {r['url']}")

        if self.findings['debug_info']:
            indicators = set(d.get('indicator', d.get('path', '')) for d in self.findings['debug_info'])
            print(f"\nDebug indicators found: {len(indicators)}")
            for i in sorted(indicators):
                print(f"  - {i}")

        # Assessment
        print("\n" + "-" * 60)
        if self.findings['sourcemaps'] or self.findings['inline_maps']:
            print("[!] SOURCE MAPS AVAILABLE - High-value for reverse engineering!")
            print("    Use --extract to save source maps for analysis")
        elif self.findings['external_refs']:
            print("[*] External source map references found")
            print("    Try fetching from referenced URLs (may require debug build)")
        elif self.findings['debug_info']:
            print("[*] Debug indicators present - app may be debug build")
            print("    Source maps might be available on Metro bundler (localhost:8081)")
        else:
            print("[*] No source maps detected - release build with maps stripped")

    def _extract_sourcemaps(self):
        """Extract found source maps to output directory."""
        if not (self.findings['sourcemaps'] or self.findings['inline_maps']):
            print("\n[!] No source maps to extract")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[*] Extracting source maps to: {self.output_dir}")

        # Extract standalone source maps from archives
        for sm in self.findings['sourcemaps']:
            if sm.get('archive'):
                try:
                    with zipfile.ZipFile(sm['archive'], 'r') as zf:
                        basename = os.path.basename(sm['path'])
                        output_path = self.output_dir / basename
                        with zf.open(sm['path']) as src, open(output_path, 'wb') as dst:
                            dst.write(src.read())
                        print(f"    [+] Extracted: {basename}")
                        self._analyze_sourcemap(output_path)
                except Exception as e:
                    print(f"    [!] Failed to extract {sm['path']}: {e}")
            else:
                # Copy from filesystem
                try:
                    src_path = Path(sm['path'])
                    dst_path = self.output_dir / src_path.name
                    dst_path.write_bytes(src_path.read_bytes())
                    print(f"    [+] Copied: {src_path.name}")
                    self._analyze_sourcemap(dst_path)
                except Exception as e:
                    print(f"    [!] Failed to copy {sm['path']}: {e}")

        # Extract inline source maps
        for idx, im in enumerate(self.findings['inline_maps']):
            try:
                decoded = base64.b64decode(im['data'])
                bundle_name = os.path.basename(im['bundle_path'])
                output_path = self.output_dir / f"{bundle_name}.map"
                output_path.write_bytes(decoded)
                print(f"    [+] Extracted inline map: {output_path.name}")
                self._analyze_sourcemap(output_path)
            except Exception as e:
                print(f"    [!] Failed to extract inline map {idx}: {e}")

    def _analyze_sourcemap(self, map_path: Path):
        """Analyze extracted source map and print summary."""
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            sources = data.get('sources', [])
            if sources:
                print(f"        Sources: {len(sources)} files")

                # Categorize sources
                categories = {
                    'app': [],
                    'node_modules': [],
                    'react-native': [],
                    'other': [],
                }

                for src in sources:
                    if 'node_modules' in src:
                        if 'react-native' in src:
                            categories['react-native'].append(src)
                        else:
                            categories['node_modules'].append(src)
                    elif src.startswith(('src/', 'app/', 'lib/', './src', './app')):
                        categories['app'].append(src)
                    else:
                        categories['other'].append(src)

                if categories['app']:
                    print(f"        App source files: {len(categories['app'])}")
                    for src in categories['app'][:5]:
                        print(f"          - {src}")
                    if len(categories['app']) > 5:
                        print(f"          ... and {len(categories['app']) - 5} more")

                if categories['node_modules']:
                    print(f"        Dependencies: {len(categories['node_modules'])} files")

            # Check for sourcesContent (actual source code)
            sources_content = data.get('sourcesContent', [])
            if sources_content:
                non_null = sum(1 for s in sources_content if s)
                print(f"        Source content included: {non_null}/{len(sources_content)} files")

        except Exception as e:
            print(f"        [!] Failed to analyze: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Detect and extract source maps from React Native apps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s app.apk                    # Scan APK for source maps
  %(prog)s app.ipa --extract          # Scan IPA and extract maps
  %(prog)s ./extracted/ --extract     # Scan directory
  %(prog)s bundle.js --output ./maps  # Scan bundle, save to custom dir
        """
    )
    parser.add_argument("target", help="APK, IPA, bundle file, or directory to scan")
    parser.add_argument("--extract", "-e", action="store_true",
                        help="Extract found source maps")
    parser.add_argument("--output", "-o", help="Output directory for extracted maps")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not os.path.exists(args.target):
        print(f"Error: Target not found: {args.target}")
        sys.exit(1)

    recovery = SourceMapRecovery(args.target, args.output)
    findings = recovery.run(extract=args.extract)

    if args.json:
        # Remove non-serializable data
        output = {k: v for k, v in findings.items() if k != 'inline_maps'}
        if findings['inline_maps']:
            output['inline_maps'] = [
                {k: v for k, v in m.items() if k != 'data'}
                for m in findings['inline_maps']
            ]
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
