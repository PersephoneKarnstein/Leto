---
name: hermes-bytecode
description: Analyze Hermes bytecode in React Native Android apps. Disassemble, decompile, patch, and instrument .hbc files and index.android.bundle. Keywords - "hermes", "react native", "hbc", "bytecode", "decompile", "frida", "r2hermes", "hbctool"
---

# Hermes Bytecode Analysis

Comprehensive toolkit for reverse engineering React Native Android applications compiled with Meta's Hermes JavaScript engine.

> **Note**: This skill focuses on Android. iOS Hermes analysis requires different tooling (IPA extraction, jailbroken device, different binary formats).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [When to Use](#when-to-use)
3. [Tool Ecosystem](#tool-ecosystem)
4. [Path Confirmation & Tool Check](#critical-path-confirmation)
5. [Installation](#installation-prompt-user-first)
6. [Penetration Testing Methodology](#penetration-testing-methodology)
7. [Security Audit Checklist](#security-audit-checklist)
8. [Static Analysis](#static-analysis-workflows)
   - [JADX Integration](#jadx-integration)
   - [Large Bundle Handling](#important-large-bundle-handling)
   - [APK Extraction](#apk-extraction-workflow)
   - [Automated APK Analysis](#automated-apk-analysis)
   - [Source Map Analysis](#source-map-analysis)
9. [Dynamic Analysis](#dynamic-analysis--runtime-instrumentation)
   - [Maestro UI Automation](#maestro-ui-automation)
   - [Burp Suite Traffic Interception](#burp-suite-traffic-interception)
   - [Frida Setup & Scripts](#frida-setup-for-hermes-apps)
10. [Emulator Setup](#emulator-setup-for-penetration-testing)
11. [Patching & Modification](#patching--modification-workflow)
12. [Troubleshooting](#troubleshooting)
13. [Security Report Writing](#security-report-writing)
14. [Command Reference](#r2hermes-command-reference)
15. [Resources](#resources)

---

## Quick Start

**Most common workflow for assessing a React Native APK:**

```bash
# 1. Check tools are installed
python scripts/check_tools.py

# 2. Run automated analysis
python scripts/analyze_apk.py target.apk --decompile

# 3. Check AndroidManifest for critical issues
cat target_analysis/apktool/AndroidManifest.xml | grep -E 'exported="true"|allowBackup'

# 4. Decompile Java code
jadx target.apk -d jadx_output/

# 5. Check for hardcoded secrets
cat jadx_output/sources/*/BuildConfig.java
grep -rE "(api[_-]?key|secret|token)" jadx_output/sources/ -i

# 6. Analyze Hermes bundle
r2 -qc 'pd:hi' target_analysis/extracted/assets/index.android.bundle

# 7. Start emulator and install app
emulator -avd pentest_api30 -writable-system &
adb install target.apk

# 8. Run with Frida bypasses
frida -U -f com.target.app \
  -l scripts/frida/universal_ssl_bypass.js \
  -l scripts/frida/root_bypass.js
```

**Key files to always check:**
- `AndroidManifest.xml` - exported components, permissions, backup settings
- `BuildConfig.java` - API keys, endpoints, debug flags
- `res/xml/network_security_config.xml` - cleartext traffic, pinning
- `res/xml/provider_paths.xml` - FileProvider exposure
- `assets/index.android.bundle` - Hermes bytecode with strings/endpoints

---

## When to Use

- Analyzing React Native Android/iOS applications
- Reverse engineering Hermes bytecode (.hbc, index.android.bundle)
- Decompiling JavaScript from compiled bundles
- Patching and modifying React Native app behavior
- Runtime instrumentation of Hermes apps with Frida
- Extracting strings, modules, and API endpoints from bundles

---

## Tool Ecosystem

### Hermes Analysis Tools
| Tool | Language | Strength | Versions | Install |
|------|----------|----------|----------|---------|
| **r2hermes** | C | radare2 integration, decompilation, patching | v51-96 | `r2pm -ci r2hermes` |
| **hbctool** | Python | Simple disasm/asm workflow | v59,62,74,76 | `pip install hbctool` |
| **hermes-dec** | Python | Pure Python, no deps, decompiler | v59-84+ | `pip install git+https://github.com/P1sec/hermes-dec` |
| **hermes_rs** | Rust | Type-safe, module extraction, r2 scripts | v76,89-96 | `cargo install hermes_rs` |
| **hasmer** | C#/.NET | Any version disassembly | All | See hasmer docs (archived) |
| **heresy** | Rust/TS | Frida runtime instrumentation | Runtime | npm install + build |
| **Official Hermes** | C++ | hbcdump, hermesc compiler | All | Build from source |

### APK Patching & Instrumentation Tools
| Tool | Purpose | Install |
|------|---------|---------|
| **Objection** | Frida gadget injection, APK patching, runtime exploration | `pip install objection` |
| **apktool** | APK decompilation/recompilation, smali editing | `brew install apktool` |
| **apksigner** | APK signing | Android SDK build-tools |
| **zipalign** | APK alignment (required before signing) | Android SDK build-tools |
| **JADX** | Java decompilation, resource extraction | `brew install jadx` |
| **r2frida** | Frida integration for radare2, runtime analysis | `r2pm -ci r2frida` |
| **r2ai** | AI-powered analysis assistant for radare2 | `r2pm -ci r2ai` |

### Version Coverage Matrix

```
Hermes Version:  51 ... 59 62 ... 74 76 ... 84 ... 89 90 ... 93 94 95 96
r2hermes:        [=================================================]
hbctool:                 [==]     [====]
hermes-dec:              [=======================]
hermes_rs:                           [==]     [==================]
hasmer:          [=================================================]
```

**Recommendation**: Use r2hermes as primary tool (broadest coverage). Fall back to hermes_rs for newer versions, hermes-dec for pure Python workflow.

---

## CRITICAL: Path Confirmation

**Before executing any tool, confirm the path with the user.**

### Automated Tool Check

Use the tool checker script to verify all tools:

```bash
# Check all tools with status
python scripts/check_tools.py

# Output as JSON
python scripts/check_tools.py --json

# Show installation commands for missing tools
python scripts/check_tools.py --install-help
```

The tool checker verifies:
- radare2 & plugins (r2hermes, r2frida, r2ai)
- Python tools (hbctool, hermes-dec, frida-tools, objection)
- Android SDK tools (adb, apktool, jadx, emulator, avdmanager)
- Rust tools (hermes_rs)
- UI automation (Maestro)
- Traffic interception (mitmproxy, Burp Suite)

### Default Paths (confirm before use)

```bash
# Check tool availability - RUN THESE FIRST
which r2          # radare2
which python3     # Python (user may have custom path)
which cargo       # Rust toolchain
which frida       # Frida CLI
which adb         # Android Debug Bridge

# r2hermes check
r2 -qc 'pd:h?' /dev/null 2>&1 | grep -q Usage && echo "r2hermes OK" || echo "r2hermes NOT installed"

# hbctool check
python3 -c "import hbctool" 2>/dev/null && echo "hbctool OK" || echo "hbctool NOT installed"

# hermes-dec check
python3 -c "import hbc_decompiler" 2>/dev/null && echo "hermes-dec OK" || echo "hermes-dec NOT installed"
```

### User-Specific Path Notes

- Python may be at custom location (e.g., `/opt/miniconda3/bin/python`)
- Always ask user to confirm before running installation commands
- Store confirmed paths for session reuse

---

## Installation (Prompt User First)

Before installing any tool, ask the user: "I need to install [tool]. Should I run: `[command]`?"

### Cross-Platform Installation Guide

#### radare2 & r2hermes (Primary Tool)

| Platform | Command |
|----------|---------|
| **macOS** | `brew install radare2` |
| **Linux (Debian/Ubuntu)** | `sudo apt install radare2` or build from source |
| **Linux (Arch)** | `sudo pacman -S radare2` |
| **Windows** | Download from https://github.com/radareorg/radare2/releases or `choco install radare2` |

```bash
# Then install r2hermes plugin (all platforms)
r2pm -ci r2hermes

# Verify
r2 -qc 'pd:hi' /dev/null
```

#### Python Tools (hbctool, hermes-dec, Frida, Objection)

```bash
# All platforms - confirm Python path first!
pip install hbctool
pip install git+https://github.com/P1sec/hermes-dec
pip install frida-tools
pip install objection

# Or with specific Python (user-specific path)
/path/to/python -m pip install hbctool frida-tools objection
```

#### Rust Tools (hermes_rs)

```bash
# Install Rust first (all platforms)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh  # macOS/Linux
# Windows: Download from https://rustup.rs

# Then install hermes_rs
cargo install --git https://github.com/Pilfer/hermes_rs
```

#### Android SDK Tools (adb, apktool, jadx)

| Tool | macOS | Linux (Debian/Ubuntu) | Windows |
|------|-------|----------------------|---------|
| **adb** | `brew install android-platform-tools` | `sudo apt install adb` | Android Studio or `choco install adb` |
| **apktool** | `brew install apktool` | `sudo apt install apktool` | Download from https://apktool.org |
| **jadx** | `brew install jadx` | Download from GitHub releases | Download from GitHub releases |
| **Android Studio** | Download from developer.android.com | Download from developer.android.com | Download from developer.android.com |

#### UI Automation (Maestro)

```bash
# All platforms (requires Java 17+)
curl -fsSL "https://get.maestro.mobile.dev" | bash

# Windows: Use WSL or download from https://maestro.mobile.dev
```

#### Traffic Interception

| Tool | macOS | Linux | Windows |
|------|-------|-------|---------|
| **mitmproxy** | `pip install mitmproxy` | `pip install mitmproxy` | `pip install mitmproxy` |
| **Burp Suite** | Download from portswigger.net | Download from portswigger.net | Download from portswigger.net |

#### heresy (Runtime Instrumentation)

```bash
# All platforms (requires Node.js)
git clone https://github.com/Pilfer/heresy
cd heresy
npm install && npm run build
```

#### Official Hermes Tools (Build from Source)

```bash
# Requires: cmake, ninja, clang/gcc
git clone https://github.com/facebook/hermes
cd hermes
cmake -S . -B build -G Ninja
cmake --build ./build
# Tools in ./build/bin/: hermesc, hbcdump, hdb, etc.
```

---

## PENETRATION TESTING METHODOLOGY

This skill is designed for **comprehensive security assessment** of React Native/Hermes Android applications. Follow this methodology systematically.

### Phase 1: Static Analysis - APK Structure

#### 1.1 Extract and Decompile APK

```bash
# Extract with apktool (preserves resources)
apktool d app.apk -o extracted/

# Decompile Java with JADX
jadx app.apk -d jadx_output/

# Extract Hermes bundle
unzip app.apk assets/index.android.bundle -d ./
```

#### 1.2 AndroidManifest.xml Analysis (CRITICAL)

**This is often where critical vulnerabilities are found.**

```bash
# View manifest
cat extracted/AndroidManifest.xml

# Find exported components (CRITICAL - check each one)
grep -E 'android:exported="true"' extracted/AndroidManifest.xml

# Find all receivers
grep -A5 '<receiver' extracted/AndroidManifest.xml

# Find all activities with intent-filters (deep links)
grep -B2 -A10 '<intent-filter>' extracted/AndroidManifest.xml

# Find permissions
grep 'uses-permission' extracted/AndroidManifest.xml

# Check backup settings
grep 'allowBackup' extracted/AndroidManifest.xml

# Find FileProvider paths
cat extracted/res/xml/provider_paths.xml 2>/dev/null || \
cat extracted/res/xml/file_paths.xml 2>/dev/null
```

**What to look for:**
| Finding | Severity | Issue |
|---------|----------|-------|
| `exported="true"` on receivers | CRITICAL | Any app can send intents |
| `exported="true"` on providers | HIGH | Data exposure |
| `allowBackup="true"` | MEDIUM | Data extraction via backup |
| FileProvider with `path="."` | HIGH | Entire directory exposed |
| Deep links without validation | MEDIUM | Intent injection |

#### 1.3 Hardcoded Secrets Scan (CRITICAL)

```bash
# BuildConfig.java - ALWAYS CHECK THIS
cat jadx_output/sources/*/BuildConfig.java

# Search for API keys, secrets, tokens
grep -rE "(api[_-]?key|secret|token|password|credential|auth)" jadx_output/sources/ --include="*.java" -i

# Search for URLs and endpoints
grep -rE "https?://[a-zA-Z0-9.-]+" jadx_output/sources/ --include="*.java"

# Search strings.xml
grep -E "(key|secret|token|api|password)" extracted/res/values/strings.xml

# Common secret patterns
grep -rE "(sk_live|pk_live|AKIA|ghp_|glpat-|xox[baprs]-)" jadx_output/sources/
```

**Common secrets to find:**
| Secret Type | Pattern | Risk |
|-------------|---------|------|
| Stripe | `pk_live_`, `sk_live_` | Payment fraud |
| AWS | `AKIA[A-Z0-9]{16}` | Cloud compromise |
| Firebase | `AIza[A-Za-z0-9_-]{35}` | Backend access |
| OAuth Client Secret | `client_secret` | Token theft |
| API Keys | `[Aa]pi[_-]?[Kk]ey` | Varies |
| CodePush | Deployment keys | Code injection |

#### 1.4 Network Security Analysis

```bash
# Check for certificate pinning
grep -r "CertificatePinner\|certificatePinner" jadx_output/sources/

# Check for SSL bypass code
grep -r "TrustManager\|X509TrustManager\|ALLOW_ALL\|trustAllCerts" jadx_output/sources/

# Check OkHttp configuration
find jadx_output/sources -name "*OkHttp*" -o -name "*Client*" | xargs grep -l "build()"

# Check network_security_config.xml
cat extracted/res/xml/network_security_config.xml 2>/dev/null
```

**Red flags:**
- No `CertificatePinner` = MitM vulnerable
- `checkServerTrusted` that's empty = SSL bypass
- `cleartextTrafficPermitted="true"` = HTTP allowed

### Phase 2: Static Analysis - Hermes Bytecode

#### 2.1 Bundle Information

```bash
# Get bundle stats
r2 -qc 'pd:hi' index.android.bundle
```

**Example output:**
```
Hermes Bytecode File
  Version: 96
  SHA1: a3f2b8c1d4e5f6...
  File size: 15234567
  Function count: 8432
  String count: 12847
  Hash status: valid
```

#### 2.2 API Endpoint Enumeration

```bash
# Extract all URLs (use r2 for large bundles)
r2 -qc 'iz~http' index.android.bundle | head -100

# Search for API paths
r2 -qc 'iz' index.android.bundle | grep -iE "frontend/|/api/|/v[0-9]/"

# Search for sensitive endpoints
r2 -qc 'iz' index.android.bundle | grep -iE "login|auth|token|password|payment|admin"
```

**Example output:**
```
0x00234567 https://api.example.com/v1/auth/login
0x00234890 https://api.example.com/v1/user/profile
0x00235012 https://api.example.com/v1/payment/process
0x00235234 wss://realtime.example.com/socket
```

#### 2.3 Function Analysis

```bash
# List all functions (pipe to file for large bundles)
r2 -qc 'pd:hf' index.android.bundle > functions.txt

# Search for interesting function names
grep -iE "auth|login|password|encrypt|decrypt|token|payment|admin" functions.txt

# Decompile specific functions
r2 -qc 'pd:hc FUNCTION_ID' index.android.bundle
```

**Example pd:hf output:**
```
#0    global
#1    requireModule
#42   authenticateUser
#108  encryptPayload
#156  validateToken
#892  processPayment
```

**Example pd:hc output (decompiled function):**
```javascript
function authenticateUser(username, password) {
  var credentials = {
    "email": username,
    "password": password
  };
  return fetch("https://api.example.com/v1/auth/login", {
    "method": "POST",
    "body": JSON.stringify(credentials)
  });
}
```

### Phase 3: Dynamic Analysis

#### 3.1 Traffic Interception (Burp Suite)

```bash
# Setup certificate (see Burp Setup section)
./scripts/setup_burp_cert.sh /path/to/burp_cert.der

# Set proxy
adb shell settings put global http_proxy YOUR_IP:8080

# Launch app and capture traffic
# Look for:
# - Authentication flows
# - API request/response patterns
# - Token handling
# - Sensitive data in transit
```

#### 3.2 Runtime Instrumentation (Frida)

```bash
# Hook with SSL bypass
frida -U -f com.target.app -l scripts/frida/ssl_bypass.js -l scripts/frida/hermes_hooks.js
# Monitor:
# - API calls
# - Authentication tokens
# - Sensitive data handling
```

#### 3.3 UI Automation (Maestro)

```yaml
# Trigger specific app flows while monitoring
appId: com.target.app
---
- launchApp
- tapOn: "Login"
- inputText: "test@test.com"
# ... capture traffic/logs during these actions
```

### Phase 4: Vulnerability Verification & PoC

#### 4.1 Exported Component Testing

```bash
# Test exported BroadcastReceiver
adb shell am broadcast -a ACTION_NAME \
  -n com.target.app/.ReceiverClassName \
  --es param1 "value1"

# Test exported Activity
adb shell am start -n com.target.app/.ActivityName \
  -d "deeplink://path?param=value"

# Test exported ContentProvider
adb shell content query --uri content://com.target.app.provider/path
```

**Example successful broadcast output:**
```
Broadcasting: Intent { act=ACTION_NAME cmp=com.target.app/.ReceiverClassName }
Broadcast completed: result=0
```

**Example ContentProvider query output:**
```
Row: 0 _id=1, username=admin, email=admin@example.com
Row: 1 _id=2, username=user, email=user@example.com
```

If you see data returned, the ContentProvider is exposed.

#### 4.2 MitM Attack Verification

```bash
# With Burp/mitmproxy capturing, verify you can:
# 1. See all HTTPS traffic (no cert pinning)
# 2. Modify requests
# 3. Inject responses
```

### Phase 5: Reporting

#### Severity Classification (CVSS 3.1)

| Severity | CVSS Score | Examples |
|----------|------------|----------|
| CRITICAL | 9.0-10.0 | RCE, auth bypass, medical data manipulation |
| HIGH | 7.0-8.9 | Credential theft, payment fraud, data breach |
| MEDIUM | 4.0-6.9 | Info disclosure, session hijacking |
| LOW | 0.1-3.9 | Minor info leak, hardcoded non-sensitive data |

#### Report Structure

```markdown
# Vulnerability Report

## Executive Summary
## Scope and Methodology
## Findings
### Finding 1: [Title]
- **Severity**: CRITICAL/HIGH/MEDIUM/LOW
- **CVSS**: X.X
- **Location**: File/Component
- **Description**: What's vulnerable
- **Impact**: What an attacker can do
- **Proof of Concept**: Steps to reproduce
- **Remediation**: How to fix
## Recommendations
## Appendix
```

---

## SECURITY AUDIT CHECKLIST

Use this checklist for every assessment:

### AndroidManifest.xml
- [ ] Check all `exported="true"` components
- [ ] Review BroadcastReceivers for permission requirements
- [ ] Check deep link handlers for input validation
- [ ] Review FileProvider path configurations
- [ ] Check `allowBackup` and `debuggable` flags
- [ ] Review requested permissions

### Hardcoded Secrets
- [ ] Check BuildConfig.java
- [ ] Check strings.xml
- [ ] Search for API keys, tokens, passwords
- [ ] Check for OAuth client secrets
- [ ] Check for payment processor credentials
- [ ] Check for analytics/crash reporting keys

### Network Security
- [ ] Verify certificate pinning is implemented
- [ ] Check for SSL bypass code (TrustManager)
- [ ] Review network_security_config.xml
- [ ] Test with MitM proxy (Burp)

### Hermes Bundle
- [ ] Extract all API endpoints
- [ ] Search for hardcoded credentials
- [ ] Identify authentication logic
- [ ] Map sensitive data flows

### Runtime
- [ ] Test exported components with ADB
- [ ] Verify traffic interception works
- [ ] Test deep link injection
- [ ] Check for root/jailbreak detection bypass

---

## JADX Integration

JADX is essential for analyzing native Java code alongside Hermes bytecode.

### Installation

```bash
# macOS
brew install jadx

# Or download from GitHub
# https://github.com/skylot/jadx/releases
```

### Key Files to Analyze

```bash
# ALWAYS check these files:
jadx_output/sources/com/PACKAGE/BuildConfig.java      # Secrets
jadx_output/sources/com/PACKAGE/MainActivity.java     # Entry point
jadx_output/sources/com/PACKAGE/*Receiver.java        # Broadcast receivers
jadx_output/sources/com/PACKAGE/*Provider.java        # Content providers
jadx_output/sources/com/PACKAGE/util/*Client*.java    # HTTP clients
jadx_output/sources/com/PACKAGE/util/*Factory*.java   # Client factories
```

### Common Vulnerability Patterns in Java

```java
// VULNERABLE: Exported receiver without permission
<receiver android:name=".MyReceiver" android:exported="true">

// VULNERABLE: Empty SSL verification
public void checkServerTrusted(X509Certificate[] chain, String authType) {
    // Empty = accepts any certificate
}

// VULNERABLE: Hardcoded secrets
public static final String API_KEY = "sk_live_xxxxx";

// VULNERABLE: Permissive FileProvider
<external-path name="external" path="." />
```

---

## IMPORTANT: Large Bundle Handling

Hermes bundles can be very large (10-50MB+). **Avoid operations that process the entire bundle at once**, as they will hang or time out.

### Safe Operations (any bundle size)
```bash
# File info - fast
r2 -qc 'pd:hi' bundle.hbc

# List functions (metadata only) - fast
r2 -qc 'pd:hf' bundle.hbc | head -100

# Decompile SINGLE function - fast
r2 -qc 'pd:hc 42' bundle.hbc
```

### Dangerous Operations (will hang on large bundles)
```bash
# DO NOT DO THESE on large bundles:
r2 -qc 'pd:ha' bundle.hbc              # Decompile ALL - will hang
strings bundle.hbc | grep ...          # Full strings - will hang
hermes_rs strings bundle.hbc           # Full extraction - will hang
```

### Safe String/Pattern Search (large bundles)
```bash
# Use dd to extract chunks, or search with byte limits
head -c 1000000 bundle.hbc | strings | grep -i "api"    # First 1MB only
tail -c 1000000 bundle.hbc | strings | grep -i "api"    # Last 1MB only

# Or use r2's limited search
r2 -qc '/s http' bundle.hbc | head -20                  # Search for string pattern

# Decompile specific functions only
r2 -qc 'pd:hc 100; pd:hc 200; pd:hc 300' bundle.hbc    # Specific IDs
```

---

## Static Analysis Workflows

### Workflow 1: Quick Bundle Analysis (r2hermes)

```bash
# Open bundle
r2 index.android.bundle

# Get file info (version, function count, hash status)
[0x00000000]> pd:hi

# List all functions
[0x00000000]> pd:hf

# Search for interesting functions
[0x00000000]> pd:hf~api
[0x00000000]> pd:hf~login
[0x00000000]> pd:hf~fetch
[0x00000000]> pd:hf~encrypt
[0x00000000]> pd:hf~password

# Decompile specific function
[0x00000000]> pd:hc 42

# Decompile with offsets (for patching)
[0x00000000]> pd:ho 42

# Decompile all to file
r2 -qc 'pd:ha' index.android.bundle > decompiled.js
```

### Workflow 2: Full Decompilation (hermes-dec)

```bash
# Parse file structure
hbc-file-parser index.android.bundle

# Disassemble to assembly
hbc-disassembler index.android.bundle output.hasm

# Decompile to JavaScript
hbc-decompiler index.android.bundle output.js
```

### Workflow 3: Module & String Extraction (hermes_rs)

```bash
# Extract all strings
hermes_rs strings index.android.bundle

# Find Metro bundler modules
hermes_rs modules index.android.bundle

# Dump arrays (often contain config)
hermes_rs arrays index.android.bundle

# Extract objects (API configs, etc.)
hermes_rs objects index.android.bundle

# Generate r2 analysis script
hermes_rs r2_script index.android.bundle > analyze.r2
r2 -i analyze.r2 index.android.bundle
```

### Workflow 4: Disassemble/Reassemble (hbctool)

```bash
# Disassemble to editable format
hbctool disasm index.android.bundle ./output_dir

# Directory structure:
# output_dir/
#   metadata.json    # File metadata
#   instruction.hasm # Assembly instructions

# Reassemble after modifications
hbctool asm ./output_dir modified.bundle
```

---

## APK Extraction Workflow

### Extract Hermes Bundle from APK

```bash
# Method 1: Using unzip
unzip -o app.apk -d extracted_apk/
ls extracted_apk/assets/
# Look for: index.android.bundle or *.hbc files

# Method 2: Using apktool (preserves structure)
apktool d app.apk -o extracted_apk/
cat extracted_apk/assets/index.android.bundle

# Method 3: From installed app via ADB
adb shell pm path com.example.app
# Returns: /data/app/~~xxx/com.example.app-xxx/base.apk
adb pull /data/app/~~xxx/com.example.app-xxx/base.apk
```

### Identify if App Uses Hermes

```bash
# Check for Hermes bytecode magic bytes
xxd -l 8 index.android.bundle
# Hermes: c61f bc03 ... (varies by version)

# Check for libhermes.so
unzip -l app.apk | grep hermes
# Should show: lib/arm64-v8a/libhermes.so

# Using file command
file index.android.bundle
# "Hermes JavaScript bytecode, version XX"
```

### Verify Hermes Version

```bash
# r2hermes
r2 -qc 'pd:hi' index.android.bundle | grep -i version

# hermes_rs
hermes_rs bytecode index.android.bundle 2>&1 | head -5

# Manual check (byte at offset 4-7)
xxd -s 4 -l 4 index.android.bundle
```

---

## Automated APK Analysis

Use the `scripts/analyze_apk.py` script for automated analysis workflow:

### Quick Analysis

```bash
# Full analysis (extract, identify, strings, report)
python scripts/analyze_apk.py target.apk

# Extract only
python scripts/analyze_apk.py target.apk --extract-only

# Full analysis with decompilation
python scripts/analyze_apk.py target.apk --decompile

# Custom output directory
python scripts/analyze_apk.py target.apk --output-dir ./analysis_output
```

### What It Does

1. **Extracts APK** - Unpacks APK contents and uses apktool for manifest
2. **Finds Hermes Bundle** - Locates index.android.bundle or similar
3. **Detects Version** - Identifies Hermes bytecode version and estimated RN version
4. **Extracts Strings** - Finds API endpoints, keys, JWTs, Firebase URLs
5. **Generates Report** - Creates JSON report with all findings

### Output Structure

```
target_analysis/
├── extracted/           # Raw APK contents
│   └── assets/
│       └── index.android.bundle
├── apktool/            # Decoded with apktool (readable manifest)
├── decompiled/         # If --decompile used
│   ├── hbctool_output/
│   ├── hermes_dec_output.js
│   └── r2_disasm_sample.txt
└── report.json         # Analysis report
```

### Report Contents

```json
{
  "apk_name": "target.apk",
  "hermes_detected": true,
  "hermes_version": {
    "bytecode_version": 94,
    "estimated_rn_version": "React Native 0.71+"
  },
  "bundle_size": 15234567,
  "api_endpoints": ["https://api.example.com/v1/..."],
  "interesting_strings": [
    {"type": "api_key", "value": "sk_live_..."},
    {"type": "firebase", "value": "myapp.firebaseio.com"}
  ],
  "native_libs": [...],
  "permissions": ["INTERNET", "CAMERA", ...]
}
```

### Hermes Version to React Native Mapping

| Bytecode Version | React Native Version |
|------------------|---------------------|
| 89 | 0.64+ |
| 90 | 0.65+ |
| 93 | 0.70+ |
| 94 | 0.71+ |
| 95 | 0.72+ |
| 96 | 0.73+ |
| 97 | 0.74+ |
| 98 | 0.75+ |

---

## Source Map Analysis

React Native apps may include source maps (`.map` files) that reveal the original JavaScript source code. This is a critical finding for security assessments.

### Finding Source Maps

```bash
# Check APK for source maps
unzip -l target.apk | grep -E "\.map$|sourcemap"

# Common locations
ls -la extracted/assets/*.map 2>/dev/null
ls -la extracted/assets/index.android.bundle.map 2>/dev/null

# Search recursively
find extracted/ -name "*.map" -o -name "*sourcemap*"
```

### Analyzing Source Maps

Source maps are JSON files that map compiled code back to original source:

```bash
# Check if it's a valid source map
head -c 100 index.android.bundle.map
# Should start with: {"version":3,"sources":[...

# Extract original source file list
cat index.android.bundle.map | jq '.sources' | head -50

# Extract source content (if embedded)
cat index.android.bundle.map | jq '.sourcesContent[0]' | head -100
```

### Using source-map-explorer

```bash
# Install
npm install -g source-map-explorer

# Analyze bundle with source map
source-map-explorer index.android.bundle index.android.bundle.map

# This shows which modules take up space and can reveal:
# - Third-party libraries used
# - Internal module structure
# - Original file paths (may reveal directory structure)
```

### Security Implications

| Finding | Severity | Issue |
|---------|----------|-------|
| Source map in production APK | HIGH | Full source code exposed |
| Source map on accessible server | HIGH | Attackers can download and analyze |
| sourcesContent embedded | CRITICAL | Actual source code in map file |
| Relative paths in sources | MEDIUM | Reveals project structure |

### Example Output

```json
{
  "version": 3,
  "sources": [
    "node_modules/react/index.js",
    "src/api/AuthService.js",      // <-- Internal code paths exposed
    "src/utils/CryptoHelper.js",   // <-- Security-relevant modules
    "src/config/secrets.js"        // <-- Potentially sensitive
  ],
  "sourcesContent": [...]          // <-- If present, full source available
}
```

### Remediation

Ensure source maps are excluded from production builds:

```javascript
// metro.config.js
module.exports = {
  transformer: {
    // Disable source maps in production
    minifierConfig: {
      sourceMap: false,  // For production builds
    },
  },
};
```

---

## Patching & Modification Workflow

### Workflow 1: Patch with r2hermes

```bash
# Open in write mode
r2 -w index.android.bundle

# Find target function
[0x00000000]> pd:hf~checkLicense
# Found: function #123 at 0x4567

# Decompile with offsets
[0x00000000]> pd:ho 123
# Shows bytecode offsets for each statement

# Modify bytecode at specific offset
[0x00004567]> wx 00  # NOP or modify instruction

# CRITICAL: Fix footer hash after patching
[0x00000000]> .(fix-hbc)

# Verify hash
[0x00000000]> pd:hi
# Should show "hash: valid"
```

### Workflow 2: Patch with hbctool

```bash
# Disassemble
hbctool disasm index.android.bundle ./patch_workspace

# Edit instruction.hasm
# Find and modify target instructions

# Reassemble
hbctool asm ./patch_workspace patched.bundle

# Replace in APK
cp patched.bundle extracted_apk/assets/index.android.bundle
```

### Workflow 3: Repackage APK After Patching

```bash
# Rebuild APK with apktool
apktool b extracted_apk/ -o patched_unsigned.apk

# Sign APK (required for installation)
# Generate keystore if needed:
keytool -genkey -v -keystore debug.keystore -alias debug -keyalg RSA -keysize 2048 -validity 10000

# Sign
apksigner sign --ks debug.keystore --ks-key-alias debug patched_unsigned.apk
mv patched_unsigned.apk patched.apk

# Or use jarsigner
jarsigner -verbose -keystore debug.keystore patched_unsigned.apk debug

# Zipalign (optional but recommended)
zipalign -v 4 patched_unsigned.apk patched.apk

# Install
adb install -r patched.apk
```

---

## APK Patching with Objection

Objection simplifies APK patching by automating Frida gadget injection, signing, and alignment. Essential for:
- Injecting Frida gadget for apps without Frida server access
- Bypassing SSL pinning
- Runtime exploration of native apps

### Quick Patch Workflow

```bash
# Patch APK with Frida gadget (auto-signs with debug key)
objection patchapk -s target.apk

# Output: target.objection.apk

# Install patched APK
adb install target.objection.apk

# Connect with Objection
objection -g com.target.app explore
```

### Objection Exploration Commands

```bash
# Inside objection REPL:

# SSL pinning bypass
android sslpinning disable

# List activities
android hooking list activities

# List services
android hooking list services

# Dump keystore
android keystore list

# Search classes
android hooking search classes firebase
android hooking search classes crypto

# Hook method and print arguments
android hooking watch class_method com.target.ClassName.methodName --dump-args

# Memory dump
memory dump all /tmp/mem.bin

# File system access
env
ls
file download /data/data/com.target.app/shared_prefs/secrets.xml
```

### Manual Smali Patching (for specific bypasses)

```bash
# 1. Decompile
apktool d target.apk -o target_src

# 2. Find and modify smali (example: bypass Play Services)
# Edit: target_src/smali_classes*/com/google/android/gms/common/GoogleApiAvailability.smali
# Change isGooglePlayServicesAvailable() to return 0 (SUCCESS)

# 3. Rebuild
apktool b target_src -o patched.apk

# 4. Align (required before signing)
zipalign -f 4 patched.apk patched_aligned.apk

# 5. Sign with debug key
apksigner sign --ks ~/.android/debug.keystore \
  --ks-key-alias androiddebugkey \
  --ks-pass pass:android \
  patched_aligned.apk

# 6. Install
adb install patched_aligned.apk
```

### Common Patching Targets

| Target | Location | Patch |
|--------|----------|-------|
| SSL Pinning | OkHttp, TrustManager | Return true/success |
| Root Detection | Various detection libs | Return false |
| Play Services | GoogleApiAvailability | Return 0 (SUCCESS) |
| Debug Detection | isDebuggable checks | Return false |
| Emulator Detection | Build.FINGERPRINT checks | Return false |

---

## Dynamic Analysis / Runtime Instrumentation

### Maestro UI Automation

Maestro enables automated UI interactions during dynamic analysis - useful for triggering specific app flows while monitoring with Frida or capturing traffic.

#### Installation

```bash
# Requires Java 17+
curl -fsSL "https://get.maestro.mobile.dev" | bash

# Verify
maestro --version
```

#### Basic Flow Syntax (YAML)

```yaml
# login_flow.yaml
appId: com.herohealth.heroconnect
---
- launchApp
- tapOn: "Log In"
- tapOn:
    id: "email_input"
- inputText: "test@example.com"
- tapOn:
    id: "password_input"
- inputText: "password123"
- tapOn: "Sign In"
- assertVisible: "Dashboard"
```

#### Key Maestro Commands

| Command | Description | Example |
|---------|-------------|---------|
| `launchApp` | Start the app | `- launchApp` |
| `tapOn` | Tap element by text/id | `- tapOn: "Login"` |
| `inputText` | Enter text | `- inputText: "user@test.com"` |
| `assertVisible` | Verify element visible | `- assertVisible: "Success"` |
| `swipe` | Swipe gesture | `- swipe: DOWN` |
| `scroll` | Scroll until visible | `- scroll` |
| `waitForAnimationToEnd` | Wait for animations | `- waitForAnimationToEnd` |
| `takeScreenshot` | Capture screen | `- takeScreenshot: output.png` |
| `runScript` | Run JS for complex logic | `- runScript: check.js` |

#### Running Flows

```bash
# Run single flow
maestro test login_flow.yaml

# Run with connected device
maestro test --device emulator-5554 login_flow.yaml

# Record interactions to create flow
maestro record

# Studio mode (visual editor)
maestro studio
```

#### Maestro + Frida Workflow

```bash
# Terminal 1: Start Frida hooks
frida -U -f com.herohealth.heroconnect -l hermes_hooks.js
# Terminal 2: Run Maestro flow to trigger app behavior
maestro test trigger_auth_flow.yaml

# Frida will log all intercepted calls as Maestro drives the UI
```

---

### Burp Suite Traffic Interception

Capture and analyze HTTPS traffic from the app during dynamic analysis.

#### Prerequisites

- Burp Suite (Community or Pro)
- Android emulator WITHOUT Google Play Store (for root access)
- rootAVD tool (for system certificate installation)
- OpenSSL

#### Setup Steps

**1. Export Burp Certificate**

```bash
# In Burp: Proxy > Options > Import/Export CA Certificate > Export in DER format
# Save as: burp_cert.der
```

**2. Convert Certificate Format**

```bash
# Convert DER to PEM
openssl x509 -inform DER -in burp_cert.der -out burp_cert.pem

# Get hash for Android system store filename
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp_cert.pem | head -1)
echo "Certificate hash: $HASH"

# Rename to Android format
cp burp_cert.pem ${HASH}.0
```

**3. Install Certificate on Emulator (Rooted)**

```bash
# Start emulator with writable system
emulator -avd YOUR_AVD -writable-system

# Wait for boot, then root
adb root
adb remount

# Push certificate to system store
adb push ${HASH}.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0

# Reboot to apply
adb reboot
```

**4. Alternative: Temporary Mount (Non-Persistent)**

```bash
# If remount fails, use tmpfs overlay
adb root
adb shell "mount -t tmpfs tmpfs /system/etc/security/cacerts"

# Copy existing certs
adb shell "cp /system_ext/etc/security/cacerts/* /system/etc/security/cacerts/"

# Push Burp cert
adb push ${HASH}.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0
```

**5. Configure Proxy on Emulator**

```bash
# Get your machine's IP
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "Use IP: $IP"

# Set proxy via ADB
adb shell settings put global http_proxy $IP:8080

# Or in emulator: Settings > Network & Internet > Wi-Fi > [network] > Proxy > Manual
# Host: YOUR_IP, Port: 8080
```

**6. Configure Burp Suite**

```
Proxy > Options > Proxy Listeners:
  - Bind to port: 8080
  - Bind to address: All interfaces (or specific IP)

Proxy > Intercept:
  - Intercept is on/off (as needed)
```

#### Clear Proxy When Done

```bash
adb shell settings put global http_proxy :0
```

### Burp Suite MCP Server (AI Integration)

The Burp MCP Server enables direct control of Burp Suite from Claude/AI assistants via the Model Context Protocol.

#### Installation

```bash
# Clone and build
git clone https://github.com/PortSwigger/mcp-server.git
cd mcp-server
./gradlew embedProxyJar
# Creates: build/libs/burp-mcp-all.jar

# Load in Burp Suite:
# Extensions > Add > Java > Select burp-mcp-all.jar
```

#### Configuration

In Burp Suite MCP tab:
- Enable server: ON
- Host: `127.0.0.1`
- Port: `9876` (default)

For Claude Desktop, add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "burp": {
      "command": "java",
      "args": ["-jar", "/path/to/mcp-server/build/libs/burp-mcp-proxy.jar", "http://127.0.0.1:9876"]
    }
  }
}
```

#### Available MCP Tools

Once configured, Claude can directly:
- View and filter proxy history
- Analyze requests/responses
- Send requests to Repeater
- Scan targets with active scanner
- Access site map data
- Control proxy intercept

#### Usage with Claude Code

When Burp MCP is configured, you can ask Claude to:
- "Show me all requests to the /api endpoint"
- "Find requests containing auth tokens"
- "Send this request to Repeater and modify the parameter"
- "Start a scan on this endpoint"

---

#### Burp + Maestro + Frida Full Workflow

```bash
# Terminal 1: Burp Suite listening on 8080

# Terminal 2: Frida hooks
frida -U -f com.herohealth.heroconnect -l ssl_bypass.js -l hermes_hooks.js
# Terminal 3: Maestro automation
maestro test full_app_flow.yaml

# Result: Burp captures all HTTPS traffic, Frida logs JS execution,
# Maestro automates the UI interactions
```

---

### Frida Setup for Hermes Apps

```bash
# Install Frida
pip install frida-tools

# Push frida-server to device (rooted/emulator)
adb push frida-server-android-arm64 /data/local/tmp/
adb shell chmod +x /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# Verify connection
frida-ps -U
```

**Example frida-ps output:**
```
  PID  Name
-----  -------------------------------------------
  234  adbd
  567  system_server
 1234  com.android.launcher3
 5678  com.target.app              <-- Your target app
```

### Basic Hermes Hooking (Frida)

```javascript
// hermes_hooks.js - Basic Hermes function interception

// Hook native Hermes runtime call
Interceptor.attach(Module.findExportByName("libhermes.so", "_ZN8facebook6hermes17HermesRuntimeImpl4callERKN8facebook3jsi8FunctionERKNS3_5ValueEPS7_m"), {
    onEnter: function(args) {
        console.log("[Hermes] Function call intercepted");
    }
});

// Hook JavaScript function by scanning strings
// Note: This is experimental due to Hermes internals
var modules = Process.enumerateModules();
modules.forEach(function(m) {
    if (m.name.indexOf("hermes") !== -1) {
        console.log("Found Hermes module: " + m.name + " at " + m.base);
    }
});
```

### Using heresy for Runtime Instrumentation

```bash
# Setup heresy
cd heresy
cp -r .heresy.example .heresy
# Edit .heresy/config.json with target package name

# Start tunnel (required for HTTPS)
ssh -R 80:localhost:3000 serveo.net

# Run heresy
npm run start

# Available RPC commands:
# - alert: Display notification in app
# - dump_this: List global properties
# - dump_env: Expose process variables
# - eval: Execute arbitrary JavaScript
```

### Intercept Network Requests

```javascript
// frida_network.js - Intercept XMLHttpRequest in Hermes apps

Java.perform(function() {
    // Hook OkHttp (common in React Native)
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");
    var Builder = Java.use("okhttp3.OkHttpClient$Builder");

    Builder.build.implementation = function() {
        console.log("[OkHttp] Client built");
        return this.build();
    };

    // Hook React Native's fetch
    var RCTNetworking = Java.use("com.facebook.react.modules.network.NetworkingModule");
    RCTNetworking.sendRequest.overload('java.lang.String', 'java.lang.String', 'int', 'com.facebook.react.bridge.ReadableArray', 'com.facebook.react.bridge.ReadableMap', 'java.lang.String', 'boolean', 'int', 'boolean').implementation = function(method, url, requestId, headers, data, responseType, useIncrementalUpdates, timeout, withCredentials) {
        console.log("[RN Fetch] " + method + " " + url);
        return this.sendRequest(method, url, requestId, headers, data, responseType, useIncrementalUpdates, timeout, withCredentials);
    };
});
```

### Pre-built Frida Scripts

The `scripts/frida/` directory contains comprehensive bypass scripts:

| Script | Purpose | Source |
|--------|---------|--------|
| `universal_ssl_bypass.js` | SSL/TLS pinning bypass (40+ methods) | Based on frida-multiple-unpinning |
| `root_bypass.js` | Root/emulator detection bypass | Based on fridantiroot |
| `gms_firebase_bypass.js` | Google Play Services & Firebase bypass | Custom |
| `detect_frameworks.js` | Identify frameworks and libraries | Custom |
| `hermes_hooks.js` | React Native bridge hooks | Custom |
| `ssl_bypass.js` | Basic SSL bypass | Custom |

#### Quick Usage

```bash
# SSL pinning bypass (comprehensive)
frida -U -f com.target.app -l scripts/frida/universal_ssl_bypass.js

# Root detection bypass
frida -U -f com.target.app -l scripts/frida/root_bypass.js

# GMS/Firebase bypass (for emulators without Play Services)
frida -U -f com.target.app -l scripts/frida/gms_firebase_bypass.js

# Detect what frameworks the app uses
frida -U -f com.target.app -l scripts/frida/detect_frameworks.js

# Combined bypass (SSL + Root + GMS)
cat scripts/frida/universal_ssl_bypass.js scripts/frida/root_bypass.js scripts/frida/gms_firebase_bypass.js > /tmp/all_bypass.js
frida -U -f com.target.app -l /tmp/all_bypass.js
```

#### Universal SSL Bypass Coverage

The `universal_ssl_bypass.js` script bypasses:
- OkHttp3 CertificatePinner (all overloads including Kotlin)
- TrustManager (Android < 7 and > 7)
- Conscrypt TrustManagerImpl and OpenSSLSocketImpl
- TrustKit, Appcelerator, Fabric
- Squareup OkHttp (pre-v3)
- PhoneGap/Cordova, Flutter plugins
- React Native OkHttpClientProvider
- WebView SSL errors
- Network Security Config
- Dynamic SSLPeerUnverifiedException bypass

#### Root/Emulator Bypass Coverage

The `root_bypass.js` script bypasses:
- Package checks (Magisk, SuperSU, Xposed, Kingroot, etc.)
- Binary file checks (su, busybox, magisk)
- System property checks (ro.debuggable, ro.secure, ro.build.tags)
- Runtime.exec and ProcessBuilder commands
- Native fopen/access hooks
- TelephonyManager spoofing (IMEI, IMSI)

#### Framework Detection

The `detect_frameworks.js` script identifies:
- **Frameworks**: React Native, Hermes, Flutter, Xamarin, Cordova, Unity
- **Networking**: OkHttp, Retrofit, Volley, Apollo GraphQL
- **Analytics**: Firebase, Google Analytics, Facebook SDK, Mixpanel, Amplitude, Segment
- **Security**: TrustKit, RootBeer, SafetyNet, Play Integrity, DexGuard
- **Storage**: Room, Realm, SQLCipher, EncryptedSharedPreferences

### SSL Bypass Scripts

For SSL pinning bypass, use the pre-built scripts in `scripts/frida/`:

- **`universal_ssl_bypass.js`** - Comprehensive bypass (40+ methods) - use this by default
- **`ssl_bypass.js`** - Basic OkHttp + TrustManager bypass

See the [Pre-built Frida Scripts](#pre-built-frida-scripts) section above for full coverage details.

---

## Emulator Setup for Penetration Testing

### Prerequisites

- Android Studio installed
- SDK Platform Tools
- System images (WITHOUT Google Play for root access)

### Creating a Rooted Test Emulator

**CRITICAL**: For security testing, you need an emulator that:
1. Can be rooted (adb root works)
2. Has writable /system (for cert installation)
3. Does NOT have Google Play Store (Play Protect blocks testing)

#### Step 1: Install Required SDK Components

```bash
# List available system images
sdkmanager --list | grep "system-images"

# Install a Google APIs image (NOT Google Play!)
# Google APIs = rootable, Google Play = locked down
sdkmanager "system-images;android-34;google_apis;x86_64"
sdkmanager "system-images;android-33;google_apis;x86_64"
sdkmanager "system-images;android-30;google_apis;x86_64"  # Recommended for compatibility

# Also ensure platform-tools and emulator are installed
sdkmanager "platform-tools" "emulator"
```

#### Step 2: Create AVD for Testing

```bash
# Create AVD with Google APIs (rootable)
avdmanager create avd \
    --name "pentest_api30" \
    --package "system-images;android-30;google_apis;x86_64" \
    --device "pixel_4"

# Or for newer Android
avdmanager create avd \
    --name "pentest_api34" \
    --package "system-images;android-34;google_apis;x86_64" \
    --device "pixel_7"

# List created AVDs
avdmanager list avd
```

#### Step 3: Boot with Writable System

```bash
# Boot with writable system partition (REQUIRED for cert install)
emulator -avd pentest_api30 -writable-system &

# Wait for boot
adb wait-for-device
adb shell getprop sys.boot_completed  # Wait until returns "1"

# Verify root access works
adb root
# Should say: "restarting adbd as root"

# Verify system is writable
adb remount
# Should say: "remount succeeded"
```

#### Step 4: Install Burp/Proxy Certificate

Use the automated script or follow detailed instructions in [Burp Suite Traffic Interception](#burp-suite-traffic-interception).

**Quick method using script:**
```bash
./scripts/setup_burp_cert.sh /path/to/burp_cert.der
```

**Or manually:**
```bash
# Convert cert and push to system store (requires root)
openssl x509 -inform DER -in burp_cert.der -out burp_cert.pem
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp_cert.pem | head -1)
cp burp_cert.pem ${HASH}.0
adb root && adb remount
adb push ${HASH}.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0
adb reboot
```

#### Step 5: Configure Proxy

```bash
# Get your machine's IP
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

# Set global proxy
adb shell settings put global http_proxy $IP:8080

# Verify
adb shell settings get global http_proxy

# Clear when done
adb shell settings put global http_proxy :0
```

### Emulator Quick Reference

| Image Type | Root Access | Play Store | Use For |
|------------|-------------|------------|---------|
| `google_apis` | YES | NO | Security testing |
| `google_apis_playstore` | NO | YES | Normal app testing |
| `default` (AOSP) | YES | NO | Basic testing |

### Recommended Test Configurations

```bash
# API 30 (Android 11) - Best compatibility
avdmanager create avd --name "pentest_30" \
    --package "system-images;android-30;google_apis;x86_64" \
    --device "pixel_4"

# API 33 (Android 13) - Modern testing
avdmanager create avd --name "pentest_33" \
    --package "system-images;android-33;google_apis;x86_64" \
    --device "pixel_6"

# API 34 (Android 14) - Latest
avdmanager create avd --name "pentest_34" \
    --package "system-images;android-34;google_apis;x86_64" \
    --device "pixel_7"
```

### Startup Script for Testing Session

```bash
#!/bin/bash
# start_pentest_emulator.sh

AVD_NAME="${1:-pentest_api30}"
PROXY_PORT="${2:-8080}"

# Get host IP
HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

echo "[*] Starting emulator: $AVD_NAME"
emulator -avd $AVD_NAME -writable-system -no-snapshot-load &

echo "[*] Waiting for boot..."
adb wait-for-device
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null)" != "1" ]; do
    sleep 2
done

echo "[*] Enabling root..."
adb root
sleep 2
adb remount

echo "[*] Setting proxy to $HOST_IP:$PROXY_PORT"
adb shell settings put global http_proxy $HOST_IP:$PROXY_PORT

echo "[+] Emulator ready for testing"
echo "    Proxy: $HOST_IP:$PROXY_PORT"
echo "    Clear proxy: adb shell settings put global http_proxy :0"
```

### Troubleshooting

#### "adbd cannot run as root in production builds"
You're using a Google Play image. Use `google_apis` instead:
```bash
sdkmanager "system-images;android-30;google_apis;x86_64"
```

#### "remount failed: Operation not permitted"
Boot with `-writable-system` flag:
```bash
emulator -avd YOUR_AVD -writable-system
```

#### Certificate not trusted by app
Some apps use certificate pinning. Use Frida to bypass:
```bash
frida -U -f com.target.app -l scripts/frida/ssl_bypass.js```

#### Emulator too slow
Enable hardware acceleration:
```bash
# Check HAXM/KVM status
emulator -accel-check

# Run with GPU acceleration
emulator -avd YOUR_AVD -gpu host
```

#### App shows black screen / requires Google Play Services

**Problem**: Apps that depend on Google Play Services (Firebase, FCM, Google Sign-In, Play Integrity) will fail or show black screens on `google_apis` emulator images because these images don't include Play Services.

**The Trade-off**:
| Image Type | Root Access | Play Services | Writable System |
|------------|-------------|---------------|-----------------|
| `google_apis` | ✅ YES | ❌ NO | ✅ YES |
| `google_apis_playstore` | ❌ NO | ✅ YES | ❌ NO |

**Solutions (in order of preference)**:

1. **Patch APK to stub Play Services checks** (Recommended for pentest):
   ```bash
   # Use Objection to inject Frida gadget and resign
   objection patchapk -s target.apk

   # Or manually patch smali to bypass checks:
   # 1. Decompile with apktool
   apktool d target.apk -o target_src

   # 2. Find and stub GoogleApiAvailability.isGooglePlayServicesAvailable()
   # In smali_classes*/com/google/android/gms/common/GoogleApiAvailability.smali:
   # Change the method to always return 0 (SUCCESS)

   # 3. Rebuild, align, and sign
   apktool b target_src -o patched.apk
   zipalign -f 4 patched.apk patched_aligned.apk
   apksigner sign --ks ~/.android/debug.keystore --ks-key-alias androiddebugkey patched_aligned.apk
   ```

2. **Install OpenGApps** (Adds real GMS to rooted emulator):

   **Prerequisites**: lzip (`brew install lzip` / `apt install lzip`)

   **Step 1: Check emulator architecture**
   ```bash
   adb shell getprop ro.product.cpu.abi
   # arm64-v8a = ARM64, x86_64 = Intel 64-bit
   # CRITICAL: Download must match this exactly!
   ```

   **Step 2: Download from https://opengapps.org/**
   - Select matching Platform (arm64/x86_64), Android version, Variant (pico is smallest)
   - Download the .zip file

   **Step 3: Extract APKs**
   ```bash
   # Create work directory
   mkdir -p /tmp/gapps_extract && cd /tmp/gapps_extract

   # Extract outer zip
   unzip ~/Downloads/open_gapps-*.zip

   # Extract GMS Core (Play Services)
   mkdir -p gmscore && lzip -dc Core/gmscore-*.tar.lz | tar -xf - -C gmscore

   # Extract GSF (Google Services Framework)
   mkdir -p gsf && lzip -dc Core/googleservicesframework-*.tar.lz | tar -xf - -C gsf
   ```

   **Step 4: Create permissions whitelist (CRITICAL)**

   OpenGApps requires privileged permissions whitelisting. Without this, system crashes with:
   `IllegalStateException: Signature|privileged permissions not in privapp-permissions whitelist`

   Use the template at `templates/privapp-permissions-google.xml` or create manually:
   ```bash
   # Copy the permissions whitelist template
   cp /path/to/hermes-skill/templates/privapp-permissions-google.xml /tmp/
   ```

   **Step 5: Push to emulator**
   ```bash
   # Remount system as writable
   adb root && adb remount

   # Push permissions whitelist FIRST
   adb push /tmp/privapp-permissions-google.xml /system/etc/permissions/

   # Push GMS Core
   adb push gmscore/*/nodpi/priv-app/PrebuiltGmsCore /system/priv-app/

   # Push GSF
   adb push gsf/*/nodpi/priv-app/GoogleServicesFramework /system/priv-app/

   # Set permissions (required)
   adb shell chmod 755 /system/priv-app/PrebuiltGmsCore
   adb shell chmod 755 /system/priv-app/GoogleServicesFramework
   adb shell chmod 644 /system/priv-app/PrebuiltGmsCore/*.apk
   adb shell chmod 644 /system/priv-app/GoogleServicesFramework/*.apk

   # Reboot for changes to take effect
   adb reboot
   ```

   **Step 6: Verify installation**
   ```bash
   adb wait-for-device && adb shell getprop sys.boot_completed | grep -q 1
   adb shell pm list packages | grep -E "(gms|gsf)"
   # Should show: com.google.android.gms, com.google.android.gsf
   ```

   **⚠️ Caveats**:
   - **Do NOT install Play Store (Phonesky)** from older OpenGApps - causes system instability
   - GMS Core + GSF alone is usually sufficient for Firebase/FCM dependencies
   - If app still fails, it may require Play Integrity which needs real Play Store
   - Consider APK patching (Option 1) as more reliable alternative

3. **Use MicroG** (Lighter alternative, may not satisfy all apps):
   - Download from https://microg.org/download.html
   - Requires signature spoofing support (not available on stock emulators)

4. **Use a physical rooted device** with Play Services for full dynamic testing

5. **Focus on static analysis** - Hermes decompilation, JADX, secrets extraction still work

**Detecting Play Services Dependency**:
```bash
# Check AndroidManifest for Play Services requirements
jadx -d /tmp/jadx_out target.apk
grep -r "com.google.android.gms" /tmp/jadx_out/resources/AndroidManifest.xml
grep -r "play-services" /tmp/jadx_out/

# Check for Firebase
grep -r "firebase" /tmp/jadx_out/resources/ | head -20
```

---

## Emulator Workflows (from android-emulator-skill)

### Boot Emulator for Testing

```bash
# List available AVDs
emulator -list-avds

# Boot emulator (for pentest, always use -writable-system)
emulator -avd pentest_api30 -writable-system &

# Wait for device ready
adb wait-for-device
adb shell getprop sys.boot_completed | grep -q 1 || sleep 5

# Verify
adb devices
```

### Install and Launch Target App

```bash
# Install APK
adb install -r target_app.apk

# Get package name
adb shell pm list packages | grep -i appname

# Launch app
adb shell am start -n com.example.app/.MainActivity

# Or with deep link
adb shell am start -a android.intent.action.VIEW -d "myapp://path"
```

### Extract Runtime Data

```bash
# Pull app data (requires root/debug build)
adb root
adb pull /data/data/com.example.app/ ./app_data/

# Capture logcat for React Native
adb logcat -s ReactNative:V ReactNativeJS:V

# Capture Hermes-specific logs
adb logcat | grep -i hermes
```

### Screen Capture During Analysis

```bash
# Screenshot
adb exec-out screencap -p > screen.png

# Screen record
adb shell screenrecord /sdcard/analysis.mp4 &
# ... perform actions ...
adb shell pkill -l INT screenrecord
adb pull /sdcard/analysis.mp4
```

---

## r2hermes Command Reference

| Command | Description |
|---------|-------------|
| `pd:h` | Decompile function at current offset |
| `pd:hc [id]` | Decompile function by ID |
| `pd:ha` | Decompile all functions |
| `pd:hf` | List all functions |
| `pd:hi` | Show file info and hash status |
| `pd:hj [id]` | JSON output for function |
| `pd:ho [id]` | Decompile with offsets per statement |
| `pd:hoa` | Decompile all with offsets |
| `.(fix-hbc)` | Fix/update footer hash (for patching) |

### r2hermes Configuration

```bash
e hbc.pretty_literals=true    # Pretty-print objects/arrays
e hbc.suppress_comments=false # Show/hide comments
e hbc.show_offsets=false      # Show bytecode offsets
```

---

## Analysis Patterns

### Find API Endpoints

```bash
# r2hermes string search
r2 -qc 'pd:ha' bundle.hbc | grep -E 'https?://'

# hermes_rs string extraction
hermes_rs strings bundle.hbc | grep -E 'api|endpoint|url'

# Search decompiled output
grep -r "fetch\|axios\|XMLHttpRequest" decompiled.js
```

### Find Authentication Logic

```bash
# Function search
r2 -qc 'pd:hf' bundle.hbc | grep -iE 'auth|login|token|jwt|session|password'

# String search
hermes_rs strings bundle.hbc | grep -iE 'bearer|authorization|x-api-key'
```

### Find Encryption/Security

```bash
# Look for crypto references
r2 -qc 'pd:hf' bundle.hbc | grep -iE 'encrypt|decrypt|crypto|aes|rsa|hash|hmac'

# Check for hardcoded keys
hermes_rs strings bundle.hbc | grep -iE 'key|secret|private'
```

### Find Premium/License Checks

```bash
# Common patterns
r2 -qc 'pd:hf' bundle.hbc | grep -iE 'premium|license|subscribe|purchase|paid|pro'

# Decompile suspicious functions
r2 -qc 'pd:hc FUNCTION_ID' bundle.hbc
```

---

## Output Format

Structure analysis findings as:

```json
{
  "bundle_info": {
    "file": "index.android.bundle",
    "hermes_version": 94,
    "function_count": 1247,
    "hash_status": "valid"
  },
  "tools_used": ["r2hermes", "hermes_rs"],
  "findings": [
    {
      "type": "api_endpoint",
      "value": "https://api.example.com/v1/auth",
      "function_id": 42,
      "source": "string extraction"
    },
    {
      "type": "hardcoded_secret",
      "value": "API_KEY_REDACTED",
      "function_id": 108,
      "severity": "high"
    }
  ],
  "functions_of_interest": [
    {
      "id": 42,
      "name": "authenticateUser",
      "purpose": "Handles user authentication via REST API",
      "calls": ["fetch", "JSON.parse"],
      "patched": false
    }
  ]
}
```

---

## Troubleshooting

### "Invalid Hermes version"

Different tools support different versions. Check version and use appropriate tool:

```bash
# Check version
r2 -qc 'pd:hi' bundle.hbc | grep version

# Version 96: Use r2hermes or hermes_rs
# Version 74-76: Use hbctool, r2hermes, or hermes_rs
# Version 59-62: Use hbctool or hermes-dec
```

### "Hash mismatch after patching"

Always fix hash after modifying bytecode:

```bash
r2 -wqc '.(fix-hbc)' bundle.hbc
```

### "Function not found"

Functions may be inlined or named generically. Search by behavior:

```bash
# Decompile all and search
r2 -qc 'pd:ha' bundle.hbc > all.js
grep -n "targetString" all.js
```

### "Frida can't attach to Hermes"

Hermes internals are not easily hooked. Use:
1. heresy for JS-level instrumentation
2. Hook at OkHttp/network layer instead
3. Patch bytecode statically instead of runtime hooks

---

## Frida & r2frida Setup

### Version Compatibility

Frida tools and frida-server versions must be compatible:

```bash
# Check local frida version
frida --version

# frida-server on device must match (major.minor)
adb shell /data/local/tmp/frida-server --version
```

**Known Working Combinations:**
| frida-tools | frida-server | r2frida | Notes |
|-------------|--------------|---------|-------|
| 17.6.2 | 17.5.0 | latest | 17.6.2 server crashes on some emulators |
| 16.3.3 | 16.3.3 | N/A | r2frida needs 17.x |

### Installing frida-server

```bash
# Check device architecture
adb shell getprop ro.product.cpu.abi  # arm64-v8a, x86_64, etc.

# Download matching version from GitHub releases
curl -sL "https://github.com/frida/frida/releases/download/17.5.0/frida-server-17.5.0-android-arm64.xz" -o /tmp/frida-server.xz
xz -d /tmp/frida-server.xz

# Push and start
adb push /tmp/frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell "su 0 /data/local/tmp/frida-server -D &"

# Verify
frida-ps -U
```

### r2frida Quick Reference

```bash
# Attach to running app
r2 frida://attach/usb//AppName

# Common commands inside r2frida:
:il                        # List native libraries
:icl                       # List Java classes
:icm ClassName             # List methods of a class
:dt java:Class.method      # Trace method calls
:di0 java:Class.method     # Hook to return 0
:di1 java:Class.method     # Hook to return 1
:dibt java:Class.method    # Hook to return true
:dibf java:Class.method    # Hook to return false
```

---

## Firebase/FCM Bypass Techniques

Apps using Firebase often block on FCM token retrieval. Common blocking points:

### Identifying Firebase Blocking

```bash
# Check logcat for blocking calls
adb logcat | grep -iE "(firebase|fcm|block|timeout)"

# Common blocking signatures:
# - FirebaseMessaging.blockingGetToken
# - SyncTask.maybeRefreshToken
# - FirebaseInstallations.registerFidWithServer
```

### Smali Patch: Bypass SyncTask Blocking

The `SyncTask.maybeRefreshToken()` method blocks waiting for FCM tokens. Patch to return immediately:

```smali
# File: smali_classes*/com/google/firebase/messaging/SyncTask.smali
# Find method: .method maybeRefreshToken()Z

# Add at start of method:
    const/4 v0, 0x1
    return v0
# This returns true immediately, skipping the blocking call
```

### Frida Hook: Runtime FCM Bypass

```javascript
Java.perform(function() {
    // Bypass SyncTask blocking
    var SyncTask = Java.use("com.google.firebase.messaging.SyncTask");
    SyncTask.maybeRefreshToken.implementation = function() {
        console.log("[+] SyncTask.maybeRefreshToken bypassed");
        return true;
    };

    // Bypass FirebaseMessaging.blockingGetToken
    var FirebaseMessaging = Java.use("com.google.firebase.messaging.FirebaseMessaging");
    FirebaseMessaging.blockingGetToken.implementation = function() {
        console.log("[+] blockingGetToken bypassed");
        return "fake_fcm_token_for_testing";
    };
});
```

---

## Common App Blocking Issues

### Two Levels of GMS Dependency

Apps may have different levels of Google dependency:

| Level | Package Required | Error Code | Solution |
|-------|------------------|------------|----------|
| **GMS Core** | com.google.android.gms | `SERVICE_MISSING` | Install OpenGApps GMS+GSF |
| **Play Store** | com.android.vending | `SERVICE_INVALID` | Patch APK or use real device |

**Detecting which level:**
```bash
adb logcat | grep -i "GooglePlayServicesUtil"
# "requires the Google Play Store" = Play Store level
# "Google Play services is missing" = GMS Core level
```

### App Stuck on Splash Screen

**Possible causes:**
1. **Play Services check blocking** - Patch GooglePlayServicesUtilLight.isGooglePlayServicesAvailable
2. **Firebase/FCM blocking** - Patch SyncTask.maybeRefreshToken
3. **Network timeout** - Check connectivity, may need real backend
4. **Debug mode waiting** - Check for "waiting for debugger" in logcat

**Diagnostic steps:**
```bash
# Check what's blocking
adb logcat -d | grep -iE "(block|wait|timeout|firebase|gms)"

# Check activity state
adb shell dumpsys activity top | head -20
```

### Signature Verification Failures

After patching, apps may fail signature checks:
```bash
# Sign with debug key
apksigner sign --ks ~/.android/debug.keystore \
  --ks-key-alias androiddebugkey \
  --ks-pass pass:android \
  patched.apk

# Or use Objection to handle signing
objection patchapk -s original.apk
```

---

## Security Considerations

- Only analyze applications you have authorization to test
- Do not distribute modified APKs
- Respect application licenses and terms of service
- Report vulnerabilities responsibly

---

## Security Report Writing

This section provides comprehensive guidance for creating professional security assessment reports that align with industry standards and compliance frameworks.

### Report Structure Template

```markdown
# Security Assessment Report

## Document Control
| Field | Value |
|-------|-------|
| Client | [Organization Name] |
| Application | [App Name] v[Version] |
| Assessment Date | [Date Range] |
| Report Version | 1.0 |
| Classification | Confidential |
| Assessor | [Name/Team] |

## Executive Summary

### Assessment Overview
Brief description of scope, methodology, and high-level findings.

### Risk Summary
| Severity | Count |
|----------|-------|
| Critical | X |
| High | X |
| Medium | X |
| Low | X |
| Info | X |

### Key Findings
Bullet points of most significant issues.

### Recommendations
Top priority actions for immediate attention.

## Compliance Dashboard

[See OWASP MASVS Compliance section below]

## Security Controls Assessment

[See Controls Assessment section below]

## Detailed Findings

[See Finding Format section below]

## Remediation Roadmap

[See Remediation section below]

## Appendix
- Testing Tools Used
- Test Cases Executed
- Raw Evidence
```

---

### OWASP MASVS v2.0 Categories

The Mobile Application Security Verification Standard (MASVS) defines security requirements for mobile apps. Use these categories to structure findings:

| Category | ID | Description | Focus Areas |
|----------|-----|-------------|-------------|
| **Storage** | MASVS-STORAGE | Secure data storage | SharedPrefs, databases, files, logs, backups, clipboard |
| **Crypto** | MASVS-CRYPTO | Cryptography usage | Key management, algorithms, random number generation |
| **Auth** | MASVS-AUTH | Authentication & Session | Login, session tokens, biometrics, 2FA |
| **Network** | MASVS-NETWORK | Network communication | TLS, certificate pinning, data in transit |
| **Platform** | MASVS-PLATFORM | Platform interaction | IPC, deep links, WebViews, permissions |
| **Code** | MASVS-CODE | Code quality & security | Input validation, memory safety, anti-tampering |
| **Resilience** | MASVS-RESILIENCE | Resilience against attacks | Root detection, debugging protection, obfuscation |

---

### MASTG Test ID Reference

The Mobile Application Security Testing Guide (MASTG) provides specific test cases. Map findings to these IDs:

#### MASVS-STORAGE Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0001 | Testing Local Storage for Sensitive Data | SharedPrefs, SQLite, files in app directory |
| MASTG-TEST-0002 | Testing Logs for Sensitive Data | Logcat output, Log.d/Log.v calls |
| MASTG-TEST-0003 | Testing Backups for Sensitive Data | android:allowBackup, adb backup extraction |
| MASTG-TEST-0004 | Testing Sensitive Data in Memory | Memory dumps, heap analysis |
| MASTG-TEST-0005 | Testing the Device-Access-Security Policy | Keyguard, screen lock requirements |
| MASTG-TEST-0011 | Testing Local Storage for Input Validation | SQL injection in local DB |

#### MASVS-CRYPTO Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0013 | Testing the Configuration of Cryptographic Standard Algorithms | AES mode, key length, IV usage |
| MASTG-TEST-0014 | Testing Key Management | Hardcoded keys, KeyStore usage |
| MASTG-TEST-0015 | Testing Random Number Generation | SecureRandom vs Random |

#### MASVS-AUTH Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0016 | Testing Biometric Authentication | Fingerprint implementation |
| MASTG-TEST-0017 | Testing Confirm Credentials | Re-authentication for sensitive ops |

#### MASVS-NETWORK Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0019 | Testing Data Encryption on the Network | TLS usage, HTTP traffic |
| MASTG-TEST-0020 | Testing TLS Settings | TLS version, cipher suites |
| MASTG-TEST-0021 | Testing Endpoint Identity Verification | Certificate pinning |
| MASTG-TEST-0022 | Testing Custom Certificate Stores | Network security config |

#### MASVS-PLATFORM Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0007 | Testing Deep Links | URL scheme handlers, intent validation |
| MASTG-TEST-0028 | Testing for Sensitive Functionality Exposure Through IPC | Exported components |
| MASTG-TEST-0029 | Testing for Vulnerable Implementation of PendingIntent | FLAG_IMMUTABLE |
| MASTG-TEST-0031 | Testing WebView Protocol Handlers | file://, javascript:// |
| MASTG-TEST-0033 | Testing for Java Objects in WebViews | addJavascriptInterface |

#### MASVS-CODE Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0039 | Testing Input Validation | Injection attacks, format strings |
| MASTG-TEST-0045 | Testing for Injection Flaws | SQL, command, XSS injection |
| MASTG-TEST-0046 | Testing Object Deserialization | Serializable, Parcelable abuse |

#### MASVS-RESILIENCE Tests

| Test ID | Test Name | What to Check |
|---------|-----------|---------------|
| MASTG-TEST-0047 | Testing Root Detection | Root detection bypass |
| MASTG-TEST-0048 | Testing Anti-Debugging | Debug detection |
| MASTG-TEST-0050 | Testing Emulator Detection | Emulator fingerprinting |
| MASTG-TEST-0051 | Testing File Integrity Checks | APK signature verification |

---

### Finding Format Template

Each finding should follow this structure:

```markdown
## Finding [N]: [Descriptive Title]

| Attribute | Value |
|-----------|-------|
| **Severity** | CRITICAL / HIGH / MEDIUM / LOW / INFO |
| **CVSS 3.1 Score** | X.X |
| **CVSS Vector** | CVSS:3.1/AV:X/AC:X/PR:X/UI:X/S:X/C:X/I:X/A:X |
| **CWE** | CWE-XXX: [CWE Name] |
| **MASVS Category** | MASVS-XXXXX |
| **MASTG Test** | MASTG-TEST-XXXX |
| **Status** | Open / Fixed / Accepted Risk |

### Description

[Technical description of the vulnerability]

### Affected Component(s)

- File: `path/to/file.java:line`
- Component: `com.package.ClassName`
- Manifest entry: `<receiver android:name="...">`

### Evidence

[Code snippets, screenshots, log output demonstrating the issue]

### Impact

[What an attacker can achieve by exploiting this vulnerability]

### Attack Scenario

1. Attacker does X
2. This causes Y
3. Resulting in Z

### Proof of Concept

```bash
# Command or code to reproduce
adb shell am broadcast -a ACTION -n com.app/.Receiver
```

### Remediation

**Short-term (Immediate):**
- Quick fix steps

**Long-term (Recommended):**
- Architectural improvements
- Best practices

### References

- [OWASP Link](https://mas.owasp.org/...)
- [CWE Link](https://cwe.mitre.org/data/definitions/XXX.html)
```

---

### CVSS 3.1 Scoring Guide

Calculate CVSS scores consistently using these metrics:

#### Attack Vector (AV)
| Value | Score | Description |
|-------|-------|-------------|
| Network (N) | 0.85 | Remotely exploitable |
| Adjacent (A) | 0.62 | Same network segment |
| Local (L) | 0.55 | Local access required |
| Physical (P) | 0.20 | Physical access required |

#### Attack Complexity (AC)
| Value | Score | Description |
|-------|-------|-------------|
| Low (L) | 0.77 | No special conditions |
| High (H) | 0.44 | Requires specific conditions |

#### Privileges Required (PR)
| Value | Score (Unchanged) | Score (Changed) | Description |
|-------|-------------------|-----------------|-------------|
| None (N) | 0.85 | 0.85 | No auth required |
| Low (L) | 0.62 | 0.68 | Basic user privileges |
| High (H) | 0.27 | 0.50 | Admin privileges |

#### User Interaction (UI)
| Value | Score | Description |
|-------|-------|-------------|
| None (N) | 0.85 | No user action needed |
| Required (R) | 0.62 | User must click/interact |

#### Impact Metrics (C/I/A)
| Value | Score | Description |
|-------|-------|-------------|
| High (H) | 0.56 | Total impact |
| Low (L) | 0.22 | Limited impact |
| None (N) | 0.00 | No impact |

#### Common Vulnerability CVSS Examples

| Finding Type | CVSS Score | Vector |
|--------------|------------|--------|
| RCE via exported component | 9.8 | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| SQL Injection (local) | 7.8 | CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| Exported receiver (no data) | 5.3 | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N |
| Hardcoded API key | 7.5 | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N |
| SSL pinning missing | 5.9 | CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N |
| Backup enabled | 4.6 | CVSS:3.1/AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N |
| Debug logging | 3.3 | CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N |

---

### CWE Reference for Mobile

Common CWEs encountered in Android/React Native apps:

| CWE ID | Name | Common Finding |
|--------|------|----------------|
| CWE-200 | Exposure of Sensitive Information | Hardcoded secrets, verbose logging |
| CWE-276 | Incorrect Default Permissions | Exported components without protection |
| CWE-295 | Improper Certificate Validation | Missing SSL pinning |
| CWE-312 | Cleartext Storage of Sensitive Info | Unencrypted SharedPrefs |
| CWE-319 | Cleartext Transmission | HTTP instead of HTTPS |
| CWE-352 | Cross-Site Request Forgery | Deep link parameter injection |
| CWE-532 | Insertion of Sensitive Info into Log | Debug logs with tokens/passwords |
| CWE-749 | Exposed Dangerous Method or Function | Exported components, JS interfaces |
| CWE-798 | Use of Hard-coded Credentials | API keys in BuildConfig |
| CWE-829 | Inclusion of Functionality from Untrusted Source | Dynamic code loading |
| CWE-862 | Missing Authorization | Intent handlers without permission |
| CWE-919 | Weaknesses in Mobile Applications | General mobile security issues |
| CWE-921 | Storage of Sensitive Data Unprotected | World-readable files |
| CWE-925 | Improper Verification of Intent by Broadcast Receiver | Intent spoofing |
| CWE-926 | Improper Export of Android Application Components | Over-exported components |
| CWE-927 | Use of Implicit Intent for Sensitive Communication | Broadcast without permission |
| CWE-939 | Improper Authorization in Handler for Custom URL Scheme | Deep link vulnerabilities |

---

### Compliance Dashboard Template

#### MASVS Compliance Matrix

```markdown
## OWASP MASVS v2.0 Compliance Status

| Category | Requirement | Status | Notes |
|----------|-------------|--------|-------|
| **MASVS-STORAGE** | | | |
| MASVS-STORAGE-1 | Secure credential storage | ⚠️ PARTIAL | See Finding #X |
| MASVS-STORAGE-2 | No sensitive data in logs | ❌ FAIL | See Finding #Y |
| **MASVS-CRYPTO** | | | |
| MASVS-CRYPTO-1 | Strong cryptography | ✅ PASS | |
| MASVS-CRYPTO-2 | Secure key management | ⚠️ PARTIAL | |
| **MASVS-AUTH** | | | |
| MASVS-AUTH-1 | Secure authentication | ✅ PASS | |
| MASVS-AUTH-2 | Session management | ✅ PASS | |
| **MASVS-NETWORK** | | | |
| MASVS-NETWORK-1 | TLS for all connections | ✅ PASS | |
| MASVS-NETWORK-2 | Certificate pinning | ❌ FAIL | See Finding #Z |
| **MASVS-PLATFORM** | | | |
| MASVS-PLATFORM-1 | Secure IPC | ❌ FAIL | See Finding #X |
| MASVS-PLATFORM-2 | WebView security | ✅ PASS | |
| MASVS-PLATFORM-3 | Deep link validation | ⚠️ PARTIAL | |
| **MASVS-CODE** | | | |
| MASVS-CODE-1 | Input validation | ✅ PASS | |
| MASVS-CODE-2 | Memory safety | ✅ PASS | |
| **MASVS-RESILIENCE** | | | |
| MASVS-RESILIENCE-1 | Anti-tampering | ❌ FAIL | No integrity checks |
| MASVS-RESILIENCE-2 | Anti-debugging | ⚠️ PARTIAL | |

**Legend**: ✅ PASS | ⚠️ PARTIAL | ❌ FAIL | ➖ N/A
```

---

### Healthcare/HIPAA Compliance Considerations

For healthcare applications, include additional compliance mapping:

#### HIPAA Technical Safeguards (45 CFR § 164.312)

| Safeguard | HIPAA Requirement | Assessment Finding | Status |
|-----------|-------------------|-------------------|--------|
| Access Control (a)(1) | Unique user identification | | |
| Access Control (a)(2) | Emergency access procedure | | |
| Audit Controls (b) | Hardware/software activity recording | | |
| Integrity (c)(1) | Mechanism to authenticate ePHI | | |
| Transmission Security (e)(1) | Integrity controls | | |
| Transmission Security (e)(2) | Encryption | TLS 1.2+ required | |

#### FDA 21 CFR Part 11 (Electronic Records)

For apps handling FDA-regulated data:

| Requirement | Section | Implementation | Status |
|-------------|---------|----------------|--------|
| Audit trails | 11.10(e) | Complete action logging | |
| Authority checks | 11.10(d) | Role-based access | |
| Electronic signatures | 11.100 | Unique ID + password | |
| Signature manifestation | 11.50 | Signer info with sig | |

---

### Security Controls Assessment

Assess the implementation of security controls:

```markdown
## Security Controls Assessment

### Authentication Controls

| Control | Expected | Observed | Gap |
|---------|----------|----------|-----|
| Password complexity | Min 8 chars, mixed | ✅ Implemented | None |
| Brute force protection | Lockout after 5 attempts | ⚠️ 10 attempts | Reduce threshold |
| Session timeout | 15 min idle | ❌ No timeout | Implement timeout |
| Biometric auth | Secure implementation | ✅ CryptoObject used | None |

### Data Protection Controls

| Control | Expected | Observed | Gap |
|---------|----------|----------|-----|
| Data at rest encryption | AES-256 | ✅ SQLCipher | None |
| Data in transit encryption | TLS 1.2+ | ✅ TLS 1.3 | None |
| Key storage | Android Keystore | ⚠️ SharedPrefs | Migrate to Keystore |
| Clipboard protection | Clear on background | ❌ Not implemented | Add clipboard clearing |

### Network Security Controls

| Control | Expected | Observed | Gap |
|---------|----------|----------|-----|
| Certificate pinning | Pin to leaf or intermediate | ❌ Not implemented | Add pinning |
| Network security config | No cleartext | ✅ cleartextTrafficPermitted=false | None |
| API authentication | Bearer tokens | ✅ Implemented | None |

### Platform Security Controls

| Control | Expected | Observed | Gap |
|---------|----------|----------|-----|
| Exported components | Protected or unexported | ❌ Unprotected receiver | Add permission |
| Deep link validation | Validate all parameters | ⚠️ Partial validation | Add validation |
| WebView hardening | No JS interfaces | ✅ No interfaces | None |
```

---

### Remediation Roadmap Template

```markdown
## Remediation Roadmap

### Immediate (0-7 days)
**Priority: CRITICAL and HIGH findings**

| Finding | Action | Owner | Target Date |
|---------|--------|-------|-------------|
| #1 FileProvider exposure | Restrict path patterns | Dev Team | Day 3 |
| #2 Exported receiver | Add signature permission | Dev Team | Day 5 |

### Short-term (7-30 days)
**Priority: MEDIUM findings, security improvements**

| Finding | Action | Owner | Target Date |
|---------|--------|-------|-------------|
| #3 SSL pinning | Implement OkHttp pinning | Dev Team | Week 2 |
| #4 Deep link validation | Add parameter validation | Dev Team | Week 3 |

### Long-term (30-90 days)
**Priority: LOW findings, architecture improvements**

| Finding | Action | Owner | Target Date |
|---------|--------|-------|-------------|
| #5 Anti-tampering | Implement integrity checks | Security | Month 2 |
| Root detection | Add RootBeer or custom | Security | Month 2 |

### Verification Testing

After remediation, re-test:
1. [ ] All CRITICAL and HIGH findings verified fixed
2. [ ] Regression testing passed
3. [ ] New security controls validated
4. [ ] Updated threat model reviewed
```

---

### Report Writing Best Practices

1. **Be specific** - Include exact file paths, line numbers, code snippets
2. **Provide evidence** - Screenshots, logs, PoC commands
3. **Explain impact** - What can an attacker actually do?
4. **Prioritize clearly** - CVSS provides objective severity ranking
5. **Map to standards** - MASVS/MASTG provides industry credibility
6. **Give actionable remediation** - Specific code changes, not vague advice
7. **Consider compliance** - HIPAA, PCI-DSS, SOC2 where applicable
8. **Include positive findings** - Security controls that ARE working
9. **Executive summary first** - Business impact in non-technical terms
10. **Appendix for details** - Keep main report focused, details in appendix

---

## Resources

- [Hermes GitHub](https://github.com/facebook/hermes)
- [r2hermes](https://github.com/radareorg/r2hermes)
- [hbctool](https://github.com/bongtrop/hbctool)
- [hermes-dec](https://github.com/P1sec/hermes-dec)
- [hermes_rs](https://github.com/Pilfer/hermes_rs)
- [heresy](https://github.com/Pilfer/heresy)
- [Frida](https://frida.re/)
