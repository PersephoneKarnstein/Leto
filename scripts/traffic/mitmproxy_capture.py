"""
mitmproxy Addon for React Native API Traffic Capture

Captures HTTP/HTTPS traffic and exports it for correlation with
bundle analysis. Filters out noise and focuses on API calls.

Usage:
    mitmproxy -s mitmproxy_capture.py
    mitmproxy -s mitmproxy_capture.py --set export_path=/tmp/traffic.json
    mitmdump -s mitmproxy_capture.py -w traffic.mitm

Configuration (via --set):
    export_path: Path to export captured traffic (default: ./captured_traffic.json)
    ignore_hosts: Comma-separated hosts to ignore
    focus_hosts: Comma-separated hosts to focus on (ignore all others)
"""

import json
import re
from datetime import datetime
from mitmproxy import http, ctx
from typing import Optional
from urllib.parse import urlparse


class ReactNativeTrafficCapture:
    def __init__(self):
        self.captured = []
        self.export_path = "./captured_traffic.json"
        self.ignore_hosts = set()
        self.focus_hosts = set()

        # Default hosts to ignore (tracking, analytics, CDNs)
        self.default_ignore = {
            "google-analytics.com",
            "googletagmanager.com",
            "facebook.com",
            "facebook.net",
            "fbcdn.net",
            "doubleclick.net",
            "crashlytics.com",
            "app-measurement.com",
            "firebaseinstallations.googleapis.com",
            "firebaselogging.googleapis.com",
            "cloudflare.com",
            "cloudfront.net",
            "akamai.net",
            "akamaized.net",
            "amplitude.com",
            "mixpanel.com",
            "segment.io",
            "segment.com",
            "sentry.io",
            "bugsnag.com",
            "appsflyer.com",
            "adjust.com",
            "branch.io",
        }

    def load(self, loader):
        loader.add_option(
            name="export_path",
            typespec=str,
            default="./captured_traffic.json",
            help="Path to export captured traffic JSON"
        )
        loader.add_option(
            name="ignore_hosts",
            typespec=str,
            default="",
            help="Comma-separated hosts to ignore"
        )
        loader.add_option(
            name="focus_hosts",
            typespec=str,
            default="",
            help="Comma-separated hosts to focus on"
        )

    def configure(self, updates):
        if "export_path" in updates:
            self.export_path = ctx.options.export_path

        if "ignore_hosts" in updates and ctx.options.ignore_hosts:
            self.ignore_hosts = set(h.strip() for h in ctx.options.ignore_hosts.split(","))

        if "focus_hosts" in updates and ctx.options.focus_hosts:
            self.focus_hosts = set(h.strip() for h in ctx.options.focus_hosts.split(","))

    def _should_capture(self, host: str) -> bool:
        """Determine if traffic from this host should be captured."""
        host_lower = host.lower()

        # If focus hosts specified, only capture those
        if self.focus_hosts:
            return any(f in host_lower for f in self.focus_hosts)

        # Check ignore lists
        if any(i in host_lower for i in self.ignore_hosts):
            return False
        if any(i in host_lower for i in self.default_ignore):
            return False

        return True

    def _extract_auth_info(self, headers: dict) -> dict:
        """Extract authentication-related headers."""
        auth_info = {}
        auth_headers = [
            "authorization",
            "x-api-key",
            "x-auth-token",
            "x-access-token",
            "x-csrf-token",
            "cookie",
            "x-requested-with",
        ]

        for key, value in headers.items():
            if key.lower() in auth_headers:
                # Truncate long values
                if len(value) > 100:
                    auth_info[key] = value[:50] + "..." + value[-20:]
                else:
                    auth_info[key] = value

        return auth_info

    def _parse_body(self, content: bytes, content_type: str) -> Optional[dict]:
        """Parse request/response body."""
        if not content:
            return None

        try:
            if "json" in content_type.lower():
                return json.loads(content.decode('utf-8', errors='ignore'))
            elif "x-www-form-urlencoded" in content_type.lower():
                from urllib.parse import parse_qs
                return parse_qs(content.decode('utf-8', errors='ignore'))
            elif "graphql" in content_type.lower():
                return json.loads(content.decode('utf-8', errors='ignore'))
        except:
            pass

        # Return truncated string for other types
        if len(content) < 1000:
            try:
                return {"_raw": content.decode('utf-8', errors='ignore')}
            except:
                pass

        return {"_size": len(content), "_type": content_type}

    def response(self, flow: http.HTTPFlow):
        """Capture completed request/response pairs."""
        host = flow.request.host

        if not self._should_capture(host):
            return

        # Skip non-API content types
        response_type = flow.response.headers.get("content-type", "")
        if any(t in response_type.lower() for t in ["image/", "font/", "video/", "audio/"]):
            return

        # Build capture record
        record = {
            "timestamp": datetime.now().isoformat(),
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "host": host,
            "path": flow.request.path,
            "status_code": flow.response.status_code,
            "request": {
                "headers": dict(flow.request.headers),
                "auth": self._extract_auth_info(dict(flow.request.headers)),
                "content_type": flow.request.headers.get("content-type", ""),
                "body": self._parse_body(
                    flow.request.content,
                    flow.request.headers.get("content-type", "")
                ),
            },
            "response": {
                "headers": dict(flow.response.headers),
                "content_type": response_type,
                "body": self._parse_body(flow.response.content, response_type),
            },
        }

        # Detect GraphQL
        if "graphql" in flow.request.path.lower() or (
            record["request"]["body"] and
            isinstance(record["request"]["body"], dict) and
            "query" in record["request"]["body"]
        ):
            record["type"] = "graphql"
            if isinstance(record["request"]["body"], dict):
                query = record["request"]["body"].get("query", "")
                # Extract operation name
                op_match = re.search(r'(query|mutation|subscription)\s+(\w+)', query)
                if op_match:
                    record["graphql_operation"] = f"{op_match.group(1)} {op_match.group(2)}"
        else:
            record["type"] = "rest"

        self.captured.append(record)

        # Log to console
        ctx.log.info(f"[{record['type'].upper()}] {record['method']} {record['url']} -> {record['status_code']}")

        # Auto-save periodically
        if len(self.captured) % 10 == 0:
            self._save()

    def done(self):
        """Save captured traffic on exit."""
        self._save()
        ctx.log.info(f"Captured {len(self.captured)} API calls -> {self.export_path}")

    def _save(self):
        """Save captured traffic to file."""
        try:
            with open(self.export_path, 'w') as f:
                json.dump({
                    "captured_at": datetime.now().isoformat(),
                    "total_requests": len(self.captured),
                    "requests": self.captured,
                }, f, indent=2, default=str)
        except Exception as e:
            ctx.log.error(f"Failed to save traffic: {e}")


addons = [ReactNativeTrafficCapture()]
