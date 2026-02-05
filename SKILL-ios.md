---
name: hermes-ios
description: Analyze Hermes bytecode in React Native iOS apps. Disassemble, decompile, patch, and instrument .hbc files and main.jsbundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "ios", "ipa", "jailbreak"
---

# Hermes iOS Analysis

Toolkit for reverse engineering React Native **iOS** applications compiled with Meta's Hermes JavaScript engine.

---

## Quick Start

```bash
# 1. Extract IPA
unzip -o app.ipa -d extracted_ipa/

# 2. Find and verify Hermes bundle
file extracted_ipa/Payload/*.app/main.jsbundle
# Expected: "Hermes JavaScript bytecode, version 96"

# 3. Analyze bundle
r2 -qc 'pd:ha' main.jsbundle > decompiled.js

# 4. On jailbroken device, run with Frida
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

**Key files to check:**
- `main.jsbundle` - Hermes bytecode
- `Info.plist` - URL schemes, ATS exceptions
- Entitlements - sensitive capabilities
- Keychain usage

---

## Platform Differences

| Aspect | Android | iOS |
|--------|---------|-----|
| Bundle file | `assets/index.android.bundle` | `main.jsbundle` |
| Package format | APK (zip) | IPA (zip) |
| Root access | Rooted emulator | Jailbroken device |
| Dynamic instrumentation | Frida + frida-server | Frida + jailbreak or gadget |

**iOS Emulation Limitations:** Unlike Android, there is no viable iOS emulator for security testing. Projects like ipasim (dormant since 2019, Windows-only) and touchHLE (only supports iPhone OS 2.x-3.0 retro games) are NOT suitable. For dynamic analysis, use:
- **Jailbroken physical device** (recommended for full testing)
- **iOS Simulator** (for apps you can build yourself - see below)
- **Frida Gadget** (inject into IPA for non-jailbroken devices)

---

## Tool Ecosystem

| Tool | Purpose | Install |
|------|---------|---------|
| **r2hermes** | Disassemble/decompile Hermes | `r2pm -ci r2hermes` |
| **hermes-dec** | Decompile to JS (binary: `hbc-decompiler`) | `pip install git+https://github.com/P1sec/hermes-dec` |
| **hbctool** | Disassemble/patch bytecode | `pip install hbctool` |
| **frida** | Runtime instrumentation | `pip install frida-tools` |
| **objection** | IPA patching, exploration | `pip install objection` |

---

## IPA Extraction

### Extract Bundle from IPA

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

### Analyze iOS Bundle

Same tools work on iOS bundles:

```bash
# Decompile with r2hermes
r2 -qc 'pd:ha' main.jsbundle > decompiled.js

# Extract strings
r2 -qc 'iz~http' main.jsbundle

# Use hermes-dec
hbc-decompiler main.jsbundle output.js

# For large bundles
strings main.jsbundle | grep -E '^https?://'
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

## Frida on iOS

### Option 1: Jailbroken Device

```bash
# Add Frida repo to Sileo/Cydia: https://build.frida.re/
# Install frida package (runs as daemon)

# From computer, verify
frida-ps -U

# Attach to app
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

### Option 2: Frida Gadget (Non-Jailbroken)

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

## SSL Pinning Bypass

### Frida Script (ios_ssl_bypass.js)

