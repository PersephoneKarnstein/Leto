---
name: hermes-android
description: Analyze Hermes bytecode in React Native Android apps. Disassemble, decompile, patch, and instrument .hbc files and index.android.bundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "android", "apk"
---

# Hermes Android Analysis

Toolkit for reverse engineering React Native **Android** applications compiled with Meta's Hermes JavaScript engine.

**For iOS analysis, see [SKILL-ios.md](SKILL-ios.md).**
**For shared methodology (secret triage, r2hermes, deep analysis), see [SKILL-common.md](SKILL-common.md).**

---

## Quick Start

```bash
# 1. Check tools
python scripts/check_tools.py

# 2. Analyze APK
python scripts/analyze_apk.py target.apk --decompile

# 3. Verify Hermes version (most reliable method)
file ./analysis/extracted/assets/index.android.bundle

# 4. Decompile Java code
jadx target.apk -d jadx_output/

# 5. Check for secrets (gitleaks or betterleaks)
gitleaks dir ./analysis/apktool/ -v

# 6. Run with Frida
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js
```

**Key files to check:**
- `AndroidManifest.xml` -- exported components, permissions
- `BuildConfig.java` -- API keys, debug flags
- `res/xml/network_security_config.xml` -- cleartext traffic, pinning
- `assets/index.android.bundle` -- Hermes bytecode

---

## Android-Specific Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **jadx** | Decompile DEX to Java | `brew install jadx` |
| **apktool** | Decode APK resources | `brew install apktool` |

