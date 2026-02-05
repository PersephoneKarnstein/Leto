---
name: hermes-ios
description: Analyze Hermes bytecode in React Native iOS apps. Disassemble, decompile, patch, and instrument .hbc files and main.jsbundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "ios", "ipa", "jailbreak"
---

# Hermes iOS Analysis

Toolkit for reverse engineering React Native **iOS** applications compiled with Meta's Hermes JavaScript engine.

**For Android analysis, see [SKILL-android.md](SKILL-android.md).**

---

## Key Insight: Manual Verification Required

> **Testing 13 real-world apps revealed a 75% false positive rate in automated secret detection.**
>
> Common false positives: RSA PUBLIC keys (not private), JWT version manifests (not auth tokens),
> asset identifier hashes, and bytecode noise patterns. Always manually verify findings before reporting.
>
> See **Phase 8: Deep Analysis** for verification methodology.

---

## Quick Start

```bash
# 1. Check tools
python scripts/check_tools_ios.py

# 2. Analyze IPA (with enhanced secret scanning)
python scripts/analyze_ipa.py target.ipa --decompile --enhanced

# 3. Verify Hermes version (most reliable method)
file ./target_analysis/extracted/Payload/*.app/main.jsbundle

# 4. Check for secrets
gitleaks dir ./target_analysis/extracted/ -v

# 5. Run with Frida (jailbroken device)
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

**Key files to check:**
- `main.jsbundle` - Hermes bytecode
- `Info.plist` - URL schemes, ATS exceptions
- `Entitlements` - Sensitive capabilities
- `PrivacyInfo.xcprivacy` - Privacy manifest (iOS 17+)

---

## Critical: iOS Testing Approaches

Unlike Android, iOS has fundamental platform restrictions that affect testing:

### App Store IPAs Cannot Run in Simulator

**This is the most important iOS limitation.** App Store/distribution IPAs are built for **device architecture only** (arm64-device) and will NOT run in iOS Simulator.

```bash
# Check binary architecture
lipo -info Payload/*.app/AppName
# App Store: "Non-fat file ... is architecture: arm64"
# Simulator-compatible: "... x86_64 arm64" (multiple slices)
```

### Choose Your Testing Approach

| Approach | What You Can Test | Requirements |
|----------|-------------------|--------------|
| **Static only** | Bundle analysis, decompilation, secrets | Just the IPA |
| **Simulator** | Apps you build from source | Xcode + source code |
| **Jailbroken device** | Any app, full Frida | Physical device + jailbreak |
| **Frida Gadget** | Patched IPAs | Xcode + dev certificate |

---

## Tool Ecosystem

| Tool | Purpose | Install |
|------|---------|---------|
| **r2hermes** | Disassemble/decompile Hermes | `r2pm -ci r2hermes` |
| **hermes-dec** | Decompile to JS (binary: `hbc-decompiler`) | `pip install git+https://github.com/P1sec/hermes-dec` |
| **hbctool** | Disassemble/patch bytecode | `pip install hbctool` |
| **frida** | Runtime instrumentation | `pip install frida-tools` |
| **objection** | IPA patching, exploration | `pip install objection` |
| **Xcode** | iOS Simulator, build tools | App Store (15GB+) |
| **Maestro** | UI automation | `curl -fsSL "https://get.maestro.mobile.dev" \| bash` |
| **gitleaks** | Secret scanning | `brew install gitleaks` |

### Xcode Requirements

**Full Xcode required** for iOS Simulator (not just Command Line Tools):
```bash
# Check current setup
xcode-select -p
# "/Library/Developer/CommandLineTools" = NO simulator
# "/Applications/Xcode.app/..." = Simulator available

# Switch to full Xcode after install
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

# Download iOS runtime if needed
xcodebuild -downloadPlatform iOS
```

---

## Analysis Workflow

### Phase 1: Setup (One-time)

```bash
# Check all tools
python scripts/check_tools_ios.py --install-help

# Verify Xcode configuration
xcode-select -p
xcrun simctl list runtimes  # Should show iOS runtimes
```

### Phase 2: Automated Analysis

```bash
# Full automated analysis with enhanced secret scanning
python scripts/analyze_ipa.py target.ipa --decompile --enhanced

# IMPORTANT: Verify Hermes version with file command
file ./target_analysis/extracted/Payload/*.app/main.jsbundle
# Expected: "Hermes JavaScript bytecode, version 96"
```

The analyzer extracts:
- IPA contents and app bundle
- Binary architecture (device vs simulator)
- Info.plist (ATS, URL schemes, permissions)
- Entitlements (capabilities, keychain groups)
- PrivacyInfo.xcprivacy (iOS 17+ privacy manifest)
- Hermes bundle and version
- API endpoints and secrets

### Phase 3: Secret Scanning

```bash
# Scan extracted IPA for secrets
gitleaks dir ./target_analysis/extracted/ -v > gitleaks_results.txt

# Check plist files for hardcoded values
plutil -p ./target_analysis/extracted/Payload/*.app/Info.plist | grep -iE 'api|key|secret'

# Scan embedded frameworks
find ./target_analysis/extracted/ -name "*.plist" -exec plutil -p {} \; | grep -iE 'key|token|secret'

# String extraction from Hermes bundle
strings ./target_analysis/extracted/Payload/*.app/main.jsbundle | grep -E '^https?://' | sort -u
```

**Note:** gitleaks/trufflehog produce false positives. **Testing showed ~75% false positive rate.**

Common false positives:
| False Positive Type | Example | How to Identify |
|---------------------|---------|-----------------|
| Unicode emoji sequences | `1F471-1F3FC-200D-2640-FE0F` | Hex pattern but emoji code |
| Build verification tokens | Sentry DSN, build hashes | Check vendor documentation |
| RSA PUBLIC keys | `BEGIN RSA PUBLIC KEY` | Safe - used for verification |
| Version manifest JWTs | JWT with `versions`, `timestamp` | Decode payload to check |
| Asset identifiers | MD5 hashes of fonts/images | Surrounded by asset names |
| Bytecode noise | `SG.` in garbled context | Check for complete key format |

**Deep analysis workflow:**
1. Run automated scanner
2. For each finding, check full context (surrounding 50+ chars)
3. Decode encoded values (Base64, JWT)
4. Classify: AUTH SECRET vs CONFIG vs FALSE POSITIVE
5. Only report confirmed secrets

### Phase 4: Hermes Analysis

```bash
# Decompile with r2hermes
r2 -qc 'pd:ha' main.jsbundle > decompiled.js

# Extract strings
r2 -qc 'iz~http' main.jsbundle

# For large bundles (>20MB), use strings command instead
strings main.jsbundle | grep -E 'api|endpoint|token'
```

### Phase 5: Enhanced Secret Scanning

Basic string matching misses obfuscated secrets. Use the enhanced scanner:

```bash
# Run enhanced secret scan (detects obfuscated secrets)
python scripts/enhanced_secret_scan.py main.jsbundle

# Or with JSON output for automation
python scripts/enhanced_secret_scan.py main.jsbundle --json
```

The enhanced scanner detects:
- **Base64 encoded secrets** - decodes and checks for sensitive data
- **Hex encoded secrets** - decodes hex strings
- **Character code arrays** - detects `[65, 75, 73, ...]` patterns (AWS keys, etc.)
- **Split string fragments** - finds `sk_test_`, `AKIA`, `ghp_` prefixes
- **Anti-tampering indicators** - jailbreak detection, Frida detection, SSL pinning

### Phase 6: Obfuscation Analysis

```bash
# Detect obfuscation techniques
python scripts/detect_obfuscation.py target.ipa

# Common obfuscation patterns in Hermes bundles:
# - String splitting with runtime concatenation
# - Base64/hex encoding of secrets
# - Character code arrays: [65,75,73,65,...] = "AKIA..."
# - Control flow flattening (javascript-obfuscator)
```

**Obfuscation effectiveness (from testing):**

| Technique | Detection Difficulty |
|-----------|---------------------|
| Direct strings | Easy - simple grep |
| Base64 encoding | Easy - decode and scan |
| Hex encoding | Easy - decode and scan |
| String splitting | Medium - fragments visible |
| Char code arrays | Hard - may be optimized away |
| Native storage | Very Hard - requires Frida |

### Phase 7: Anti-Tampering Detection

Apps may include protections that affect analysis:

```bash
# Check for anti-tampering code in bundle
strings main.jsbundle | grep -iE 'jailbreak|frida|cydia|substrate|integrity'

# Common iOS anti-tampering indicators:
# - isJailbroken, checkJailbreak, JailMonkey
# - checkFrida, frida-server, frida-agent
# - checkDebugger, ptrace, sysctl
# - checkCydia, checkSubstrate
# - SSL_PINS, certificatePinning
```

**Bypassing anti-tampering:**
```bash
# Use jailbreak bypass Frida script
frida -U -f com.target.app -l scripts/frida/ios_jailbreak_bypass.js

# Combined bypass for stubborn apps
cat scripts/frida/ios_ssl_bypass.js \
    scripts/frida/ios_jailbreak_bypass.js > /tmp/ios_all.js
frida -U -f com.target.app -l /tmp/ios_all.js
```

### Phase 8: Deep Analysis (Manual Verification)

**CRITICAL: Automated scanners produce ~75% false positive rate.** Always manually verify findings.

#### RSA Key Analysis

```bash
# Search for RSA keys in bundle
strings main.jsbundle | grep -E "RSA|BEGIN.*KEY|END.*KEY"

# IMPORTANT: Distinguish PUBLIC vs PRIVATE
# - "RSA PUBLIC KEY" or "PUBLIC KEY" = SAFE (expected for signature verification)
# - "RSA PRIVATE KEY" or "PRIVATE KEY" = CRITICAL (should never be in client)

# Check full context around matches
strings main.jsbundle | grep -B2 -A2 "RSA"
```

#### JWT Token Analysis

```bash
# Find JWT tokens (eyJ... format)
strings main.jsbundle | grep -oE 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'

# Decode JWT payload to determine purpose
JWT="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXlsb2FkIjoiZGF0YSJ9.sig"
echo "$JWT" | cut -d. -f2 | base64 -d 2>/dev/null

# JWT Classification:
# - Auth tokens: contain user_id, exp, iat, scopes → SENSITIVE
# - Version manifests: contain version, timestamp, messages → NOT SENSITIVE
# - Config tokens: contain feature flags, settings → REVIEW CONTEXT
```

#### Native Binary Analysis (iOS-Specific)

```bash
# Extract strings from native binary for security patterns
APP_BINARY="./extracted/Payload/*.app/AppName"

# Check for jailbreak detection paths
strings "$APP_BINARY" | grep -E '/Applications/Cydia|MobileSubstrate|/var/lib/cydia'

# Known jailbreak detection paths (from enterprise apps):
# - /Applications/Cydia.app
# - /Library/MobileSubstrate/MobileSubstrate.dylib
# - /Library/MobileSubstrate/DynamicLibraries/*.plist
# - /private/var/lib/cydia
# - /private/var/tmp/cydia.log
# - /System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist

# Check for SSL pinning libraries
strings "$APP_BINARY" | grep -iE 'PinnedCertificate|TrustEvaluator|CertificatePinning'

# Common SSL pinning implementations:
# - Alamofire: PinnedCertificatesTrustEvaluator
# - Starscream: CertificatePinning (WebSocket)
# - TrustKit: TSKPinningValidator
```

#### Enterprise Security Patterns

Enterprise apps often include MDM and advanced security:

```bash
# Check for Microsoft Intune MDM
ls ./extracted/Payload/*.app/Frameworks/ | grep -i intune

# Check Info.plist for MDM settings
plutil -p ./extracted/Payload/*.app/Info.plist | grep -iE 'intune|mdm|adal'

# Common enterprise indicators:
# - IntuneMAMSwift.framework
# - ADALClientId, ADALRedirectUri (Azure AD)
# - Policy enforcement, compliance checks
# - File protection levels

# Check for WebRTC security (voice/video calls)
ls ./extracted/Payload/*.app/Frameworks/ | grep -i webrtc
# WebRTC should use DTLS + SRTP for secure media
```

#### False Positive Checklist (iOS)

| Pattern | Usually False Positive? | How to Verify |
|---------|------------------------|---------------|
| `RSA` | Often (check for PUBLIC) | Full context shows "PUBLIC KEY" |
| `eyJ...` JWT | Sometimes | Decode payload - check for auth claims |
| MD5/SHA256 hash | Usually | Check surrounding context (asset IDs) |
| `SG.` prefix | Often | Bytecode noise - check for full key format |
| SendGrid pattern | Often | Hermes bytecode contains partial matches |

### Phase 10: Dynamic Analysis (Choose One)

**Option A: Simulator** (apps you build)
```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
xcrun simctl install booted /path/to/App.app
xcrun simctl launch booted com.bundle.id
```

**Option B: Jailbroken Device** (recommended for real apps)
```bash
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

**Option C: Frida Gadget** (non-jailbroken)
```bash
objection patchipa --source app.ipa --codesign-signature "Apple Development: you@email.com"
ios-deploy --bundle app-frida-codesigned.ipa
objection -g "App Name" explore
```

---

## IPA Extraction (Manual)

If not using `analyze_ipa.py`:

```bash
# Unzip IPA
unzip -o app.ipa -d extracted_ipa/

# Find Hermes bundle
ls extracted_ipa/Payload/*.app/main.jsbundle

# Copy for analysis
cp extracted_ipa/Payload/*.app/main.jsbundle ./

# Verify it's Hermes bytecode
file main.jsbundle
# "Hermes JavaScript bytecode, version XX" = Hermes
# "ASCII text" = Plain JavaScript
```

---

## Info.plist Analysis

```bash
# Convert to readable format
plutil -convert xml1 extracted_ipa/Payload/*.app/Info.plist -o Info_readable.plist

# Check ATS exceptions (allows HTTP)
grep -A 10 "NSAppTransportSecurity" Info_readable.plist

# Check URL schemes (deep links)
grep -A 20 "CFBundleURLTypes" Info_readable.plist

# Check entitlements
codesign -d --entitlements :- extracted_ipa/Payload/*.app/ 2>/dev/null
```

---

## Privacy Manifest Analysis (iOS 17+)

iOS 17+ apps may include privacy manifests declaring data collection:

```bash
# Find privacy manifests
find extracted_ipa/ -name "PrivacyInfo.xcprivacy"

# Parse privacy manifest
plutil -p extracted_ipa/Payload/*.app/PrivacyInfo.xcprivacy

# Key fields to check:
# - NSPrivacyAccessedAPITypes: APIs requiring reason
# - NSPrivacyTrackingDomains: Tracking domains
# - NSPrivacyCollectedDataTypes: Data collected from users
```

---

## Jailbreak Tools

| Tool | Devices | iOS Versions | Type |
|------|---------|--------------|------|
| **Palera1n** | A8-A11 | 15.0-17.x | Semi-tethered |
| **Dopamine** | A12-A16 | 15.0-16.6.1 | Semi-untethered |
| **nathanlr** | A12+ | 16.5.1-17.0 | Semi-jailbreak |
| **Checkra1n** | A7-A11 | 12.0-14.8.1 | Semi-tethered |

**Note on nathanlr:** Semi-jailbreak providing limited functionality (no tweak injection). Useful for Frida access on newer devices. Install via [ios.cfw.guide](https://ios.cfw.guide/installing-nathanlr/).

### Palera1n Setup (A8-A11)

```bash
# Download from https://github.com/palera1n/palera1n/releases
./palera1n

# After jailbreak, install Sileo
# Add Frida repo: https://build.frida.re/
```

### Dopamine Setup (A12+)

```bash
# Install TrollStore first
# Install Dopamine.tipa via TrollStore
# Jailbreak from Dopamine app
# Install Sileo, then Frida
```

---

## iOS Simulator (Development Testing)

For apps you can build yourself (your own apps or open-source), iOS Simulator provides a testing environment without jailbreak. Note: App Store apps cannot run in Simulator.

### Basic Commands

```bash
# List available simulators
xcrun simctl list devices

# Boot a simulator
xcrun simctl boot "iPhone 15 Pro"

# Open Simulator app
open -a Simulator

# Install app (requires .app bundle, not .ipa)
xcrun simctl install booted /path/to/App.app

# Launch app
xcrun simctl launch booted com.target.app

# Terminate app
xcrun simctl terminate booted com.target.app

# Uninstall app
xcrun simctl uninstall booted com.target.app

# Take screenshot
xcrun simctl io booted screenshot screenshot.png

# Record video
xcrun simctl io booted recordVideo recording.mp4
```

### Permission Management

```bash
# Grant all permissions
xcrun simctl privacy booted grant all com.target.app

# Grant specific permissions
xcrun simctl privacy booted grant photos com.target.app
xcrun simctl privacy booted grant camera com.target.app
xcrun simctl privacy booted grant location com.target.app
xcrun simctl privacy booted grant contacts com.target.app

# Revoke permissions
xcrun simctl privacy booted revoke all com.target.app

# Reset permissions
xcrun simctl privacy booted reset all com.target.app
```

### Push Notification Testing

```bash
# Send push notification (create payload.json first)
xcrun simctl push booted com.target.app payload.json

# Example payload.json:
# {
#   "aps": {
#     "alert": {
#       "title": "Test",
#       "body": "Test notification"
#     },
#     "badge": 1
#   }
# }
```

### Deep Link Testing

```bash
# Open URL scheme
xcrun simctl openurl booted "myapp://path/to/screen"

# Open universal link
xcrun simctl openurl booted "https://example.com/app-link"
```

### Network & Location

```bash
# Set location (latitude, longitude)
xcrun simctl location booted set 37.7749,-122.4194

# Clear location override
xcrun simctl location booted clear

# Trigger iCloud sync
xcrun simctl spawn booted notifyutil -p com.apple.cloudd.sync
```

### Accessibility Auditing

```bash
# Run accessibility audit
xcrun simctl ui booted accessibility audit

# Appearance mode
xcrun simctl ui booted appearance dark
xcrun simctl ui booted appearance light
```

---

## Maestro for iOS

Maestro works with iOS Simulator for UI automation testing.

### Setup

```bash
# Install Maestro
curl -fsSL "https://get.maestro.mobile.dev" | bash

# Download sample iOS app (has simulator architecture)
maestro download-samples
unzip -o samples/sample.zip -d /tmp/maestro_sample/

# Install in simulator
xcrun simctl install booted /tmp/maestro_sample/Wikipedia.app
```

### Basic Flow

```yaml
# ios_test.yaml
appId: org.wikimedia.wikipedia
tags:
  - ios
---
- launchApp
- takeScreenshot: step1_launch
- tapOn: "Search"
- inputText: "React Native"
- takeScreenshot: step2_search
- stopApp
```

### Run Tests

```bash
# Run single flow
maestro test ios_test.yaml

# Run with specific simulator
maestro test --platform ios --udid "DEVICE-UUID" ios_test.yaml

# Record video of flow
maestro record ios_test.yaml

# Start Maestro MCP server for AI agents
maestro mcp

# Find test results and screenshots
ls ~/.maestro/tests/
```

### Limitations

- Requires **full Xcode** (not Command Line Tools)
- Only works with **simulator-compatible .app** bundles
- Cannot test App Store IPAs directly
- For jailbroken device testing, use Frida instead
- Test results saved to `~/.maestro/tests/YYYY-MM-DD_HHMMSS/`

---

## Frida on iOS

### Option 1: Jailbroken Device (Recommended)

```bash
# Add Frida repo to Sileo/Cydia: https://build.frida.re/
# Install frida package (runs as daemon)

# From computer, verify
frida-ps -U

# Attach to app
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js

# Combined bypass (SSL + jailbreak detection)
cat scripts/frida/ios_ssl_bypass.js \
    scripts/frida/ios_jailbreak_bypass.js > /tmp/ios_all_bypasses.js
frida -U -f com.target.app -l /tmp/ios_all_bypasses.js
```

### Option 2: iOS Simulator (Limited)

Frida can attach to simulator processes but requires using **PID** (not device name):

```bash
# Launch app first
xcrun simctl launch booted com.bundle.id

# Find PID (simulator apps appear as local processes)
frida-ps | grep "AppName"
# Output: 59734  AppName

# Attach by PID (WORKS)
frida -p 59734 -l script.js

# NOTE: -D simulator does NOT work in recent Frida versions
# frida -D simulator -n "AppName"  # FAILS: Device 'simulator' not found
```

**Recommended approach for simulator:**
1. Launch app via `xcrun simctl launch booted bundle.id`
2. Find PID with `frida-ps | grep AppName`
3. Attach with `frida -p PID -l script.js`

### Option 3: Frida Gadget (Non-Jailbroken)

Requires macOS with Xcode and Apple Developer account.

```bash
# Patch IPA with objection
objection patchipa --source app.ipa --codesign-signature "Apple Development: your@email.com"

# Install with ios-deploy
ios-deploy --bundle app-frida-codesigned.ipa

# Connect
objection -g "App Name" explore
```

---

## Frida Scripts

Pre-built scripts in `scripts/frida/`:

| Script | Purpose |
|--------|---------|
| `ios_ssl_bypass.js` | SSL pinning bypass for iOS |
| `ios_jailbreak_bypass.js` | Jailbreak detection bypass |
| `universal_ssl_bypass.js` | Cross-platform SSL bypass |

See `scripts/frida/README.md` for full documentation.

### Usage

```bash
# Single script
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js

# Combined scripts
cat scripts/frida/ios_ssl_bypass.js \
    scripts/frida/ios_jailbreak_bypass.js > /tmp/all.js
frida -U -f com.target.app -l /tmp/all.js
```

---

## Objection for iOS

```bash
# Start objection
objection -g "Target App" explore

# iOS-specific commands:

# Disable SSL pinning
ios sslpinning disable

# List URL handlers
ios plist cat Info.plist | grep CFBundleURLSchemes -A 10

# Dump keychain
ios keychain dump

# List cookies
ios cookies get

# Dump NSUserDefaults
ios nsuserdefaults get

# Jailbreak detection bypass
ios jailbreak disable

# Search classes
ios hooking search classes Auth

# Watch method
ios hooking watch method "+[KeychainHelper getPassword]" --dump-args
```

---

## r2hermes Commands

```bash
# Get bundle info
r2 -qc 'pd:hi' main.jsbundle

# Decompile all functions
r2 -qc 'pd:ha' main.jsbundle > all.js

# Search strings
r2 -qc 'iz~api' main.jsbundle

# Fix hash after patching
r2 -wqc '.(fix-hbc)' main.jsbundle
```

---

## Troubleshooting

### IPA extraction fails

Some IPAs have non-standard structures (e.g., `.app` at root instead of in `Payload/`):
```bash
# Standard structure: Payload/AppName.app/
# Non-standard: AppName.app/ (at root)

# The analyze_ipa.py script handles both structures automatically
# For manual extraction, check both locations:
ls extracted_ipa/Payload/*.app/main.jsbundle 2>/dev/null || \
ls extracted_ipa/*.app/main.jsbundle
```

### Hermes version detection issues

The `analyze_ipa.py` script may sometimes report incorrect versions. **Always verify with `file` command:**
```bash
file main.jsbundle
# Output: Hermes JavaScript bytecode, version 96
```

The `file` command is the most reliable method for version detection.

### r2hermes fails on large bundles

Use `file` command for version detection:
```bash
file main.jsbundle
```

Use `strings` for extraction:
```bash
strings main.jsbundle | grep -E '^https?://'
```

For enhanced analysis on large bundles:
```bash
python scripts/enhanced_secret_scan.py main.jsbundle --json
```

### Secrets not detected (obfuscation)

If standard scanning misses secrets, they may be obfuscated:

```bash
# Check for Base64 encoded secrets
strings main.jsbundle | grep -oE '[A-Za-z0-9+/]{20,}={0,2}' | while read b64; do
  echo "$b64" | base64 -d 2>/dev/null | grep -q 'api\|key\|secret' && echo "Found: $b64"
done

# Check for hex encoded secrets
strings main.jsbundle | grep -oE '[0-9a-fA-F]{40,}' | while read hex; do
  echo "$hex" | xxd -r -p 2>/dev/null
done

# Use enhanced scanner for comprehensive detection
python scripts/enhanced_secret_scan.py main.jsbundle --category base64
```

### Frida can't connect to device

- Verify jailbreak is active
- Check Frida is installed from build.frida.re
- Try `killall frida-server && frida-server -D &`

### Frida can't connect to simulator

- Don't use `-D simulator` (doesn't work in recent Frida)
- Find PID with `frida-ps | grep AppName`
- Use `frida -p PID -l script.js`

### App crashes with Frida gadget

- Check code signing is correct
- Verify provisioning profile includes device UDID
- Try with `--pause` flag to attach debugger

### Xcode signing issues

```bash
# List available signing identities
security find-identity -v -p codesigning

# Check provisioning profiles
ls ~/Library/MobileDevice/Provisioning\ Profiles/

# Decode provisioning profile
security cms -D -i profile.mobileprovision
```

---

## Security Checklist

### Static Analysis
- [ ] Extract IPA and locate `main.jsbundle`
- [ ] Verify Hermes bytecode vs plain JavaScript (`file main.jsbundle`)
- [ ] Analyze bundle with r2hermes/hermes-dec
- [ ] Check `Info.plist` for URL schemes
- [ ] Check App Transport Security (ATS) exceptions
- [ ] Analyze PrivacyInfo.xcprivacy (iOS 17+)
- [ ] Analyze Keychain usage
- [ ] Check entitlements for sensitive capabilities

### Secret Scanning
- [ ] Run basic secret scanner (gitleaks)
- [ ] Run enhanced secret scanner (detects obfuscated secrets)
- [ ] **Manually verify all findings** (75% are false positives)
- [ ] Check RSA keys: PUBLIC vs PRIVATE
- [ ] Decode JWT tokens: auth vs config vs version manifest
- [ ] Verify hash patterns: secrets vs asset identifiers

### Native Binary Analysis
- [ ] Check for jailbreak detection paths in binary
- [ ] Identify SSL pinning libraries (Alamofire, TrustKit, Starscream)
- [ ] Check for MDM integration (Intune, AirWatch)
- [ ] Analyze WebRTC security if app has calls

### Anti-Tampering
- [ ] Check for anti-tampering code (jailbreak detection, Frida detection)
- [ ] Identify bypass requirements

### Dynamic Analysis
- [ ] Test on jailbroken device with Frida
- [ ] Bypass SSL pinning and jailbreak detection
- [ ] Intercept traffic with Burp Suite

---

## Platform Differences

| Aspect | Android | iOS |
|--------|---------|-----|
| Bundle file | `assets/index.android.bundle` | `main.jsbundle` |
| Package format | APK (zip) | IPA (zip) |
| Root access | Rooted emulator | Jailbroken device |
| Dynamic instrumentation | Frida + frida-server | Frida + jailbreak or gadget |
| Emulation | Android Emulator (full) | iOS Simulator (limited) |
| Analysis script | `analyze_apk.py` | `analyze_ipa.py` |
| Tool checker | `check_tools.py` | `check_tools_ios.py` |

**iOS Emulation Limitations:** Unlike Android, there is no viable iOS emulator for security testing. Projects like ipasim (dormant since 2019, Windows-only) and touchHLE (only supports iPhone OS 2.x-3.0 retro games) are NOT suitable. For dynamic analysis, use:
- **Jailbroken physical device** (recommended for full testing)
- **iOS Simulator** (for apps you can build yourself)
- **Frida Gadget** (inject into IPA for non-jailbroken devices)

---

## References

- [Palera1n](https://palera.in/) - Jailbreak for A8-A11
- [Dopamine](https://ellekit.space/dopamine/) - Jailbreak for A12+
- [nathanlr Guide](https://ios.cfw.guide/installing-nathanlr/) - Semi-jailbreak for A12+
- [OWASP MASTG - iOS](https://mas.owasp.org/MASTG/)
- [Frida iOS Codeshare](https://codeshare.frida.re/)
- [Frida iOS Simulator Issues](https://github.com/frida/frida/issues/1830)
- [Maestro iOS](https://maestro.mobile.dev/)
- [Mattermost Mobile Build](https://developers.mattermost.com/contribute/more-info/mobile/developer-setup/)
