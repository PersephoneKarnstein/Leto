# Hermes Bytecode Analysis Skills

**Comprehensive penetration testing toolkit** for React Native applications compiled with Hermes. Available as two separate skills for Android and iOS.

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
# 1. Extract IPA
unzip -o app.ipa -d extracted_ipa/

# 2. Verify Hermes bundle
file extracted_ipa/Payload/*.app/main.jsbundle

# 3. Analyze bundle
r2 -qc 'pd:ha' main.jsbundle > decompiled.js

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
│   ├── check_tools.py    # Verify tool installation
│   ├── analyze_apk.py    # Automated APK analysis
│   ├── analyze_bundle.py # Hermes bundle analysis
│   ├── extract_bundle.py # Extract from APK/device
│   ├── patch_and_repack.py # Patch and rebuild APK
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
| Emulator | ARM64/x86_64 AVD | N/A (device only) |
| Root/JB tools | Frida server | Palera1n, Dopamine |
| Patching | Objection, apktool | Objection + codesign |

## License

For authorized security testing, research, and educational purposes only.
