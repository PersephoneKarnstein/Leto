---
name: hermes-ios
description: Analyze Hermes bytecode in React Native iOS apps. Disassemble, decompile, patch, and instrument .hbc files and main.jsbundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "ios", "ipa", "jailbreak"
---

# Hermes iOS Analysis

Toolkit for reverse engineering React Native **iOS** applications compiled with Meta's Hermes JavaScript engine.

**For Android analysis, see [SKILL-android.md](SKILL-android.md).**
**For shared methodology (secret triage, r2hermes, deep analysis), see [SKILL-common.md](SKILL-common.md).**

---

## Quick Start

```bash
# 1. Check tools
python scripts/check_tools_ios.py

# 2. Analyze IPA (with enhanced secret scanning)
python scripts/analyze_ipa.py target.ipa --decompile --enhanced

# 3. Verify Hermes version (most reliable method)
file ./target_analysis/extracted/Payload/*.app/main.jsbundle

# 4. Check for secrets (gitleaks or betterleaks)
gitleaks dir ./target_analysis/extracted/ -v

# 5. Run with Frida (jailbroken device)
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

**Key files to check:**
- `main.jsbundle` -- Hermes bytecode
- `Info.plist` -- URL schemes, ATS exceptions
- `Entitlements` -- Sensitive capabilities
- `PrivacyInfo.xcprivacy` -- Privacy manifest (iOS 17+)

---

## Critical: iOS Testing Approaches

Unlike Android, iOS has fundamental platform restrictions.

### App Store IPAs Cannot Run in Simulator

**This is the most important iOS limitation.** App Store/distribution IPAs are built for device architecture only (arm64-device) and will NOT run in iOS Simulator.

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

## iOS-Specific Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **Xcode** | iOS Simulator, build tools | App Store (15GB+) |
| **Maestro** | UI automation | `curl -fsSL "https://get.maestro.mobile.dev" \| bash` |

For shared tools (r2hermes, hermes-dec, frida, etc.), see [SKILL-common.md](SKILL-common.md#shared-tool-ecosystem).

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
python scripts/check_tools_ios.py --install-help
xcode-select -p
xcrun simctl list runtimes  # Should show iOS runtimes
```

### Phase 2: Automated Analysis

```bash
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

### Phase 3: Static Analysis

```bash
# Scan extracted IPA for secrets
gitleaks dir ./target_analysis/extracted/ -v > gitleaks_results.txt