For shared tools (r2hermes, hermes-dec, frida, etc.), see [SKILL-common.md](SKILL-common.md#shared-tool-ecosystem).

---

## APK Analysis Workflow

### Phase 1: Architecture Check

```bash
# Check host architecture BEFORE downloading emulator images
uname -m
# arm64 -> use arm64-v8a system images (Apple Silicon)
# x86_64 -> use x86_64 system images (Intel)
```

### Phase 2: Obtain APK

**Recommended sources (in order):**
1. Official GitHub releases (e.g., Mattermost)
2. ADB from device: `adb shell pm path com.app && adb pull /path/to/base.apk`
3. APKMirror/APKPure (may block automation)

### Phase 3: Automated Analysis

```bash
python scripts/analyze_apk.py target.apk --decompile

# IMPORTANT: Verify Hermes version with file command
file ./analysis/extracted/assets/index.android.bundle
# Expected: "Hermes JavaScript bytecode, version 96"
```

### Phase 4: Static Analysis

```bash
# JADX decompilation
jadx target.apk -d jadx_output/

# Secret scanning (review for false positives!)
gitleaks dir ./analysis/apktool/ -v > gitleaks_results.txt

# Manual secret check (scanners miss these)
grep -iE 'api.*key|firebase|google_api' ./analysis/apktool/res/values/strings.xml
cat jadx_output/sources/*/BuildConfig.java

# String extraction from Hermes bundle
strings ./analysis/extracted/assets/index.android.bundle | grep -E '^https?://' | sort -u
```

### Phase 5: Hermes + Secret + Obfuscation Analysis

See [SKILL-common.md](SKILL-common.md) for:
- [r2hermes commands](SKILL-common.md#r2hermes-commands)
- [Enhanced secret scanning](SKILL-common.md#enhanced-secret-scanning)
- [Obfuscation analysis](SKILL-common.md#obfuscation-analysis)
- [Deep analysis / false positive triage](SKILL-common.md#deep-analysis-manual-verification)
- [Source map recovery](SKILL-common.md#source-map-recovery)
- [Traffic capture and correlation](SKILL-common.md#traffic-capture-and-correlation)

---

## Emulator Setup

### Create Rooted Test Emulator

```bash
# Check architecture first
uname -m  # arm64 = Apple Silicon, x86_64 = Intel

# Install ARM64 image (Apple Silicon)
sdkmanager "system-images;android-30;google_apis;arm64-v8a"

# Or x86_64 (Intel)
sdkmanager "system-images;android-30;google_apis;x86_64"

# Create AVD
avdmanager create avd -n pentest_api30 -k "system-images;android-30;google_apis;arm64-v8a" -d pixel_6

# Start with writable system
emulator -avd pentest_api30 -writable-system &
```

**Emulator trade-offs:**
- `google_apis` images: allow root/Frida but NO Google Play Services
- `google_apis_playstore` images: have Play Services but locked, no root
- Apps depending on Firebase/GMS show black screens on pentest emulators
- **Solution**: Patch APK with Objection: `objection patchapk -s target.apk`

### Install Frida Server

```bash
# Check device architecture
adb shell getprop ro.product.cpu.abi  # arm64-v8a, x86_64, etc.

# Download matching frida-server (use current version)
curl -sL "https://github.com/frida/frida/releases/download/17.8.0/frida-server-17.8.0-android-arm64.xz" -o /tmp/frida-server.xz
xz -d /tmp/frida-server.xz

# Push and start
adb root
adb push /tmp/frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell "/data/local/tmp/frida-server -D &"

# Verify
frida-ps -U
```

---

## Dynamic Analysis

### Frida Scripts

```bash
# SSL pinning bypass
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js

# Root detection bypass
frida -U -f com.target.app -l scripts/frida/root_bypass.js

# GMS/Firebase bypass (for non-Play Store emulators)
frida -U -f com.target.app -l scripts/frida/gms_firebase_bypass.js

# Combined bypass
cat scripts/frida/universal_ssl_bypass.js \
    scripts/frida/root_bypass.js \
    scripts/frida/gms_firebase_bypass.js > /tmp/all_bypasses.js
frida -U -f com.target.app -l /tmp/all_bypasses.js

# React Native bridge tracing
frida -U -f com.target.app -l scripts/frida/rn_bridge_trace.js
```

**Note:** Some hooks may fail on specific apps due to different class structures. Check error output and adapt.

### Maestro UI Automation

```bash
# Install
curl -fsSL "https://get.maestro.mobile.dev" | bash

# IMPORTANT: Screenshot first to see actual UI
# discovery_flow.yaml
appId: com.target.app
---
- launchApp
- takeScreenshot: screen1_initial
- tapOn:
    index: 0
- takeScreenshot: screen2_after_tap
```

Then build actual flows based on observed UI.

### Burp Suite Setup

```bash
# Export Burp cert and convert
openssl x509 -inform DER -in burp_cert.der -out burp_cert.pem
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp_cert.pem | head -1)
mv burp_cert.pem $HASH.0

# Push to emulator (requires writable system)
adb root
adb remount
adb push $HASH.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/$HASH.0

# Set proxy
adb shell settings put global http_proxy 10.0.2.2:8080
```

---

## APK Patching

### Objection (Quick Method)

```bash
# Inject Frida gadget
objection patchapk -s target.apk

# Install patched APK
adb install target.objection.apk
```

### Manual Smali Patching

```bash
# Decode
apktool d target.apk -o decoded/

# Edit smali files...

# Rebuild
apktool b decoded/ -o patched.apk

# Sign
zipalign -v 4 patched.apk aligned.apk
apksigner sign --ks debug.keystore aligned.apk
```

---

## Troubleshooting

### App stuck on splash (GMS dependency)

Options:
1. Patch APK with Objection: `objection patchapk -s target.apk`
2. Use `gms_firebase_bypass.js` Frida script
3. Install OpenGApps (complex, may cause instability)

### Frida hooks failing

Some hooks fail due to different class structures. Check:
```javascript
Java.perform(function() {
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes("OkHttp")) console.log(className);
        },
        onComplete: function() {}
    });
});
```

For shared troubleshooting (Hermes version detection, large bundles, obfuscated secrets), see [SKILL-common.md](SKILL-common.md#hermes-version-detection).

---

## Security Checklist

### Static Analysis
- [ ] `AndroidManifest.xml` -- exported components, allowBackup
- [ ] `network_security_config.xml` -- cleartext traffic, cert pinning
- [ ] `BuildConfig.java` -- API keys, debug flags
- [ ] `strings.xml` -- hardcoded secrets
- [ ] Hermes bundle -- API endpoints, tokens
- [ ] Deep link handlers -- intent injection
- [ ] WebView usage -- JavaScript interfaces

### Secret & Obfuscation Analysis
- [ ] Run gitleaks/betterleaks + enhanced scanner
- [ ] Run obfuscation detector
- [ ] **Manually verify all findings** ([false positive triage](SKILL-common.md#false-positive-checklist))

### Dynamic Analysis
- [ ] Test on rooted emulator with Frida
- [ ] Bypass SSL pinning and root detection
- [ ] Intercept traffic with Burp Suite / mitmproxy
- [ ] Run bridge tracer for sensitive operations
