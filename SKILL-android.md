---
name: hermes-android
description: Analyze Hermes bytecode in React Native Android apps. Disassemble, decompile, patch, and instrument .hbc files and index.android.bundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "android", "apk"
---

# Hermes Android Analysis

Toolkit for reverse engineering React Native **Android** applications compiled with Meta's Hermes JavaScript engine.

**For iOS analysis, see [SKILL-ios.md](SKILL-ios.md).**

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

# 5. Check for secrets
gitleaks dir ./analysis/apktool/ -v

# 6. Run with Frida
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js
```

**Key files to check:**
- `AndroidManifest.xml` - exported components, permissions
- `BuildConfig.java` - API keys, debug flags
- `res/xml/network_security_config.xml` - cleartext traffic, pinning
- `assets/index.android.bundle` - Hermes bytecode

---

## Tool Ecosystem

| Tool | Purpose | Install |
|------|---------|---------|
| **r2hermes** | Disassemble/decompile Hermes | `r2pm -ci r2hermes` |
| **hermes-dec** | Decompile to JS (binary: `hbc-decompiler`) | `pip install git+https://github.com/P1sec/hermes-dec` |
| **hbctool** | Disassemble/patch bytecode | `pip install hbctool` |
| **jadx** | Decompile DEX to Java | `brew install jadx` |
| **apktool** | Decode APK resources | `brew install apktool` |
| **frida** | Runtime instrumentation | `pip install frida-tools` |
| **objection** | APK patching, exploration | `pip install objection` |
| **gitleaks** | Secret scanning | `brew install gitleaks` |

### Version Compatibility

| frida-tools | frida-server | Notes |
|-------------|--------------|-------|
| 17.6.2 | 17.5.0 | Recommended combo |

**Note:** frida-tools 17.x has no `--no-pause` flag - app auto-resumes with `-f`.

---

## APK Analysis Workflow

### Phase 1: Architecture Check

```bash
# Check host architecture BEFORE downloading emulator images
uname -m
# arm64 → use arm64-v8a system images (Apple Silicon)
# x86_64 → use x86_64 system images (Intel)
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

### Phase 5: Hermes Analysis

```bash
# Decompile with r2hermes
r2 -qc 'pd:ha' index.android.bundle > decompiled.js

# Extract strings
r2 -qc 'iz~http' index.android.bundle

# For large bundles (>20MB), use strings command instead
strings index.android.bundle | grep -E 'api|endpoint|token'
```

### Phase 6: Enhanced Secret Scanning

Basic string matching misses obfuscated secrets. Use the enhanced scanner:

```bash
# Run enhanced secret scan (detects obfuscated secrets)
python scripts/enhanced_secret_scan.py index.android.bundle

# Or run with full APK analysis
python scripts/analyze_apk.py target.apk --enhanced
```

The enhanced scanner detects:
- **Base64 encoded secrets** - decodes and checks for sensitive data
- **Hex encoded secrets** - decodes hex strings
- **Character code arrays** - detects `[65, 75, 73, ...]` patterns (AWS keys, etc.)
- **Split string fragments** - finds `sk_test_`, `AKIA`, `ghp_` prefixes
- **Anti-tampering indicators** - root detection, Frida detection, SSL pinning

### Phase 7: Obfuscation Analysis

```bash
# Detect obfuscation techniques
python scripts/detect_obfuscation.py target.apk

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

### Phase 8: Anti-Tampering Detection

Apps may include protections that affect analysis:

```bash
# Check for anti-tampering code in bundle
strings index.android.bundle | grep -iE 'checkRoot|frida|jailbreak|emulator|integrity'

# Common anti-tampering indicators:
# - checkRootStatus, isRooted, RootBeer
# - checkFrida, frida-server, frida-agent
# - checkDebugger, isDebuggerAttached
# - checkEmulator, goldfish, ranchu
# - SSL_PINS, certificatePinning
```

**Bypassing anti-tampering:**
```bash
# Use root bypass Frida script
frida -U -f com.target.app -l scripts/frida/root_bypass.js

# Combined bypass for stubborn apps
cat scripts/frida/universal_ssl_bypass.js \
    scripts/frida/root_bypass.js \
    scripts/frida/gms_firebase_bypass.js > /tmp/all.js
frida -U -f com.target.app -l /tmp/all.js
```

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

### Install Frida Server

```bash
# Check device architecture
adb shell getprop ro.product.cpu.abi  # arm64-v8a, x86_64, etc.

# Download matching frida-server
curl -sL "https://github.com/frida/frida/releases/download/17.5.0/frida-server-17.5.0-android-arm64.xz" -o /tmp/frida-server.xz
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

# Combined
cat scripts/frida/universal_ssl_bypass.js \
    scripts/frida/root_bypass.js \
    scripts/frida/gms_firebase_bypass.js > /tmp/all_bypasses.js
frida -U -f com.target.app -l /tmp/all_bypasses.js
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

## r2hermes Commands

```bash
# Get bundle info
r2 -qc 'pd:hi' bundle.hbc

# Decompile all functions
r2 -qc 'pd:ha' bundle.hbc > all.js

# Decompile specific function
r2 -qc 'pd:hf 123' bundle.hbc

# Search strings
r2 -qc 'iz~api' bundle.hbc

# Fix hash after patching
r2 -wqc '.(fix-hbc)' bundle.hbc
```

---

## Troubleshooting

### Hermes version detection issues

The `analyze_apk.py` script may sometimes report incorrect versions. **Always verify with `file` command:**
```bash
file index.android.bundle
# Output: Hermes JavaScript bytecode, version 96
```

The `file` command is the most reliable method for version detection.

### r2hermes fails on large bundles

Use `strings` for extraction:
```bash
strings index.android.bundle | grep -E '^https?://'
```

For enhanced analysis on large bundles:
```bash
python scripts/enhanced_secret_scan.py index.android.bundle --json
```

### Secrets not detected (obfuscation)

If standard scanning misses secrets, they may be obfuscated:

```bash
# Check for Base64 encoded secrets
strings bundle | grep -oE '[A-Za-z0-9+/]{20,}={0,2}' | while read b64; do
  echo "$b64" | base64 -d 2>/dev/null | grep -q 'api\|key\|secret' && echo "Found: $b64"
done

# Check for hex encoded secrets
strings bundle | grep -oE '[0-9a-fA-F]{40,}' | while read hex; do
  echo "$hex" | xxd -r -p 2>/dev/null
done

# Use enhanced scanner for comprehensive detection
python scripts/enhanced_secret_scan.py bundle --category base64
```

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

### Secret scanner false positives

gitleaks/trufflehog produce false positives:
- Unicode emoji sequences
- Build verification tokens
- Base64-encoded non-secrets

Always manually review findings.

---

## Security Checklist

- [ ] `AndroidManifest.xml` - exported components, allowBackup
- [ ] `network_security_config.xml` - cleartext traffic, cert pinning
- [ ] `BuildConfig.java` - API keys, debug flags
- [ ] `strings.xml` - hardcoded secrets
- [ ] Hermes bundle - API endpoints, tokens
- [ ] Deep link handlers - intent injection
- [ ] WebView usage - JavaScript interfaces

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

---

## References

- [OWASP MASTG - Android](https://mas.owasp.org/MASTG/)
- [Frida Android](https://frida.re/docs/android/)
- [Frida Codeshare](https://codeshare.frida.re/)
- [Hermes GitHub](https://github.com/facebook/hermes)
- [hermes-dec](https://github.com/nickcopi/hermes-dec)
- [Maestro](https://maestro.mobile.dev/)