# Check plist files for hardcoded values
plutil -p ./target_analysis/extracted/Payload/*.app/Info.plist | grep -iE 'api|key|secret'

# String extraction from Hermes bundle
strings ./target_analysis/extracted/Payload/*.app/main.jsbundle | grep -E '^https?://' | sort -u
```

### Phase 4: Hermes + Secret + Obfuscation Analysis

See [SKILL-common.md](SKILL-common.md) for:
- [r2hermes commands](SKILL-common.md#r2hermes-commands)
- [Enhanced secret scanning](SKILL-common.md#enhanced-secret-scanning)
- [Obfuscation analysis](SKILL-common.md#obfuscation-analysis)
- [Deep analysis / false positive triage](SKILL-common.md#deep-analysis-manual-verification)
- [Source map recovery](SKILL-common.md#source-map-recovery)
- [Traffic capture and correlation](SKILL-common.md#traffic-capture-and-correlation)

### Phase 5: Native Binary Analysis (iOS-Specific)

```bash
APP_BINARY="./extracted/Payload/*.app/AppName"

# Check for jailbreak detection paths
strings "$APP_BINARY" | grep -E '/Applications/Cydia|MobileSubstrate|/var/lib/cydia'

# Known jailbreak detection paths (from enterprise apps):
# - /Applications/Cydia.app
# - /Library/MobileSubstrate/MobileSubstrate.dylib
# - /private/var/lib/cydia
# - /System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist

# Check for SSL pinning libraries
strings "$APP_BINARY" | grep -iE 'PinnedCertificate|TrustEvaluator|CertificatePinning'

# Common implementations:
# - Alamofire: PinnedCertificatesTrustEvaluator
# - Starscream: CertificatePinning (WebSocket)
# - TrustKit: TSKPinningValidator
```

### Phase 6: Enterprise Security Patterns

Enterprise apps often include MDM and advanced security:

```bash
# Check for Microsoft Intune MDM
ls ./extracted/Payload/*.app/Frameworks/ | grep -i intune

# Check Info.plist for MDM settings
plutil -p ./extracted/Payload/*.app/Info.plist | grep -iE 'intune|mdm|adal'

# Check for WebRTC security (voice/video calls)
ls ./extracted/Payload/*.app/Frameworks/ | grep -i webrtc
```

### Phase 7: Dynamic Analysis (Choose One)

**Option A: Jailbroken Device** (recommended for real apps)
```bash
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

**Option B: Simulator** (apps you build)
```bash
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
xcrun simctl install booted /path/to/App.app
xcrun simctl launch booted com.bundle.id
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
unzip -o app.ipa -d extracted_ipa/

# Find Hermes bundle (handles non-standard structures)
ls extracted_ipa/Payload/*.app/main.jsbundle 2>/dev/null || \
ls extracted_ipa/*.app/main.jsbundle

# Verify it's Hermes bytecode
file main.jsbundle
# "Hermes JavaScript bytecode, version XX" = Hermes
# "ASCII text" = Plain JavaScript
```

---

## Info.plist & Privacy Analysis

```bash
# Check ATS exceptions (allows HTTP)
plutil -convert xml1 extracted_ipa/Payload/*.app/Info.plist -o Info_readable.plist
grep -A 10 "NSAppTransportSecurity" Info_readable.plist

# Check URL schemes (deep links)
grep -A 20 "CFBundleURLTypes" Info_readable.plist

# Check entitlements
codesign -d --entitlements :- extracted_ipa/Payload/*.app/ 2>/dev/null

# Privacy manifest (iOS 17+)
find extracted_ipa/ -name "PrivacyInfo.xcprivacy"
plutil -p extracted_ipa/Payload/*.app/PrivacyInfo.xcprivacy
# Key fields: NSPrivacyAccessedAPITypes, NSPrivacyTrackingDomains, NSPrivacyCollectedDataTypes
```

---

## Jailbreak Tools

| Tool | Devices | iOS Versions | Type |
|------|---------|--------------|------|
| **Palera1n** | A8-A11 | 15.0-18.x | Semi-tethered |
| **Dopamine** | A9-A11 (arm64) | 15.0-16.6.1 | Semi-untethered |
| **Dopamine** | A12-A14 (arm64e) | 15.0-16.5.1 | Semi-untethered |
| **Dopamine** | A15-A16/M2 | 15.0-16.5 | Semi-untethered |
| **nathanlr** | A12+ | 16.5.1-17.0 | Semi-jailbreak |
| **Checkra1n** | A7-A11 | 12.0-14.8.1 | Semi-tethered |

**nathanlr note:** Semi-jailbreak with limited functionality (no tweak injection). Useful for Frida access on newer devices. Install via [ios.cfw.guide](https://ios.cfw.guide/installing-nathanlr/).

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

## Frida on iOS

### Option 1: Jailbroken Device (Recommended)

```bash
# Add Frida repo to Sileo/Cydia: https://build.frida.re/
# Install frida package (runs as daemon)

frida-ps -U  # Verify connection

# SSL + jailbreak bypass combo
cat scripts/frida/ios_ssl_bypass.js \
    scripts/frida/ios_jailbreak_bypass.js > /tmp/ios_all_bypasses.js
frida -U -f com.target.app -l /tmp/ios_all_bypasses.js

# Bridge tracing
frida -U -f com.target.app -l scripts/frida/rn_bridge_trace.js
```

### Option 2: iOS Simulator (Limited)

Frida can attach to simulator processes using **PID** (not device name):

```bash
xcrun simctl launch booted com.bundle.id
frida-ps | grep "AppName"       # Find PID
frida -p <PID> -l script.js     # Attach by PID

# NOTE: frida -D simulator does NOT work in recent Frida versions
```

### Option 3: Frida Gadget (Non-Jailbroken)

```bash
objection patchipa --source app.ipa --codesign-signature "Apple Development: your@email.com"
ios-deploy --bundle app-frida-codesigned.ipa
objection -g "App Name" explore
```

---

## Objection for iOS

```bash
objection -g "Target App" explore

# Key commands:
ios sslpinning disable              # Disable SSL pinning
ios keychain dump                   # Dump keychain
ios cookies get                     # List cookies
ios nsuserdefaults get              # Dump NSUserDefaults
ios jailbreak disable               # Jailbreak detection bypass
ios hooking search classes Auth     # Search classes
ios hooking watch method "+[KeychainHelper getPassword]" --dump-args
```

---

## Troubleshooting

### Frida can't connect to device

- Verify jailbreak is active
- Check Frida is installed from build.frida.re
- Try `killall frida-server && frida-server -D &`

### Frida can't connect to simulator

- Don't use `-D simulator` (doesn't work in recent Frida)
- Find PID with `frida-ps | grep AppName`
- Use `frida -p PID -l script.js`

### App crashes with Frida gadget

- Check code signing: `security find-identity -v -p codesigning`
- Verify provisioning profile includes device UDID
- Decode profile: `security cms -D -i profile.mobileprovision`

For shared troubleshooting (Hermes version detection, large bundles, obfuscated secrets), see [SKILL-common.md](SKILL-common.md#hermes-version-detection).

---

## Security Checklist

### Static Analysis
- [ ] Extract IPA and locate `main.jsbundle`
- [ ] Verify Hermes bytecode vs plain JavaScript (`file main.jsbundle`)
- [ ] Check `Info.plist` for URL schemes and ATS exceptions
- [ ] Analyze PrivacyInfo.xcprivacy (iOS 17+)
- [ ] Check entitlements for sensitive capabilities
- [ ] Analyze native binary for jailbreak detection / SSL pinning
- [ ] Check for MDM integration (Intune, AirWatch)

### Secret & Obfuscation Analysis
- [ ] Run gitleaks/betterleaks + enhanced scanner
- [ ] Run obfuscation detector
- [ ] **Manually verify all findings** ([false positive triage](SKILL-common.md#false-positive-checklist))

### Dynamic Analysis
- [ ] Test on jailbroken device with Frida
- [ ] Bypass SSL pinning and jailbreak detection
- [ ] Intercept traffic with Burp Suite / mitmproxy
- [ ] Run bridge tracer for sensitive operations

---

## References

- [Palera1n](https://palera.in/) -- Jailbreak for A8-A11
- [Dopamine](https://ellekit.space/dopamine/) -- Jailbreak for A12+
- [nathanlr Guide](https://ios.cfw.guide/installing-nathanlr/) -- Semi-jailbreak for A12+
- [OWASP MASTG - iOS](https://mas.owasp.org/MASTG/)
- [Frida iOS](https://frida.re/docs/ios/)
- [Frida CodeShare](https://codeshare.frida.re/)
