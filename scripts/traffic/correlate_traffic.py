#!/usr/bin/env python3
"""
Traffic-Bundle Correlation Tool

Correlates captured API traffic with strings found in Hermes bundles.
Helps identify which endpoints are used, authentication patterns,
and potential attack surfaces.

Usage:
    python correlate_traffic.py captured_traffic.json index.android.bundle
    python correlate_traffic.py traffic.json bundle.js --output report.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Any
from urllib.parse import urlparse


class TrafficCorrelator:
    def __init__(self, traffic_file: str, bundle_path: str):
        self.traffic_file = Path(traffic_file)
        self.bundle_path = Path(bundle_path)

        self.traffic_data = None
        self.bundle_strings = set()
        self.bundle_urls = set()

        self.correlation = {
            "matched_endpoints": [],
            "unmatched_traffic": [],
            "bundle_only_endpoints": [],
            "auth_patterns": [],
            "graphql_operations": [],
            "api_summary": {},
        }

    def run(self) -> Dict[str, Any]:
        """Run correlation analysis."""
        print(f"[*] Loading traffic from: {self.traffic_file}")
        self._load_traffic()

        print(f"[*] Extracting strings from bundle: {self.bundle_path}")
        self._extract_bundle_strings()

        print("[*] Correlating traffic with bundle...")
        self._correlate()

        print("[*] Analyzing patterns...")
        self._analyze_patterns()

        self._print_report()

        return self.correlation

    def _load_traffic(self):
        """Load captured traffic JSON."""
        with open(self.traffic_file, 'r') as f:
            self.traffic_data = json.load(f)

        requests = self.traffic_data.get("requests", [])
        print(f"    [+] Loaded {len(requests)} captured requests")

    def _extract_bundle_strings(self):
        """Extract URLs and API-related strings from bundle."""
        # Read bundle (may be large)
        content = self.bundle_path.read_bytes()

        # Extract URLs
        url_pattern = re.compile(rb'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+')
        for match in url_pattern.finditer(content):
            url = match.group().decode('utf-8', errors='ignore')
            self.bundle_urls.add(url)

        # Extract path patterns (API routes)
        path_pattern = re.compile(rb'["\']/(api|v[0-9]+|graphql|rest|auth)/[a-zA-Z0-9/_\-{}:]+["\']')
        for match in path_pattern.finditer(content):
            path = match.group().decode('utf-8', errors='ignore').strip('"\'')
            self.bundle_strings.add(path)

        # Extract GraphQL operation names
        graphql_pattern = re.compile(rb'(query|mutation|subscription)\s+(\w+)\s*[\({]')
        for match in graphql_pattern.finditer(content):
            op = f"{match.group(1).decode()} {match.group(2).decode()}"
            self.bundle_strings.add(op)

        print(f"    [+] Found {len(self.bundle_urls)} URLs in bundle")
        print(f"    [+] Found {len(self.bundle_strings)} API patterns in bundle")

    def _correlate(self):
        """Correlate traffic with bundle strings."""
        requests = self.traffic_data.get("requests", [])

        matched_urls = set()
        seen_endpoints = defaultdict(list)

        for req in requests:
            url = req.get("url", "")
            path = req.get("path", "")
            host = req.get("host", "")
            method = req.get("method", "")

            # Check if URL or path appears in bundle
            url_matched = False
            matching_bundle_string = None

            # Check exact URL match
            if url in self.bundle_urls:
                url_matched = True
                matching_bundle_string = url
            else:
                # Check if base URL (without query params) matches
                base_url = url.split('?')[0]
                if base_url in self.bundle_urls:
                    url_matched = True
                    matching_bundle_string = base_url

            # Check path patterns
            if not url_matched:
                for pattern in self.bundle_strings:
                    if pattern in path or pattern in url:
                        url_matched = True
                        matching_bundle_string = pattern
                        break

            # Categorize
            endpoint_key = f"{method} {urlparse(url).path}"

            if url_matched:
                matched_urls.add(url)
                if endpoint_key not in [m["endpoint"] for m in self.correlation["matched_endpoints"]]:
                    self.correlation["matched_endpoints"].append({
                        "endpoint": endpoint_key,
                        "url": url,
                        "method": method,
                        "host": host,
                        "bundle_match": matching_bundle_string,
                        "status_codes": [],
                        "request_count": 0,
                    })

                # Update stats
                for m in self.correlation["matched_endpoints"]:
                    if m["endpoint"] == endpoint_key:
                        m["request_count"] += 1
                        if req.get("status_code") not in m["status_codes"]:
                            m["status_codes"].append(req.get("status_code"))
                        break
            else:
                if endpoint_key not in [u["endpoint"] for u in self.correlation["unmatched_traffic"]]:
                    self.correlation["unmatched_traffic"].append({
                        "endpoint": endpoint_key,
                        "url": url,
                        "method": method,
                        "host": host,
                        "note": "Endpoint called but not found in bundle strings",
                    })

        # Find bundle endpoints not seen in traffic
        traffic_hosts = set(req.get("host", "") for req in requests)

        for url in self.bundle_urls:
            parsed = urlparse(url)
            if parsed.netloc and parsed.netloc not in traffic_hosts:
                if url not in [b["url"] for b in self.correlation["bundle_only_endpoints"]]:
                    self.correlation["bundle_only_endpoints"].append({
                        "url": url,
                        "host": parsed.netloc,
                        "path": parsed.path,
                        "note": "Found in bundle but not observed in traffic",
                    })

    def _analyze_patterns(self):
        """Analyze authentication and API patterns."""
        requests = self.traffic_data.get("requests", [])

        # Auth patterns
        auth_methods = defaultdict(list)

        for req in requests:
            auth = req.get("request", {}).get("auth", {})
            if auth:
                for header, value in auth.items():
                    header_lower = header.lower()
                    if "bearer" in value.lower():
                        auth_methods["Bearer Token"].append(req["url"])
                    elif header_lower == "authorization" and "basic" in value.lower():
                        auth_methods["Basic Auth"].append(req["url"])
                    elif "api" in header_lower and "key" in header_lower:
                        auth_methods["API Key"].append(req["url"])
                    elif header_lower == "cookie":
                        auth_methods["Session Cookie"].append(req["url"])
                    elif "csrf" in header_lower:
                        auth_methods["CSRF Token"].append(req["url"])

        for method, urls in auth_methods.items():
            unique_hosts = set(urlparse(u).netloc for u in urls)
            self.correlation["auth_patterns"].append({
                "type": method,
                "request_count": len(urls),
                "hosts": list(unique_hosts),
            })

        # GraphQL operations
        for req in requests:
            if req.get("type") == "graphql":
                op = req.get("graphql_operation", "unknown")
                body = req.get("request", {}).get("body", {})

                if op not in [g["operation"] for g in self.correlation["graphql_operations"]]:
                    self.correlation["graphql_operations"].append({
                        "operation": op,
                        "url": req["url"],
                        "variables": list(body.get("variables", {}).keys()) if isinstance(body, dict) else [],
                    })

        # API summary by host
        host_stats = defaultdict(lambda: {"methods": set(), "endpoints": set(), "count": 0})

        for req in requests:
            host = req.get("host", "unknown")
            host_stats[host]["methods"].add(req.get("method", ""))
            host_stats[host]["endpoints"].add(req.get("path", "").split("?")[0])
            host_stats[host]["count"] += 1

        self.correlation["api_summary"] = {
            host: {
                "methods": list(stats["methods"]),
                "unique_endpoints": len(stats["endpoints"]),
                "total_requests": stats["count"],
            }
            for host, stats in host_stats.items()
        }

    def _print_report(self):
        """Print correlation report."""
        print("\n" + "=" * 70)
        print("TRAFFIC-BUNDLE CORRELATION REPORT")
        print("=" * 70)

        # Matched endpoints
        print(f"\n## Matched Endpoints ({len(self.correlation['matched_endpoints'])})")
        print("Endpoints found in both traffic AND bundle:")
        for m in sorted(self.correlation['matched_endpoints'], key=lambda x: -x['request_count'])[:15]:
            print(f"  [{m['request_count']:3}x] {m['endpoint']}")
            print(f"         Bundle: {m['bundle_match'][:60]}..." if len(str(m['bundle_match'])) > 60 else f"         Bundle: {m['bundle_match']}")

        # Unmatched traffic
        if self.correlation['unmatched_traffic']:
            print(f"\n## Unmatched Traffic ({len(self.correlation['unmatched_traffic'])})")
            print("Endpoints in traffic but NOT in bundle (dynamic or third-party):")
            for u in self.correlation['unmatched_traffic'][:10]:
                print(f"  - {u['endpoint']} ({u['host']})")

        # Bundle-only endpoints
        if self.correlation['bundle_only_endpoints']:
            print(f"\n## Bundle-Only Endpoints ({len(self.correlation['bundle_only_endpoints'])})")
            print("Found in bundle but NOT observed in traffic (potential attack surface):")
            for b in self.correlation['bundle_only_endpoints'][:15]:
                print(f"  - {b['url']}")

        # Auth patterns
        if self.correlation['auth_patterns']:
            print(f"\n## Authentication Patterns")
            for auth in self.correlation['auth_patterns']:
                print(f"  - {auth['type']}: {auth['request_count']} requests across {len(auth['hosts'])} host(s)")

        # GraphQL
        if self.correlation['graphql_operations']:
            print(f"\n## GraphQL Operations ({len(self.correlation['graphql_operations'])})")
            for gql in self.correlation['graphql_operations']:
                vars_str = f" (vars: {', '.join(gql['variables'][:3])})" if gql['variables'] else ""
                print(f"  - {gql['operation']}{vars_str}")

        # API Summary
        print(f"\n## API Summary by Host")
        for host, stats in sorted(self.correlation['api_summary'].items(), key=lambda x: -x[1]['total_requests']):
            print(f"  {host}:")
            print(f"    Methods: {', '.join(stats['methods'])}")
            print(f"    Endpoints: {stats['unique_endpoints']} unique, {stats['total_requests']} total requests")

        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Correlate captured traffic with bundle strings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("traffic", help="Captured traffic JSON file")
    parser.add_argument("bundle", help="Hermes/JS bundle file")
    parser.add_argument("--output", "-o", help="Output report to JSON file")

    args = parser.parse_args()

    if not Path(args.traffic).exists():
        print(f"Error: Traffic file not found: {args.traffic}")
        sys.exit(1)

    if not Path(args.bundle).exists():
        print(f"Error: Bundle file not found: {args.bundle}")
        sys.exit(1)

    correlator = TrafficCorrelator(args.traffic, args.bundle)
    result = correlator.run()

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[*] Report saved to: {args.output}")


if __name__ == "__main__":
    main()
