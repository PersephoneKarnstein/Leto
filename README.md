# Hermes Bytecode Analysis Skills

**Comprehensive penetration testing toolkit** for React Native applications compiled with Hermes. Available as two separate skills for Android and iOS.

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

# 2. Analyze APK
python scripts/analyze_apk.py target.apk --decompile

# 3. Verify Hermes version
file ./analysis/extracted/assets/index.android.bundle

# 4. Run with Frida
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js
```

### iOS
```bash
# 1. Check tools
python scripts/check_tools_ios.py

# 2. Analyze IPA
python scripts/analyze_ipa.py target.ipa --decompile

# 3. Verify Hermes version
file ./target_analysis/extracted/Payload/*.app/main.jsbundle

# 4. Run with Frida (jailbroken device)
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
│   ├── extract_bundle.py     # Extract from APK/device
│   ├── patch_and_repack.py   # Patch and rebuild APK
│   ├── frida/
│   │   ├── universal_ssl_bypass.js  # SSL pinning bypass (40+ methods)
│   │   ├── root_bypass.js           # Root/emulator detection bypass
│   │   ├── ios_ssl_bypass.js        # iOS SSL pinning bypass
│   │   ├── ios_jailbreak_bypass.js  # iOS jailbreak detection bypass
│   │   ├── gms_firebase_bypass.js   # GMS/Firebase bypass
│   │   ├── hermes_hooks.js          # React Native bridge hooks
│   │   └── detect_frameworks.js     # Framework detection
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
- Secret scanning with gitleaks/trufflehog

### Dynamic Analysis
- Frida scripts for SSL pinning bypass (40+ methods)
- Root/jailbreak detection bypass
- GMS/Firebase bypass for emulators
- React Native bridge hooking
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

## License

For authorized security testing, research, and educational purposes only.
