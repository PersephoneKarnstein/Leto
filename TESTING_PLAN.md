# Testing Plan for Lêtô Hermes Analysis Toolkit

This document outlines plans for comprehensive validation of the toolkit.

---

## Part A: Testing with Real-World React Native Apps

### Objective
Validate the toolkit against diverse, production React Native applications to identify edge cases, improve coverage, and ensure reliability.

### Target App Selection Criteria

Apps should cover:
- Different Hermes bytecode versions (v89-96)
- Various obfuscation levels (none, minified, obfuscated)
- Different authentication patterns (OAuth, JWT, session cookies)
- Both Android and iOS platforms
- Different app categories (social, finance, productivity)

### Proposed Test Targets

| App | Platform | Category | Hermes | Source | Notes |
|-----|----------|----------|--------|--------|-------|
| **Mattermost** | Android/iOS | Productivity | Yes | GitHub releases | Already tested - baseline |
| **Discord** | Android/iOS | Social | Yes | APKMirror | Large bundle (62MB), heavy obfuscation |
| **Shopify** | Android/iOS | E-commerce | Yes | APKMirror | Complex auth, payment flows |
| **Bloomberg** | Android/iOS | Finance | Yes | APKMirror | Financial data, likely strong security |
| **Coinbase** | Android | Finance | Yes | APKMirror | Crypto, likely heavy obfuscation |
| **Walmart** | Android/iOS | E-commerce | Yes | APKMirror | Large user base, mature app |
| **Wix** | Android/iOS | Productivity | Yes | APKMirror | App builder, diverse functionality |
| **Pinterest** | Android | Social | Partial | APKMirror | Hybrid RN + native |
| **Skype** | Android/iOS | Communication | Yes | APKMirror | Microsoft app, mature |
| **SoundCloud** | Android | Media | Yes | APKMirror | Media streaming |

### Test Matrix

For each app, execute:

#### Static Analysis
- [ ] `check_tools.py` / `check_tools_ios.py` passes
- [ ] `analyze_apk.py` / `analyze_ipa.py` completes without errors
- [ ] Hermes version correctly detected (`file` command verification)
- [ ] Bundle size handled (test with bundles >20MB)
- [ ] `detect_obfuscation.py` produces meaningful results
- [ ] `sourcemap_recovery.py` finds maps if present
- [ ] Secret scanner runs without false positive overload
- [ ] API endpoints extracted

#### Dynamic Analysis (where possible)
- [ ] App launches in emulator/simulator (or document why not)
- [ ] Frida attaches successfully
- [ ] SSL bypass works
- [ ] Root/jailbreak bypass works (if needed)
- [ ] `rn_bridge_trace.js` produces output
- [ ] Traffic capture works with mitmproxy addon
- [ ] `correlate_traffic.py` matches endpoints

### Success Criteria

- All scripts complete without crashes on 8/10 apps
- Hermes detection accuracy: 100%
- API endpoint extraction: >80% of manually verified endpoints
- Dynamic analysis: works on 6/10 apps (accounting for anti-tampering)

### Timeline

| Week | Tasks |
|------|-------|
| 1 | Test Discord, Shopify (high complexity) |
| 2 | Test Bloomberg, Coinbase (finance/security) |
| 3 | Test Walmart, Wix, Pinterest (variety) |
| 4 | Test Skype, SoundCloud, document findings |

### Deliverables

1. Test results spreadsheet with pass/fail per app/test
2. List of bugs/issues discovered
3. Updated scripts addressing discovered issues
4. Documentation updates for edge cases

---

## Part B: Minimal Hermes Test App

### Objective
Create a purpose-built React Native app with known secrets, endpoints, and security configurations for repeatable toolkit validation.

### App Specification

#### Core Features

```
HermesTestApp/
├── Intentional vulnerabilities:
│   ├── Hardcoded API keys (various formats)
│   ├── Hardcoded JWT tokens
│   ├── Cleartext HTTP endpoints
│   ├── Insecure storage usage
│   └── Debug logging with sensitive data
│
├── Security features to bypass:
│   ├── SSL pinning (TrustKit on iOS, OkHttp on Android)
│   ├── Root/jailbreak detection
│   ├── Certificate transparency
│   └── Debugger detection
│
├── API patterns:
│   ├── REST endpoints (GET, POST, PUT, DELETE)
│   ├── GraphQL endpoint
│   ├── WebSocket connection
│   └── File upload endpoint
│
├── Auth flows:
│   ├── Basic auth
│   ├── Bearer token
│   ├── OAuth2 flow
│   └── Session cookies
│
└── Native modules:
    ├── Keychain/Keystore usage
    ├── Biometric authentication
    ├── Crypto operations
    └── Clipboard access
```

