# Hermes Bytecode Analysis Skills

**Comprehensive penetration testing toolkit** for React Native applications compiled with Hermes. Available as two separate skills for Android and iOS.

> **Key Insight from Testing:** Analysis of 13 real-world apps revealed a **75% false positive rate** in automated secret detection. RSA PUBLIC keys (not private), JWT version manifests (not auth tokens), and asset identifier hashes are commonly misidentified. **Always manually verify findings.** See the [Deep Analysis methodology](SKILL-android.md#phase-9-deep-analysis-manual-verification) in the skills.

## Why "Lêtô"?

This repository is named **Lêtô** (Λητώ) in honor of the Greek titaness who confronted Hermes at Troy. In Homer's *Iliad*, when the gods chose sides in the Trojan War, Hermes faced Leto on the battlefield, though he declined combat with the mother of Apollo and Artemis, saying "Off you go, and make loud boasts among the deathless gods that you have conquered me by strength and force." (Wilson, 2023)

## Installation

Download from GitLab CI artifacts:
- `hermes-android.zip` - Android APK analysis
- `hermes-ios.zip` - iOS IPA analysis

Both skills can be installed simultaneously (different names in frontmatter).

## Quick Start

### Android
```bash
# 1. Check tools
python scripts/check_tools.py

# 2. Analyze APK (with enhanced secret scanning)
python scripts/analyze_apk.py target.apk --decompile --enhanced

# 3. Verify Hermes version
file ./analysis/extracted/assets/index.android.bundle

# 4. IMPORTANT: Manually verify any secret findings (75% are false positives)
# - Check RSA keys: PUBLIC vs PRIVATE
# - Decode JWT tokens: auth vs config/version manifest
# - Verify hash patterns: secrets vs asset identifiers

# 5. Run with Frida
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js
```

### iOS
```bash
# 1. Check tools
python scripts/check_tools_ios.py

# 2. Analyze IPA (with enhanced secret scanning)
python scripts/analyze_ipa.py target.ipa --decompile --enhanced

# 3. Verify Hermes version
file ./target_analysis/extracted/Payload/*.app/main.jsbundle

# 4. IMPORTANT: Manually verify any secret findings (75% are false positives)
# - Check RSA keys: PUBLIC vs PRIVATE
# - Decode JWT tokens: auth vs config/version manifest
# - Verify hash patterns: secrets vs asset identifiers

# 5. Run with Frida (jailbroken device)
frida -U -f com.target.app -l scripts/frida/ios_ssl_bypass.js
```

## Directory Structure

```
hermes-skill/
├── SKILL-android.md      # Android skill documentation
├── SKILL-ios.md          # iOS skill documentation
├── README.md             # This file
├── scripts/
│   ├── check_tools.py        # Android tool checker
│   ├── check_tools_ios.py    # iOS tool checker
│   ├── analyze_apk.py        # Automated APK analysis
│   ├── analyze_ipa.py        # Automated IPA analysis
│   ├── analyze_bundle.py     # Hermes bundle analysis
│   ├── sourcemap_recovery.py # Source map detection/extraction
│   ├── detect_obfuscation.py # Obfuscation detection
│   ├── extract_bundle.py     # Extract from APK/device
│   ├── patch_and_repack.py   # Patch and rebuild APK
│   ├── frida/
│   │   ├── universal_ssl_bypass.js  # SSL pinning bypass (40+ methods)
│   │   ├── root_bypass.js           # Root/emulator detection bypass
│   │   ├── ios_ssl_bypass.js        # iOS SSL pinning bypass
│   │   ├── ios_jailbreak_bypass.js  # iOS jailbreak detection bypass
│   │   ├── gms_firebase_bypass.js   # GMS/Firebase bypass
│   │   ├── rn_bridge_trace.js       # React Native bridge tracer
│   │   ├── hermes_hooks.js          # React Native bridge hooks
│   │   └── detect_frameworks.js     # Framework detection
│   ├── traffic/
│   │   ├── mitmproxy_capture.py     # Traffic capture addon
│   │   └── correlate_traffic.py     # Traffic-bundle correlation
│   └── maestro/
│       └── *.yaml        # UI automation flows
└── templates/
    └── ANALYSIS_TEMPLATE.md
```

## Tool Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| radare2 + r2hermes | Primary analysis | `brew install radare2 && r2pm -ci r2hermes` |
| hermes-dec | Decompiler (binary: `hbc-decompiler`) | `pip install git+https://github.com/P1sec/hermes-dec` |
| hbctool | Disasm/asm | `pip install hbctool` |
| jadx | DEX decompilation | `brew install jadx` |
| apktool | APK decoding | `brew install apktool` |
| Frida | Runtime hooks | `pip install frida-tools` |
| objection | APK/IPA patching | `pip install objection` |
| gitleaks | Secret scanning | `brew install gitleaks` |
| Maestro | UI automation | `curl -fsSL "https://get.maestro.mobile.dev" \| bash` |

## Key Features

### Static Analysis
- APK/IPA extraction and Hermes bundle detection
- Hermes version identification (`file` command most reliable)
- String and API endpoint extraction
- JADX decompilation for Java/Kotlin code
- iOS entitlements and privacy manifest analysis (iOS 17+)
- Source map detection and extraction
- Obfuscation detection (javascript-obfuscator, Metro, CFG flattening)
- Secret scanning with gitleaks/trufflehog

### Dynamic Analysis
- Frida scripts for SSL pinning bypass (40+ methods)
- Root/jailbreak detection bypass
- GMS/Firebase bypass for emulators
- React Native bridge tracing (native module calls, keychain, crypto)
- Traffic capture and bundle correlation
- Maestro UI automation

### Platform-Specific

| Feature | Android | iOS |
|---------|---------|-----|
| Bundle location | `assets/index.android.bundle` | `main.jsbundle` |
| Analysis script | `analyze_apk.py` | `analyze_ipa.py` |
| Tool checker | `check_tools.py` | `check_tools_ios.py` |
| Emulator | ARM64/x86_64 AVD | iOS Simulator (limited)* |
| Root/JB tools | Frida server | Palera1n, Dopamine |
| Patching | Objection, apktool | Objection + codesign |

*iOS Simulator only works with apps you build from source. App Store IPAs are device-only.

## Testing Results

The toolkit has been tested against **13 real-world React Native applications** (12 Android APKs, 1 iOS IPA) including:

| App | Hermes | Security Features |
|-----|--------|-------------------|
| Mattermost | v96 | Enterprise MDM, SSL pinning, jailbreak detection |
| Expensify | v96 | Firebase integration |
| BlueWallet | v96 | 4 anti-tampering indicators (crypto wallet) |
| Rocket.Chat | v96 | Root detection, enterprise features |
| Standard Notes | v96 | Integrity checking, encryption |

**Key findings:**
- 10/12 Android apps use Hermes bytecode v96 (React Native 0.73+)
- 9/13 apps implement root/jailbreak detection
- **75% false positive rate** on automated secret detection
- Only 1/4 flagged "secrets" were confirmed after deep analysis

## License

For authorized security testing, research, and educational purposes only.
