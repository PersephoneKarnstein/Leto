---
name: hermes-common
description: Shared methodology for Hermes bytecode analysis across Android and iOS. Secret scanning false positive triage, obfuscation detection, r2hermes commands, deep analysis verification, and traffic correlation workflows.
---

# Hermes Common Analysis Reference

Shared methodology for both Android and iOS React Native / Hermes analysis.

**Platform-specific guides:** [SKILL-android.md](SKILL-android.md) | [SKILL-ios.md](SKILL-ios.md)

---

## Key Insight: Manual Verification Required

> **Testing 13 real-world apps revealed a 75% false positive rate in automated secret detection.**
>
> Common false positives: RSA PUBLIC keys (not private), JWT version manifests (not auth tokens),
> asset identifier hashes, and bytecode noise patterns. Always manually verify findings before reporting.

---

## Shared Tool Ecosystem

These tools are used on both platforms:

| Tool | Purpose | Install | Notes |
|------|---------|---------|-------|
| **r2hermes** | Disassemble/decompile Hermes | `r2pm -ci r2hermes` | Run `r2pm update` first if install fails |
| **hermes-dec** | Decompile to JS (binary: `hbc-decompiler`) | `pip install git+https://github.com/P1sec/hermes-dec` | Actively maintained |
| **hbctool** | Disassemble/patch bytecode | `pip install hbctool` | **Legacy only**: supports bytecode v59-76. Use hermes-dec for v84+ |
| **frida** | Runtime instrumentation | `pip install frida-tools` | See version table below |
| **objection** | App patching, exploration | `pip install objection` | May need sqlite3 fix on macOS Conda |
| **gitleaks** | Secret scanning | `brew install gitleaks` | Use `gitleaks dir` syntax (not `gitleaks detect --source`) |
| **betterleaks** | Secret scanning (alternative) | See [betterleaks](https://github.com/betterleaks/betterleaks) | Lower false positive rate than gitleaks on bytecode |

### Frida Version Compatibility

| frida-tools | frida-server | Notes |
|-------------|--------------|-------|
| 14.6.x | 17.8.x | Current recommended combo |

**Note:** frida-tools uses independent versioning from frida-server. The `--no-pause` flag does not exist in current frida-tools -- app auto-resumes when spawned with `-f`.

---

## r2hermes Commands

Replace `BUNDLE` with `index.android.bundle` (Android) or `main.jsbundle` (iOS).

```bash
# Get bundle info
r2 -qc 'pd:hi' BUNDLE

# Decompile all functions
r2 -qc 'pd:ha' BUNDLE > decompiled.js

# Decompile specific function by ID
r2 -qc 'pd:hf 123' BUNDLE

# Search strings
r2 -qc 'iz~api' BUNDLE

# Fix hash after patching
r2 -wqc '.(fix-hbc)' BUNDLE
```

**Large bundles (>20MB):** r2hermes may hang or crash with "String offset/length out of bounds". Use `strings` instead:

```bash
strings BUNDLE | grep -E '^https?://' | sort -u
strings BUNDLE | grep -E 'api|endpoint|token'
```

---

## Enhanced Secret Scanning

Basic string matching misses obfuscated secrets. Use the enhanced scanner:

```bash
# Full scan
python scripts/enhanced_secret_scan.py BUNDLE

# JSON output for automation
python scripts/enhanced_secret_scan.py BUNDLE --json

# Filter by category
python scripts/enhanced_secret_scan.py BUNDLE --category base64
# Categories: direct, base64, hex, char_array, fragments, anti_tamper, endpoints, all
```

The enhanced scanner detects:
- **Base64 encoded secrets** -- decodes and checks for sensitive data
- **Hex encoded secrets** -- decodes hex strings
- **Character code arrays** -- detects `[65, 75, 73, ...]` patterns (AWS keys, etc.)
- **Split string fragments** -- finds `sk_test_`, `AKIA`, `ghp_` prefixes
- **Anti-tampering indicators** -- root/jailbreak detection, Frida detection, SSL pinning

---

## Obfuscation Analysis

```bash
# Detect obfuscation techniques
python scripts/detect_obfuscation.py TARGET [--verbose] [--json]
# TARGET: APK, IPA, bundle file, or directory
```

Common obfuscation patterns in Hermes bundles:
- String splitting with runtime concatenation
- Base64/hex encoding of secrets
- Character code arrays: `[65,75,73,65,...]` = `"AKIA..."`
- Control flow flattening (javascript-obfuscator)

**Obfuscation effectiveness (from testing):**

| Technique | Detection Difficulty |
|-----------|---------------------|
| Direct strings | Easy -- simple grep |
| Base64 encoding | Easy -- decode and scan |
| Hex encoding | Easy -- decode and scan |
| String splitting | Medium -- fragments visible |
| Char code arrays | Hard -- may be optimized away |
| Native storage | Very Hard -- requires Frida |

---

## Deep Analysis (Manual Verification)

**CRITICAL: Automated scanners produce ~75% false positive rate.** Always manually verify findings.

### RSA Key Analysis

```bash
strings BUNDLE | grep -E "RSA|BEGIN.*KEY|END.*KEY"

# IMPORTANT: Distinguish PUBLIC vs PRIVATE
# - "RSA PUBLIC KEY" or "PUBLIC KEY" = SAFE (expected for signature verification)
# - "RSA PRIVATE KEY" or "PRIVATE KEY" = CRITICAL (should never be in client)

# Check full context around matches
strings BUNDLE | grep -B2 -A2 "RSA"
```

### JWT Token Analysis

```bash
# Find JWT tokens (eyJ... format)
strings BUNDLE | grep -oE 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'

# Decode JWT payload to determine purpose
JWT="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXlsb2FkIjoiZGF0YSJ9.sig"
echo "$JWT" | cut -d. -f2 | base64 -d 2>/dev/null

# JWT Classification:
# - Auth tokens: contain user_id, exp, iat, scopes -> SENSITIVE
# - Version manifests: contain version, timestamp, messages -> NOT SENSITIVE
# - Config tokens: contain feature flags, settings -> REVIEW CONTEXT
```

### Hash Pattern Analysis

```bash
# Many MD5/SHA256 matches are NOT secrets
# Common false positives: asset/font identifiers, file integrity hashes, cache keys
strings BUNDLE | grep -oE '[a-f0-9]{32}' | head -10
# If surrounded by asset names, font data, or config -> likely NOT a secret
```

### Firebase/Google API Key Verification

```bash
# Firebase keys (AIza...) are often safe if properly restricted
strings BUNDLE | grep -oE 'AIza[A-Za-z0-9_-]{35}'
# Verify: Keys should be restricted to specific APIs and app signatures
# Unrestricted keys in production builds = vulnerability
```

### False Positive Checklist

| Pattern | Usually False Positive? | How to Verify |
|---------|------------------------|---------------|
| `RSA` | Often (check for PUBLIC) | Full context shows "PUBLIC KEY" |
| `eyJ...` JWT | Sometimes | Decode payload -- check for auth claims |
| MD5/SHA256 hash | Usually | Check surrounding context (asset IDs) |
| `SG.` prefix | Often | Bytecode noise -- check for full key format |
| Base64 strings | Often | Decode -- usually config/asset data |
| SendGrid pattern | Often | Hermes bytecode contains partial matches |

### Deep Analysis Workflow

1. Run automated scanner
2. For each finding, check full context (surrounding 50+ chars)
3. Decode encoded values (Base64, JWT)
4. Classify: AUTH SECRET vs CONFIG vs FALSE POSITIVE
5. Only report confirmed secrets

---

## Anti-Tampering Detection

Apps may include protections that affect analysis.

### Android Indicators

```bash
strings BUNDLE | grep -iE 'checkRoot|frida|jailbreak|emulator|integrity'
# checkRootStatus, isRooted, RootBeer
# checkFrida, frida-server, frida-agent
# checkDebugger, isDebuggerAttached
# checkEmulator, goldfish, ranchu
# SSL_PINS, certificatePinning
```

### iOS Indicators

```bash
strings BUNDLE | grep -iE 'jailbreak|frida|cydia|substrate|integrity'
# isJailbroken, checkJailbreak, JailMonkey
# checkFrida, frida-server, frida-agent
# checkDebugger, ptrace, sysctl
# checkCydia, checkSubstrate
# SSL_PINS, certificatePinning
```

---

## Source Map Recovery

Source maps can dramatically improve reverse engineering by mapping bundled code back to original source files.

```bash
# Scan APK/IPA/directory for source maps
python scripts/sourcemap_recovery.py TARGET

# Scan and extract found maps
python scripts/sourcemap_recovery.py TARGET --extract --output ./sourcemaps/

# JSON output
python scripts/sourcemap_recovery.py TARGET --json
```

Detects: standalone `.map` files, inline base64 source maps, external `sourceMappingURL` references, and debug build indicators (`__DEV__`, Metro bundler URLs).

---

## Traffic Capture and Correlation

### Capture Traffic with mitmproxy

```bash
# Basic capture
mitmproxy -s scripts/traffic/mitmproxy_capture.py

# Custom export path
mitmproxy -s scripts/traffic/mitmproxy_capture.py --set export_path=/tmp/traffic.json

# Focus on specific hosts
mitmproxy -s scripts/traffic/mitmproxy_capture.py --set focus_hosts=api.target.com

# Ignore additional hosts
mitmproxy -s scripts/traffic/mitmproxy_capture.py --set ignore_hosts=analytics.com,tracking.io
```

The addon automatically filters out analytics/tracking noise (Google Analytics, Facebook, Sentry, etc.) and detects GraphQL operations.

### Correlate Traffic with Bundle

```bash
# Correlate captured traffic with bundle strings
python scripts/traffic/correlate_traffic.py captured_traffic.json BUNDLE

# Save report as JSON
python scripts/traffic/correlate_traffic.py traffic.json BUNDLE --output report.json
```

The correlator identifies:
- **Matched endpoints** -- URLs found in both traffic and bundle
- **Unmatched traffic** -- dynamic or third-party endpoints not in bundle
- **Bundle-only endpoints** -- potential attack surface (in code but not exercised)
- **Authentication patterns** -- Bearer tokens, API keys, session cookies
- **GraphQL operations** -- queries, mutations, and their variables

---

## React Native Bridge Tracing

Hook the React Native bridge to trace native module calls and detect sensitive operations:

```bash
frida -U -f com.target.app -l scripts/frida/rn_bridge_trace.js
```

Traces sensitive modules including: Keychain access, crypto operations, AsyncStorage/MMKV reads, network calls, biometric auth, clipboard access, and push notifications. Highlights payloads containing passwords, tokens, and secrets.

Configure at the top of the script:
- `TRACE_ALL: true` -- log all bridge calls (verbose)
- `TRACE_SENSITIVE: true` -- only log sensitive modules (default)
- `LOG_PAYLOADS: true` -- include method arguments (default)

---

## Hermes Version Detection

The `analyze_apk.py` / `analyze_ipa.py` scripts may report incorrect bytecode versions. **Always verify with the `file` command:**

```bash
file BUNDLE
# Output: Hermes JavaScript bytecode, version 96
```

The `file` command is the most reliable method for version detection.

---

## Script Reference

### Analysis Scripts

| Script | Purpose | Flags |
|--------|---------|-------|
| `analyze_apk.py` | APK analysis workflow | `--decompile`, `--enhanced`, `--extract-only`, `-o DIR` |
| `analyze_ipa.py` | IPA analysis workflow | `--decompile`, `--enhanced`, `--extract-only`, `-o DIR` |
| `analyze_bundle.py` | Hermes bundle analysis | `--strings`, `--functions`, `--json`, `--limit N`, `-o DIR` |
| `enhanced_secret_scan.py` | Obfuscated secret detection | `--json`, `--category {direct,base64,hex,char_array,fragments,anti_tamper,endpoints,all}` |
| `detect_obfuscation.py` | Obfuscation technique detection | `--verbose`, `--json` |
| `sourcemap_recovery.py` | Source map detection/extraction | `--extract`, `--output DIR`, `--json` |

### Traffic Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `traffic/mitmproxy_capture.py` | mitmproxy addon for API capture | `mitmproxy -s scripts/traffic/mitmproxy_capture.py` |
| `traffic/correlate_traffic.py` | Correlate traffic with bundle | `python scripts/traffic/correlate_traffic.py traffic.json bundle` |

### Frida Scripts

| Script | Purpose | Platform |
|--------|---------|----------|
| `frida/universal_ssl_bypass.js` | SSL/TLS pinning bypass (40+ methods) | Android |
| `frida/root_bypass.js` | Root + emulator detection bypass | Android |
| `frida/gms_firebase_bypass.js` | Google Play Services stub | Android |
| `frida/ios_ssl_bypass.js` | SSL pinning bypass (TrustKit, AFNetworking, SecTrust) | iOS |
| `frida/ios_jailbreak_bypass.js` | Jailbreak detection bypass | iOS |
| `frida/hermes_hooks.js` | React Native bridge + network hooks | Both |
| `frida/rn_bridge_trace.js` | Bridge tracer with sensitive module detection | Both |
| `frida/detect_frameworks.js` | Detect frameworks, libs, SDKs | Android |

---

## Platform Differences

| Aspect | Android | iOS |
|--------|---------|-----|
| Bundle file | `assets/index.android.bundle` | `main.jsbundle` |
| Package format | APK (zip) | IPA (zip) |
| Root access | Rooted emulator | Jailbroken device |
| Dynamic instrumentation | Frida + frida-server | Frida + jailbreak or gadget |
| Emulation | Android Emulator (full) | iOS Simulator (limited, source-built apps only) |
| Analysis script | `analyze_apk.py` | `analyze_ipa.py` |
| Tool checker | `check_tools.py` | `check_tools_ios.py` |

---

## References

- [OWASP MASTG](https://mas.owasp.org/MASTG/) -- Mobile security testing guide
- [Frida](https://frida.re/) -- Runtime instrumentation
- [Frida CodeShare](https://codeshare.frida.re/) -- Community Frida scripts
- [Hermes](https://github.com/facebook/hermes) -- Meta's JS engine
- [hermes-dec](https://github.com/P1sec/hermes-dec) -- Hermes decompiler
- [Maestro](https://maestro.mobile.dev/) -- UI automation
