#!/usr/bin/env python3
"""
Enhanced Secret Scanner for Hermes Bundles

Detects obfuscated secrets using multiple techniques:
- Direct pattern matching
- Base64 decoding
- Hex string decoding
- Character code array detection
- Split string fragment detection
- Anti-tampering code detection

Usage:
    python enhanced_secret_scan.py path/to/bundle.hbc
    python enhanced_secret_scan.py path/to/bundle.hbc --json
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


class EnhancedSecretScanner:
    def __init__(self, bundle_path: str):
        self.bundle_path = Path(bundle_path)
        with open(self.bundle_path, 'rb') as f:
            self.content_bytes = f.read()
        self.content = self.content_bytes.decode('utf-8', errors='ignore')
        self.findings: Dict[str, List[Dict[str, Any]]] = {
            'direct_secrets': [],
            'base64_encoded': [],
            'hex_encoded': [],
            'char_code_arrays': [],
            'split_fragments': [],
            'anti_tampering': [],
            'endpoints': [],
        }

    def scan_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run all scanning techniques."""
        self.scan_direct_secrets()
        self.scan_base64_encoded()
        self.scan_hex_encoded()
        self.scan_char_code_arrays()
        self.scan_split_fragments()
        self.scan_anti_tampering()
        self.scan_endpoints()
        return self.findings

    def scan_direct_secrets(self):
        """Scan for secrets using direct pattern matching."""
        patterns = {
            'aws_access_key': (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
            'aws_secret_key': (r'(?:aws_secret|AWS_SECRET|secret_key)["\s:=]+["\']?([A-Za-z0-9/+=]{40})["\']?', 'AWS Secret Key'),
            'jwt_token': (r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', 'JWT Token'),
            'stripe_key': (r'sk_(?:test|live)_[a-zA-Z0-9]{24,}', 'Stripe Secret Key'),
            'stripe_pk': (r'pk_(?:test|live)_[a-zA-Z0-9]{24,}', 'Stripe Publishable Key'),
            'firebase_key': (r'AIza[a-zA-Z0-9_-]{35}', 'Firebase/Google API Key'),
            'github_token': (r'gh[pousr]_[a-zA-Z0-9]{36,}', 'GitHub Token'),
            'sendgrid_key': (r'SG\.[a-zA-Z0-9_-]{22,}', 'SendGrid API Key'),
            'oauth_secret': (r'GOCSPX-[a-zA-Z0-9_-]{28}', 'Google OAuth Client Secret'),
            'private_key': (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', 'Private Key Header'),
            'database_url': (r'(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s"\'<>]+', 'Database Connection URL'),
            'slack_webhook': (r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[a-zA-Z0-9]+', 'Slack Webhook'),
            'heroku_api': (r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', 'Possible Heroku API Key'),
            'generic_api_key': (r'(?:api[_-]?key|apikey|api_secret)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?', 'Generic API Key'),
            'md5_hash': (r'\b[a-fA-F0-9]{32}\b', 'MD5 Hash'),
            'sha256_hash': (r'\b[a-fA-F0-9]{64}\b', 'SHA256 Hash'),
        }

        for name, (pattern, description) in patterns.items():
            for match in re.finditer(pattern, self.content, re.IGNORECASE):
                value = match.group(1) if match.lastindex else match.group()
                # Skip common false positives
                if self._is_likely_false_positive(value, name):
                    continue
                self.findings['direct_secrets'].append({
                    'type': name,
                    'description': description,
                    'value': value[:100] + '...' if len(value) > 100 else value,
                    'position': match.start(),
                })

    def scan_base64_encoded(self):
        """Scan for Base64 encoded strings and decode them."""
        # Look for Base64 patterns that might be secrets
        b64_pattern = re.compile(r'["\']([A-Za-z0-9+/]{20,}={0,2})["\']')

        interesting_keywords = [
            'api', 'key', 'secret', 'password', 'token', 'auth',
            'http', 'https', 'admin', 'aws', 'slack', 'github',
            'bearer', 'credential', 'firebase', 'database'
        ]

        for match in b64_pattern.finditer(self.content):
            b64_str = match.group(1)
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                # Check if decoded content looks interesting
                if any(kw in decoded.lower() for kw in interesting_keywords) or self._looks_like_secret(decoded):
                    self.findings['base64_encoded'].append({
                        'type': 'base64_secret',
                        'encoded': b64_str[:50] + '...' if len(b64_str) > 50 else b64_str,
                        'decoded': decoded[:100] + '...' if len(decoded) > 100 else decoded,
                        'position': match.start(),
                    })
            except Exception:
                pass

    def scan_hex_encoded(self):
        """Scan for hex-encoded strings and decode them."""
        # Look for hex strings in quotes or assignments
        hex_pattern = re.compile(r'["\']([0-9a-fA-F]{20,})["\']')

        for match in hex_pattern.finditer(self.content):
            hex_str = match.group(1)
            if len(hex_str) % 2 != 0:
                continue
            try:
                decoded = bytes.fromhex(hex_str).decode('utf-8', errors='ignore')
                if decoded and len(decoded) > 5 and decoded.isprintable():
                    self.findings['hex_encoded'].append({
                        'type': 'hex_secret',
                        'encoded': hex_str[:50] + '...' if len(hex_str) > 50 else hex_str,
                        'decoded': decoded[:100] + '...' if len(decoded) > 100 else decoded,
                        'position': match.start(),
                    })
            except Exception:
                pass

    def scan_char_code_arrays(self):
        """Scan for character code arrays like [65, 75, 73, ...]."""
        # Pattern for arrays of numbers
        array_pattern = re.compile(r'\[\s*(\d+(?:\s*,\s*\d+){4,})\s*\]')

        for match in array_pattern.finditer(self.content):
            arr_str = match.group(1)
            try:
                nums = [int(x.strip()) for x in arr_str.split(',')]
                # Check if numbers are in printable ASCII range
                if all(32 <= n <= 126 for n in nums):
                    decoded = ''.join(chr(n) for n in nums)
                    if len(decoded) >= 5 and self._looks_like_secret(decoded):
                        self.findings['char_code_arrays'].append({
                            'type': 'char_array',
                            'array': f'[{arr_str[:50]}...]' if len(arr_str) > 50 else f'[{arr_str}]',
                            'decoded': decoded,
                            'position': match.start(),
                        })
            except Exception:
                pass

    def scan_split_fragments(self):
        """Scan for fragments of split secrets."""
        fragments = {
            'aws_key_prefix': ('AKIA', 'AWS Access Key prefix'),
            'jwt_header': ('eyJhbG', 'JWT header fragment'),
            'github_prefix': ('ghp_', 'GitHub token prefix'),
            'stripe_prefix': ('sk_test_', 'Stripe test key prefix'),
            'stripe_live': ('sk_live_', 'Stripe live key prefix'),
            'sendgrid_prefix': ('SG.', 'SendGrid key prefix'),
            'firebase_prefix': ('AIzaSy', 'Firebase key prefix'),
            'oauth_prefix': ('GOCSPX-', 'Google OAuth secret prefix'),
            'private_key_start': ('-----BEGIN', 'Private key header start'),
            'db_postgres': ('postgresql://', 'PostgreSQL URL prefix'),
            'db_mongodb': ('mongodb+srv://', 'MongoDB URL prefix'),
            'db_redis': ('redis://', 'Redis URL prefix'),
            'slack_hook': ('hooks.slack.com', 'Slack webhook domain'),
        }

        for name, (fragment, description) in fragments.items():
            if fragment in self.content:
                # Find context around the fragment
                idx = self.content.find(fragment)
                context_start = max(0, idx - 20)
                context_end = min(len(self.content), idx + len(fragment) + 50)
                context = self.content[context_start:context_end]

                self.findings['split_fragments'].append({
                    'type': name,
                    'fragment': fragment,
                    'description': description,
                    'context': context.replace('\n', ' ')[:100],
                    'position': idx,
                })

    def scan_anti_tampering(self):
        """Detect anti-tampering and security check code."""
        indicators = {
            # Function names
            'root_detection': [
                'checkRoot', 'isRooted', 'detectRoot', 'checkRootStatus',
                'RootBeer', 'rootCheck', 'isDeviceRooted'
            ],
            'jailbreak_detection': [
                'checkJailbreak', 'isJailbroken', 'detectJailbreak',
                'jailbreakCheck', 'JailbreakDetection'
            ],
            'frida_detection': [
                'checkFrida', 'detectFrida', 'checkFridaPresence',
                'frida-server', 'frida-agent', 'frida-gadget', 'LIBFRIDA'
            ],
            'debugger_detection': [
                'checkDebugger', 'isDebuggerAttached', 'detectDebugger',
                'checkDebuggerAttached', 'debugger_detection'
            ],
            'emulator_detection': [
                'checkEmulator', 'isEmulator', 'detectEmulator',
                'goldfish', 'ranchu', 'vbox86'
            ],
            'integrity_check': [
                'checkIntegrity', 'verifySignature', 'integrityCheck',
                'validateSignature', 'packageIntegrity'
            ],
            'hooking_detection': [
                'checkHooking', 'detectHooks', 'checkHookingFrameworks',
                'xposed', 'substrate', 'Cydia'
            ],
            'ssl_pinning': [
                'SSL_PINS', 'sslPinning', 'certificatePinning',
                'TrustKit', 'sha256/', 'CertificatePinner'
            ],
            'root_paths': [
                '/system/bin/su', '/system/xbin/su', '/sbin/su',
                '/data/local/tmp/su', '/su/bin/su'
            ],
            'root_packages': [
                'com.topjohnwu.magisk', 'eu.chainfire.supersu',
                'com.koushikdutta.superuser', 'com.noshufou.android.su'
            ],
        }

        for category, patterns in indicators.items():
            for pattern in patterns:
                if pattern in self.content:
                    self.findings['anti_tampering'].append({
                        'category': category,
                        'indicator': pattern,
                        'present': True,
                    })

    def scan_endpoints(self):
        """Scan for API endpoints and URLs."""
        # URL pattern - more permissive to catch concatenated strings
        url_pattern = re.compile(r'https?://[a-zA-Z0-9][a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*')

        seen_domains = set()
        for match in url_pattern.finditer(self.content):
            url = match.group()
            # Extract domain
            domain_match = re.search(r'https?://([^/:]+)', url)
            if domain_match:
                domain = domain_match.group(1)
                # Skip common CDN/tracking domains
                skip_domains = [
                    'facebook.com', 'google.com', 'googleapis.com', 'gstatic.com',
                    'cloudflare', 'cdn', 'analytics', 'tracking', 'localhost',
                    'react.dev', 'github.com/react-native', 'reactnative.dev'
                ]
                if any(skip in domain.lower() for skip in skip_domains):
                    continue

                if domain not in seen_domains:
                    seen_domains.add(domain)
                    self.findings['endpoints'].append({
                        'domain': domain,
                        'full_url': url[:100] + '...' if len(url) > 100 else url,
                        'position': match.start(),
                    })

    def _looks_like_secret(self, value: str) -> bool:
        """Heuristic to determine if a string looks like a secret."""
        if not value or len(value) < 10:
            return False

        # Check for high entropy patterns
        secret_patterns = [
            r'[A-Za-z0-9]{20,}',  # Long alphanumeric
            r'[a-f0-9]{32,}',  # Hex hash
            r'[A-Z0-9_]{10,}',  # Uppercase with underscores
        ]

        for pattern in secret_patterns:
            if re.match(pattern, value):
                return True

        # Check for secret-like keywords
        keywords = ['key', 'secret', 'token', 'password', 'api', 'auth', 'credential']
        return any(kw in value.lower() for kw in keywords)

    def _is_likely_false_positive(self, value: str, secret_type: str) -> bool:
        """Check if a finding is likely a false positive."""
        # Unicode emoji sequences often match hash patterns
        if secret_type in ['md5_hash', 'sha256_hash']:
            # Check if it's part of a larger alphanumeric string (likely not a hash)
            if re.match(r'^[a-f0-9]+$', value.lower()) and len(value) in [32, 64]:
                return False  # Likely a real hash
            return True  # Probably not a hash

        # UUID-like patterns are often not Heroku keys
        if secret_type == 'heroku_api' and not self.content.count(value) > 1:
            return True

        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of findings."""
        return {
            'total_findings': sum(len(v) for v in self.findings.values()),
            'direct_secrets': len(self.findings['direct_secrets']),
            'base64_encoded': len(self.findings['base64_encoded']),
            'hex_encoded': len(self.findings['hex_encoded']),
            'char_code_arrays': len(self.findings['char_code_arrays']),
            'split_fragments': len(self.findings['split_fragments']),
            'anti_tampering_indicators': len(self.findings['anti_tampering']),
            'unique_endpoints': len(self.findings['endpoints']),
        }


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Secret Scanner for Hermes Bundles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s bundle.hbc                 # Scan bundle with formatted output
  %(prog)s bundle.hbc --json          # Output as JSON
  %(prog)s bundle.hbc --category base64  # Show only Base64 findings
        """
    )
    parser.add_argument('bundle', help='Path to Hermes bundle file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--category', choices=[
        'direct', 'base64', 'hex', 'char_array', 'fragments', 'anti_tamper', 'endpoints', 'all'
    ], default='all', help='Filter by category')

    args = parser.parse_args()

    if not Path(args.bundle).exists():
        print(f"Error: Bundle not found: {args.bundle}", file=sys.stderr)
        sys.exit(1)

    scanner = EnhancedSecretScanner(args.bundle)
    findings = scanner.scan_all()
    summary = scanner.get_summary()

    if args.json:
        output = {
            'bundle': str(args.bundle),
            'summary': summary,
            'findings': findings,
        }
        print(json.dumps(output, indent=2))
        return

    # Pretty print
    print("=" * 70)
    print("ENHANCED SECRET SCAN RESULTS")
    print("=" * 70)
    print(f"Bundle: {args.bundle}")
    print()

    # Summary
    print("## SUMMARY")
    for key, count in summary.items():
        print(f"  {key.replace('_', ' ').title()}: {count}")
    print()

    # Detailed findings
    category_map = {
        'direct': ('direct_secrets', 'DIRECT SECRET MATCHES'),
        'base64': ('base64_encoded', 'BASE64 ENCODED SECRETS'),
        'hex': ('hex_encoded', 'HEX ENCODED SECRETS'),
        'char_array': ('char_code_arrays', 'CHARACTER CODE ARRAYS'),
        'fragments': ('split_fragments', 'SPLIT STRING FRAGMENTS'),
        'anti_tamper': ('anti_tampering', 'ANTI-TAMPERING INDICATORS'),
        'endpoints': ('endpoints', 'API ENDPOINTS'),
    }

    categories_to_show = category_map.keys() if args.category == 'all' else [args.category]

    for cat in categories_to_show:
        key, title = category_map[cat]
        items = findings[key]
        if items:
            print(f"## {title}")
            for item in items[:20]:  # Limit output
                if cat == 'direct':
                    print(f"  [{item['type']}] {item['description']}")
                    print(f"    Value: {item['value']}")
                elif cat == 'base64':
                    print(f"  Encoded: {item['encoded']}")
                    print(f"  Decoded: {item['decoded']}")
                elif cat == 'hex':
                    print(f"  Hex: {item['encoded']}")
                    print(f"  Decoded: {item['decoded']}")
                elif cat == 'char_array':
                    print(f"  Array: {item['array']}")
                    print(f"  Decoded: {item['decoded']}")
                elif cat == 'fragments':
                    print(f"  [{item['type']}] {item['description']}")
                    print(f"    Fragment: '{item['fragment']}'")
                elif cat == 'anti_tamper':
                    print(f"  [{item['category']}] {item['indicator']}")
                elif cat == 'endpoints':
                    print(f"  {item['domain']}")
                    print(f"    URL: {item['full_url']}")
                print()

            if len(items) > 20:
                print(f"  ... and {len(items) - 20} more\n")


if __name__ == '__main__':
    main()
