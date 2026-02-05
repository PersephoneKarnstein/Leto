# CLAUDE.md

This file provides guidance for Claude Code instances working with the Hermes Analysis Toolkit (Lêtô).

## Project Overview

This is a penetration testing toolkit for analyzing React Native applications compiled with Meta's Hermes JavaScript engine. It provides tools for static analysis, dynamic instrumentation, and security assessment of Android APKs and iOS IPAs containing Hermes bytecode.

**This is a security research tool - all analysis is for authorized testing only.**

## Quick Start Commands

```bash
# Check tool availability
python scripts/check_tools.py --install-help

# Analyze an Android APK
python scripts/analyze_apk.py target.apk --decompile

# Analyze an iOS IPA
python scripts/analyze_ipa.py target.ipa --decompile

# Verify Hermes version (most reliable method)
file ./analysis/extracted/assets/index.android.bundle

# Run Frida with SSL bypass
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js

# Secret scanning
gitleaks dir ./analysis/apktool/ -v
```

## Repository Structure

```
hermes-skill/
├── SKILL-android.md         # Main Android analysis documentation
├── SKILL-ios.md             # Main iOS analysis documentation
├── scripts/
│   ├── check_tools.py       # Tool availability checker (Android)
│   ├── check_tools_ios.py   # Tool availability checker (iOS)
│   ├── analyze_apk.py       # APK analysis workflow
│   ├── analyze_ipa.py       # IPA analysis workflow
│   ├── analyze_bundle.py    # Hermes bundle analysis
│   ├── extract_bundle.py    # Bundle extraction utilities
│   ├── patch_and_repack.py  # APK patching utilities
│   ├── sourcemap_recovery.py # Source map detection/extraction
│   ├── detect_obfuscation.py # Obfuscation detection
│   ├── frida/               # Frida instrumentation scripts
│   │   ├── universal_ssl_bypass.js
│   │   ├── root_bypass.js
│   │   ├── gms_firebase_bypass.js
│   │   ├── ios_ssl_bypass.js
│   │   ├── ios_jailbreak_bypass.js
│   │   ├── hermes_hooks.js
│   │   ├── rn_bridge_trace.js
│   │   └── detect_frameworks.js
│   ├── traffic/             # Traffic analysis tools
│   │   ├── mitmproxy_capture.py
│   │   └── correlate_traffic.py
│   └── maestro/             # UI automation flows
└── templates/
    └── ANALYSIS_TEMPLATE.md # Report template
```

## Critical Shell Command Rules

**IMPORTANT:** Always pipe `yes` into `rm -rf` commands or they will hang:
```bash
# CORRECT
yes | rm -rf directory/

# WRONG - will hang indefinitely
rm -rf directory/
```

## Key Workflow Rules

**ALWAYS follow this order:**
1. Run `python scripts/check_tools.py` first to verify tool availability
2. Use `python scripts/analyze_apk.py` (not manual extraction) for APK analysis
3. Use `python scripts/analyze_bundle.py` for Hermes bundle analysis
4. Verify Hermes version with `file` command (analyze_apk.py may report incorrect versions)

## Known Issues and Gotchas

### Hermes Version Detection
- `analyze_apk.py` may report incorrect bytecode versions
- **Always verify with**: `file index.android.bundle`
- The `file` command reliably reports "Hermes JavaScript bytecode, version 96"

### Large Bundle Handling (>20MB)
- r2hermes may hang or crash with "String offset/length out of bounds"
- Use `strings` command instead of `r2 -qc 'iz'` for extraction
- `analyze_bundle.py` has chunked extraction built-in

### Emulator Trade-offs
- `google_apis` images: Allow root/Frida but NO Google Play Services
- `google_apis_playstore` images: Have Play Services but locked, no root
- Apps depending on Firebase/GMS show black screens on pentest emulators
- **Solution**: Patch APK with Objection: `objection patchapk -s target.apk`

### Frida Compatibility
- Recommended: frida-tools 17.6.2 + frida-server 17.5.0
- No `--no-pause` flag in frida-tools 17.x (auto-resumes with `-f`)
- Some hooks fail due to app-specific class structures - this is expected

### Secret Scanning
- gitleaks/trufflehog produce false positives (emoji sequences, build tokens)
- **Always manually review findings**
- Use `gitleaks dir` syntax (not `gitleaks detect --source`)

### Tool Installation Notes
- `hermes_rs`: Upstream has missing source, `cargo install` fails
- Objection: May need sqlite3 fix on macOS Conda
- r2hermes: Use `r2pm -ci r2hermes` (run `r2pm update` first if issues)

## User Preferences

- Python path: `/opt/miniconda3/bin/python`
- Always confirm paths before executing tools
- Prompt before auto-installing missing tools
- Pipe `yes` into `rm -rf` commands on this system

## Platform-Specific Notes

| Aspect | Android | iOS |
|--------|---------|-----|
| Bundle file | `assets/index.android.bundle` | `main.jsbundle` |
| Analysis script | `analyze_apk.py` | `analyze_ipa.py` |
| Tool checker | `check_tools.py` | `check_tools_ios.py` |
| Dynamic analysis | Frida + frida-server | Frida + jailbreak or gadget |

## References

- [SKILL-android.md](SKILL-android.md) - Full Android analysis guide
- [SKILL-ios.md](SKILL-ios.md) - Full iOS analysis guide
- [scripts/frida/README.md](scripts/frida/README.md) - Frida script documentation
- [OWASP MASTG](https://mas.owasp.org/MASTG/) - Mobile security testing guide