```javascript
if (ObjC.available) {
    console.log("[*] iOS SSL Pinning Bypass");

    // NSURLSession TLS bypass
    try {
        var NSURLSessionConfiguration = ObjC.classes.NSURLSessionConfiguration;
        Interceptor.attach(NSURLSessionConfiguration['- setTLSMinimumSupportedProtocol:'].implementation, {
            onEnter: function(args) {
                console.log("[+] Bypassing TLS minimum protocol");
            }
        });
    } catch(e) {}

    // TrustKit bypass
    try {
        var TSKPinningValidator = ObjC.classes.TSKPinningValidator;
        if (TSKPinningValidator) {
            Interceptor.attach(TSKPinningValidator['- evaluateTrust:forHostname:'].implementation, {
                onLeave: function(retval) {
                    console.log("[+] TrustKit bypassed");
                    retval.replace(0);
                }
            });
        }
    } catch(e) {}

    // AFNetworking bypass
    try {
        var AFSecurityPolicy = ObjC.classes.AFSecurityPolicy;
        if (AFSecurityPolicy) {
            Interceptor.attach(AFSecurityPolicy['- setSSLPinningMode:'].implementation, {
                onEnter: function(args) {
                    args[2] = ptr(0); // AFSSLPinningModeNone
                    console.log("[+] AFNetworking pinning disabled");
                }
            });
        }
    } catch(e) {}

    // Generic SecTrust bypass
    try {
        var SecTrustEvaluateWithError = Module.findExportByName("Security", "SecTrustEvaluateWithError");
        if (SecTrustEvaluateWithError) {
            Interceptor.attach(SecTrustEvaluateWithError, {
                onLeave: function(retval) {
                    retval.replace(1);
                    console.log("[+] SecTrustEvaluateWithError bypassed");
                }
            });
        }
    } catch(e) {}

    console.log("[*] iOS SSL bypass hooks installed");
}
```

---

## Jailbreak Detection Bypass

### Frida Script (ios_jailbreak_bypass.js)

```javascript
if (ObjC.available) {
    console.log("[*] iOS Jailbreak Bypass");

    var jailbreakPaths = [
        "/Applications/Cydia.app",
        "/Applications/Sileo.app",
        "/usr/sbin/sshd",
        "/usr/bin/ssh",
        "/bin/bash",
        "/etc/apt",
        "/private/var/lib/apt",
        "/private/var/lib/cydia",
        "/var/jb"
    ];

    // Hook fileExistsAtPath
    var NSFileManager = ObjC.classes.NSFileManager;
    Interceptor.attach(NSFileManager['- fileExistsAtPath:'].implementation, {
        onEnter: function(args) {
            this.path = ObjC.Object(args[2]).toString();
        },
        onLeave: function(retval) {
            for (var i = 0; i < jailbreakPaths.length; i++) {
                if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                    console.log("[+] Blocked: " + this.path);
                    retval.replace(0);
                    return;
                }
            }
        }
    });

    // Hook canOpenURL for cydia://
    var UIApplication = ObjC.classes.UIApplication;
    Interceptor.attach(UIApplication['- canOpenURL:'].implementation, {
        onEnter: function(args) {
            this.url = ObjC.Object(args[2]).toString();
        },
        onLeave: function(retval) {
            if (this.url.indexOf("cydia://") !== -1 ||
                this.url.indexOf("sileo://") !== -1) {
                console.log("[+] Blocked canOpenURL: " + this.url);
                retval.replace(0);
            }
        }
    });

    // Block fork()
    var fork = Module.findExportByName(null, "fork");
    if (fork) {
        Interceptor.attach(fork, {
            onLeave: function(retval) {
                retval.replace(-1);
            }
        });
    }

    console.log("[*] Jailbreak bypass hooks installed");
}
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

### r2hermes fails on large bundles

Use `file` command for version detection:
```bash
file main.jsbundle
```

Use `strings` for extraction:
```bash
strings main.jsbundle | grep -E '^https?://'
```

### Frida can't connect

- Verify jailbreak is active
- Check Frida is installed from build.frida.re
- Try `killall frida-server && frida-server -D &`

### App crashes with Frida gadget

- Check code signing is correct
- Verify provisioning profile includes device UDID
- Try with `--pause` flag to attach debugger

---

## Security Checklist

- [ ] Extract IPA and locate `main.jsbundle`
- [ ] Verify Hermes bytecode vs plain JavaScript
- [ ] Analyze bundle with r2hermes/hermes-dec
- [ ] Check `Info.plist` for URL schemes
- [ ] Check App Transport Security (ATS) exceptions
- [ ] Analyze Keychain usage
- [ ] Check entitlements for sensitive capabilities
- [ ] Test on jailbroken device with Frida
- [ ] Bypass SSL pinning and jailbreak detection
- [ ] Intercept traffic with Burp Suite

---

## References

- [Palera1n](https://palera.in/) - Jailbreak for A8-A11
- [Dopamine](https://ellekit.space/dopamine/) - Jailbreak for A12+
- [OWASP MASTG - iOS](https://mas.owasp.org/MASTG/)
- [Frida iOS Codeshare](https://codeshare.frida.re/)