#### Known Secrets (for validation)

```javascript
// These MUST be detected by the toolkit
const KNOWN_SECRETS = {
  // API Keys
  API_KEY_1: "sk_test_51ABC123XYZ789DEF456GHI",
  API_KEY_2: "api_key_hermestest_abc123def456",

  // AWS (fake but realistic format)
  AWS_ACCESS_KEY: "AKIAIOSFODNN7EXAMPLE",
  AWS_SECRET_KEY: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",

  // JWT (expired, safe to include)
  JWT_TOKEN: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidGVzdCI6Imhlcm1lcyJ9.fake",

  // Firebase (fake project)
  FIREBASE_KEY: "AIzaSyA1B2C3D4E5F6G7H8I9J0-hermestest",

  // Generic
  PASSWORD_HASH: "5f4dcc3b5aa765d61d8327deb882cf99",
  PRIVATE_KEY_HEADER: "-----BEGIN RSA PRIVATE KEY-----",
};

// Known endpoints (for correlation testing)
const KNOWN_ENDPOINTS = {
  REST_API: "https://api.hermestest.local/v1/users",
  GRAPHQL: "https://api.hermestest.local/graphql",
  WEBSOCKET: "wss://api.hermestest.local/ws",
  INSECURE: "http://insecure.hermestest.local/data",
};
```

#### Build Configurations

1. **Debug build** - No obfuscation, source maps included
2. **Release build** - Metro minification only
3. **Obfuscated build** - javascript-obfuscator applied
4. **Hermes build** - Compiled to bytecode (default)

### Implementation Steps

1. **Initialize project**
   ```bash
   npx react-native init HermesTestApp --version 0.73
   cd HermesTestApp
   ```

2. **Add dependencies**
   ```bash
   npm install @react-native-async-storage/async-storage
   npm install react-native-keychain
   npm install react-native-ssl-pinning
   npm install @apollo/client graphql
   npm install react-native-root-detection  # For detection we'll bypass
   ```

3. **Implement features**
   - Create screens demonstrating each vulnerability
   - Add mock backend (can use json-server or MSW)
   - Implement all auth flows
   - Add security checks to bypass

4. **Build variants**
   ```bash
   # Debug (Android)
   cd android && ./gradlew assembleDebug

   # Release (Android)
   cd android && ./gradlew assembleRelease

   # iOS
   xcodebuild -workspace ios/HermesTestApp.xcworkspace \
     -scheme HermesTestApp -configuration Release \
     -archivePath build/HermesTestApp.xcarchive archive
   ```

5. **Generate all artifacts**
   - APK (debug + release)
   - IPA (if possible without paid dev account)
   - Extracted bundles for direct testing
   - Source maps for each build

### Validation Checklist

After building, verify toolkit detects:

- [ ] All 6 known secrets detected by `analyze_apk.py`
- [ ] All 4 known endpoints extracted
- [ ] Hermes bytecode version correct
- [ ] SSL pinning detected and bypassable
- [ ] Root detection detected and bypassable
- [ ] Keychain/Keystore operations traced
- [ ] GraphQL operations captured
- [ ] Source maps extracted from debug build
- [ ] Obfuscation correctly identified per build variant

### Repository Structure

```
hermes-test-app/
├── README.md           # Setup and usage instructions
├── KNOWN_SECRETS.md    # List of intentional secrets for validation
├── src/                # React Native source
├── android/            # Android project
├── ios/                # iOS project
├── builds/             # Pre-built artifacts
│   ├── debug/
│   │   ├── hermestest-debug.apk
│   │   └── index.android.bundle
│   ├── release/
│   │   ├── hermestest-release.apk
│   │   └── index.android.bundle
│   └── obfuscated/
│       └── hermestest-obfuscated.apk
└── validation/         # Expected outputs for comparison
    ├── expected_secrets.json
    ├── expected_endpoints.json
    └── expected_obfuscation.json
```

### Timeline

| Week | Tasks |
|------|-------|
| 1 | Initialize project, implement core features |
| 2 | Add security features, mock backend |
| 3 | Build all variants, generate artifacts |
| 4 | Validate toolkit, document results |

### Deliverables

1. GitHub repository with test app source
2. Pre-built APKs/IPAs for each configuration
3. Validation scripts comparing actual vs expected results
4. CI integration for automated validation

---

## Approval Required

This plan requires approval before implementation. Key decisions needed:

1. **App selection** - Confirm the 10 target apps or suggest alternatives
2. **Test app scope** - Full implementation vs MVP (fewer features)
3. **Timeline** - Adjust based on priority and availability
4. **Repository** - Where to host the test app (same repo vs separate)

Please review and provide feedback.
