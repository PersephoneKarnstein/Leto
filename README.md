# Hermes Bytecode Analysis Skill

**Comprehensive penetration testing toolkit** for React Native/Hermes Android applications. Covers static analysis, dynamic instrumentation, traffic interception, and exploit development.

## Quick Start - Security Assessment

```bash
# 1. Check tool availability
python scripts/check_tools.py --install-help

# 2. Extract and decompile APK
apktool d app.apk -o extracted/
jadx app.apk -d jadx_output/

# 3. CRITICAL: Check for exported components & secrets
grep 'exported="true"' extracted/AndroidManifest.xml
cat jadx_output/sources/*/BuildConfig.java

# 4. Analyze Hermes bundle
python scripts/extract_bundle.py app.apk --output ./hermes/
r2 -qc 'pd:hi' ./hermes/index.android.bundle    # Bundle info
r2 -qc 'iz~http' ./hermes/index.android.bundle  # Find API endpoints

# 5. Setup traffic interception
./scripts/setup_burp_cert.sh /path/to/burp_cert.der
adb shell settings put global http_proxy YOUR_IP:8080
```

## Assessment Methodology

| Phase | Focus | Tools |
|-------|-------|-------|
| **1. APK Analysis** | Manifest, exports, secrets | apktool, jadx, grep |
| **2. Hermes Analysis** | API endpoints, logic | r2hermes, hbc-decompiler |
| **3. Traffic Capture** | Auth flows, API calls | Burp Suite, mitmproxy |
| **4. Runtime Hooks** | Token capture, bypass | Frida |
| **5. UI Automation** | Trigger flows | Maestro |
| **6. PoC Development** | Prove exploitability | ADB, custom apps |

## Features

- **Static Analysis**: Decompile, disassemble, extract strings/modules
- **Dynamic Analysis**: Frida hooks for React Native/Hermes runtime
- **Patching**: Modify bytecode and repackage APKs
- **Multi-tool**: Integrates r2hermes, hbctool, hermes-dec, hermes_rs

## Directory Structure

```
hermes-skill/
├── SKILL.md              # Main skill documentation
├── README.md             # This file
└── scripts/
    ├── check_tools.py    # Verify tool installation
    ├── analyze_bundle.py # Quick bundle analysis
    ├── extract_bundle.py # Extract from APK/device
    ├── patch_and_repack.py # Patch and rebuild APK
    └── frida/
        ├── hermes_hooks.js   # React Native/Hermes hooks
        └── ssl_bypass.js     # Certificate pinning bypass
```

## Tool Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| radare2 + r2hermes | Primary analysis | `brew install radare2 && r2pm -ci r2hermes` |
| Python 3.8+ | Scripts | System or custom path |
| hbctool | Disasm/asm | `pip install hbctool` |
| hermes-dec | Pure Python decompiler | `pip install git+https://github.com/P1sec/hermes-dec` |
| hermes_rs | Rust tools | `cargo install --git https://github.com/Pilfer/hermes_rs` |
| Frida | Runtime hooks | `pip install frida-tools` |
| adb | Device interaction | Android SDK |
| apktool | APK manipulation | `brew install apktool` |

## Workflows

### Static Analysis
```bash
# Decompile all functions
r2 -qc 'pd:ha' bundle.hbc > decompiled.js

# Extract strings
hermes_rs strings bundle.hbc

# Find API endpoints
grep -E 'https?://' decompiled.js
```

### Runtime Analysis
```bash
# Start Frida server on device
adb push frida-server /data/local/tmp/
adb shell chmod +x /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# Hook app
frida -U -f com.example.app -l scripts/frida/hermes_hooks.js
```

### Patching
```bash
# Patch bundle and repackage
python scripts/patch_and_repack.py original.apk patched.bundle -o patched.apk

# Install
adb install -r patched.apk
```

## Path Configuration

Before running tools, confirm paths with user. Default assumptions:
- `r2` / `radare2` in PATH
- `python3` in PATH (or custom like `/opt/miniconda3/bin/python`)
- `cargo` in PATH for Rust tools
- `adb` in PATH (Android SDK)

## License

For authorized security testing, research, and educational purposes only.
