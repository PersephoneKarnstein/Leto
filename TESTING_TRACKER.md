# Testing Tracker - Hermes Analysis Toolkit

This document tracks progress testing the toolkit against real-world React Native apps.

**Last Updated:** 2026-02-05

---

## Downloaded Test Apps

### Android APKs (12 apps, ~1.2GB total)

| App | Version | Size | Source | Hermes | Status |
|-----|---------|------|--------|--------|--------|
| Expensify | staging | 230MB | GitHub | **Yes (v96)** | ✅ Tested |
| Streamyfin | 0.51.0 | 177MB | GitHub | **Yes (v96)** | ✅ Tested |
| Rocket.Chat | 4.69.0 | 141MB | GitHub | **Yes (v96)** | ✅ Tested |
| Joplin | 3.5.9 | 121MB | F-Droid | **Yes (v96)** | ✅ Tested |
| Fintunes | 2.4.6 | 121MB | GitHub | **Yes (v96)** | ✅ Tested |
| Standard Notes | 3.201.4 | 85MB | F-Droid | **Yes (v96)** | ✅ Tested |
| Mattermost | 2.36.4 | 75MB | GitHub | **Yes (v96)** | ✅ Tested |
| BlueWallet | 7.2.3 | 68MB | GitHub | **Yes (v96)** | ✅ Tested |
| Podverse | 4.16.3 | 46MB | F-Droid | **No (Plain JS)** | ✅ Tested |
| Jellify | 1.0.15 | 41MB | GitHub | **Yes (v96)** | ✅ Tested |
| Notesnook | arm64 | 35MB | GitHub | **Yes (v96)** | ✅ Tested |
| EteSync Notes | 1.7.0 | 27MB | F-Droid | **No (Plain JS)** | ✅ Tested |

### iOS IPAs (1 app)

| App | Version | Size | Source | Hermes | Status |
|-----|---------|------|--------|--------|--------|
| Mattermost | 2.36.4 | 40MB | GitHub | **Yes (v96)** | ✅ Tested |

**Note:** iOS IPAs are rarely published publicly. Most apps only distribute via App Store.

---

## Test Results Summary

| App | Hermes | Bundle Size | Endpoints | Secrets Found | Anti-Tamper |
|-----|--------|-------------|-----------|---------------|-------------|
| EteSync Notes | ❌ Plain JS | 2.8MB | 81 | AWS key (potential) | 0 |
| Notesnook | ✅ v96 | 9.7MB | 100 | 0 | 2 |
| Jellify | ✅ v96 | 6.2MB | 38 | Sentry DSN | 1 |
| Podverse | ❌ Plain JS | 7.2MB | 100 | 0 | 1 |
| BlueWallet | ✅ v96 | 8.4MB | 100 | 0 | 4 |
| Mattermost Android | ✅ v96 | 21MB | 75 | 0 | 3 (isRooted) |
| Standard Notes | ✅ v96 | 2.2MB | 17 | 0 | 3 (checkIntegrity) |
| Fintunes | ✅ v96 | 4.3MB | 40 | 0 | 0 |
| Joplin | ✅ v96 | 28MB | 100 | ~~RSA PRIVATE KEY~~ (PUBLIC) | 0 |
| Rocket.Chat | ✅ v96 | 11MB | 98 | ~~JWT token~~ (version manifest) | 4 (isRooted) |
| Streamyfin | ✅ v96 | 6.3MB | 44 | 0 | 2 (isRooted) |
| Expensify | ✅ v96 | 26MB | 100 | ⚠️ **Firebase key, RSA PRIVATE KEY** | 1 |
| Mattermost iOS | ✅ v96 | 27MB | 26 | ~~SendGrid prefix~~ (bytecode noise) | 3 (jailbreak, xposed) |

---

## Detailed Test Results

### EteSync Notes (1.7.0) - 27MB

**Tested:** 2026-02-05
**Status:** ✅ Pass (with findings)

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version: **NOT Hermes** (Plain JavaScript/ASCII text)
- [x] Bundle size: 2.8MB
- [x] Endpoints found: 81
- [x] Secrets found: Potential AWS key (AKIANBIBAKIAULJAALBA)
- [x] Enhanced scan: 94 findings (2 Base64, 3 hex)

#### Key Findings
- **NOT using Hermes bytecode** despite having libhermes libraries
- Potential AWS key detected - requires manual verification
- App has Hermes executor libraries but JS bundle is plain text

#### Issues Encountered
- None - script handled plain JS bundle correctly

---

### Notesnook (arm64) - 35MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 9.7MB
- [x] Endpoints found: 100
- [x] Secrets found: 0
- [x] Enhanced scan: 46 findings
- [x] Anti-tampering: 2 indicators

#### Key Findings
- Clean encrypted notes app
- No hardcoded secrets detected
- Standard React Native anti-tampering

---

### Jellify (1.0.15) - 41MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 6.2MB
- [x] Endpoints found: 38
- [x] Secrets found: Sentry DSN (o447951.ingest.sentry.io)
- [x] Enhanced scan: 22 findings

#### Key Findings
- Sentry error tracking DSN exposed (common, low risk)
- Jellyfin music client

---

### Podverse (4.16.3) - 46MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version: **NOT Hermes** (Plain JavaScript)
- [x] Bundle size: 7.2MB
- [x] Endpoints found: 100
- [x] Secrets found: 0
- [x] Enhanced scan: 79 findings (2 hex decoded)

#### Key Findings
- **NOT using Hermes bytecode** despite having libhermes libraries
- Similar to EteSync - has Hermes executor but plain JS bundle

---

### BlueWallet (7.2.3) - 68MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 8.4MB
- [x] Endpoints found: 100
- [x] Secrets found: 0
- [x] Enhanced scan: 53 findings
- [x] Anti-tampering: 4 indicators

#### Key Findings
- Bitcoin wallet with strong security posture
- 4 anti-tampering indicators (highest among tested apps)
- No hardcoded secrets (as expected for crypto wallet)

---

### Mattermost Android (2.36.4) - 75MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 21MB (large)
- [x] Endpoints found: 75
- [x] Secrets found: 0
- [x] Enhanced scan: 53 findings
- [x] Anti-tampering: 3 indicators (isRooted)

#### Key Findings
- Root detection implemented
- Large bundle handled correctly
- Enterprise collaboration app with good security

---

### Standard Notes (3.201.4) - 85MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 2.2MB (smallest Hermes bundle)
- [x] Endpoints found: 17
- [x] Secrets found: 0
- [x] Enhanced scan: 11 findings
- [x] Anti-tampering: 3 indicators (checkIntegrity)

#### Key Findings
- Encrypted notes app with integrity checking
- Smallest Hermes bundle tested
- Clean security posture

---

### Fintunes (2.4.6) - 121MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 4.3MB
- [x] Endpoints found: 40
- [x] Secrets found: 0
- [x] Enhanced scan: 19 findings
- [x] Anti-tampering: 0 indicators

#### Key Findings
- Jellyfin audio player
- No anti-tampering code
- Clean bundle

---

### Joplin (3.5.9) - 121MB

**Tested:** 2026-02-05
**Status:** ✅ Pass (FALSE POSITIVE corrected)

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 28MB (large)
- [x] Endpoints found: 100
- [x] Secrets found: **NONE** (false positive corrected)
- [x] Enhanced scan: 66 findings

#### Deep Analysis Findings
- **FALSE POSITIVE CORRECTED**: Scanner detected "RSA" pattern but full context shows "RSA PUBLIC KEY" (not private)
- Contains RSA public keys for signature verification (safe to embed)
- Large bundle handled correctly
- Popular note-taking app with good security practices

#### Security Assessment
- ✅ No actual secrets exposed
- ✅ Only public keys in bundle (expected for crypto operations)

---

### Rocket.Chat (4.69.0) - 141MB

**Tested:** 2026-02-05
**Status:** ✅ Pass (JWT analyzed - not sensitive)

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 11MB
- [x] Endpoints found: 98
- [x] Secrets found: **NONE** (JWT is version manifest, not auth token)
- [x] Enhanced scan: 50 findings
- [x] Anti-tampering: 4 indicators (isRooted)

#### Deep Analysis Findings
- **JWT ANALYZED**: The embedded JWT is a **version compatibility manifest** signed by Rocket.Chat
- JWT payload contains: `timestamp`, `messages`, `versions` (list of supported server versions with expiration dates)
- This is a **client-side version checking mechanism**, NOT an authentication token
- Root detection implemented with 4 indicators
- Enterprise chat platform with good security

#### Security Assessment
- ✅ No auth secrets exposed
- ✅ JWT serves legitimate purpose (version compatibility checking)
- ✅ Strong anti-tampering with root detection

---

### Streamyfin (0.51.0) - 177MB

**Tested:** 2026-02-05
**Status:** ✅ Pass

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 6.3MB
- [x] Endpoints found: 44
- [x] Secrets found: 0
- [x] Enhanced scan: 30 findings
- [x] Anti-tampering: 2 indicators (isRooted)

#### Key Findings
- Jellyfin client
- Root detection implemented
- Clean bundle despite large APK (media libraries)

---

### Expensify (staging) - 230MB

**Tested:** 2026-02-05
**Status:** ⚠️ CONFIRMED SECRETS (staging build)

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 26MB (large)
- [x] Endpoints found: 100
- [x] Secrets found: **Firebase key (CONFIRMED), RSA PRIVATE KEY (CONFIRMED)**
- [x] Enhanced scan: 118 findings (highest)

#### Deep Analysis Findings
- **CONFIRMED Firebase API key**: `AIzaSyBrLKgCuo6Vem6Xi5RPokdumssW8HaWBow`
  - This is a real Firebase key for the staging environment
  - Used for Firebase Cloud Messaging (FCM) and likely other Firebase services
  - Should be restricted by API key restrictions in Firebase console
- **CONFIRMED RSA PRIVATE KEY**: Full PEM-encoded private key found in bundle
  - 2048-bit RSA private key with complete structure
  - Located in bundle at multiple positions
  - Purpose unclear but represents significant exposure
- **SendGrid reference** found but not a complete key

#### Security Assessment
- ⚠️ **HIGH RISK**: Real Firebase API key exposed
- ⚠️ **HIGH RISK**: Complete RSA private key embedded
- This is a **staging build** - production builds should be verified separately
- Recommend: Report to Expensify security team

#### Recommendations
1. Firebase key should have API restrictions configured
2. RSA private key should be removed from client bundle
3. Production build should be analyzed for comparison

---

### Mattermost iOS (2.36.4) - 40MB

**Tested:** 2026-02-05
**Status:** ✅ Pass (comprehensive deep analysis completed)

#### Static Analysis
- [x] analyze_ipa.py completed (after fix for non-standard IPA structure)
- [x] Hermes version: v96 (RN 0.73+)
- [x] Bundle size: 27MB
- [x] Endpoints found: 26
- [x] Secrets found: **NONE** (SG. was false positive in bytecode noise)
- [x] Enhanced scan: 50 findings (20 hashes - asset identifiers)
- [x] Anti-tampering: 3 indicators (isRooted, verifySignature, xposed)

#### Deep Analysis Findings

**Jailbreak Detection (Native Binary)**:
- Explicit path checks implemented:
  - `/Applications/Cydia.app`
  - `/Library/MobileSubstrate/DynamicLibraries/LiveClock.plist`
  - `/Library/MobileSubstrate/DynamicLibraries/Veency.plist`
  - `/Library/MobileSubstrate/MobileSubstrate.dylib`
  - `/private/var/lib/cydia`
  - `/private/var/tmp/cydia.log`
  - `/System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist`

**SSL Pinning**:
- Alamofire `PinnedCertificatesTrustEvaluator`
- Starscream `CertificatePinning` (WebSocket)
- Certificate chain validation enabled

**Microsoft Intune MDM Integration**:
- Full IntuneMAMSwift.framework integration
- Azure AD authentication (MSAL)
- Policy enforcement: encryption, wipe, compliance checks
- File protection level: `NSFileProtectionCompleteUntilFirstUserAuthentication`

**WebRTC Security** (Calls):
- DTLS for secure key exchange
- SRTP encryption for media
- AES-128-SHA1 and GCM cipher suites
- Encrypted RTP header extensions

**App Transport Security**:
- `NSAllowsArbitraryLoads = true` (allows HTTP)
- Only localhost has explicit HTTP exception
- No insecure HTTP API endpoints found in codebase

**Share Extension**:
- Separate Sentry DSN (empty/disabled)
- Supports up to 10 attachments
- Uses App Groups for secure data sharing

**MD5/SHA256 Hashes**:
- Confirmed as **asset/font identifiers**, not secrets
- Used for internal caching and integrity

#### Security Assessment
- ✅ Enterprise-grade security posture
- ✅ Comprehensive jailbreak detection
- ✅ SSL pinning on network layer
- ✅ MDM policy enforcement
- ✅ No hardcoded secrets
- ✅ Secure WebRTC implementation for calls

#### Issues Encountered (Now Fixed)
- **analyze_ipa.py bug fixed**: Now handles IPAs without Payload/ directory

---

## Deep Analysis Results

The following apps received comprehensive manual deep analysis beyond automated scanning:

### 1. Expensify (staging) - ⚠️ CONFIRMED SECRETS

**Firebase API Key**: `AIzaSyBrLKgCuo6Vem6Xi5RPokdumssW8HaWBow`
- Real Firebase key for staging environment
- Used for FCM and Firebase services
- Should have API restrictions configured

**RSA Private Key**: Complete 2048-bit PEM-encoded private key
- Full private key structure in bundle
- Significant security exposure
- Purpose unclear, but should not be in client

**Recommendation**: Consider responsible disclosure to Expensify security team.

---

### 2. Joplin - ✅ FALSE POSITIVE

**Initial Finding**: "RSA PRIVATE KEY" pattern detected
**Actual Finding**: RSA **PUBLIC** keys only
- Scanner matched "RSA" but full context shows public keys
- Used for signature verification (expected)
- No private key material exposed

---

### 3. Rocket.Chat - ✅ NOT SENSITIVE

**Initial Finding**: JWT token detected
**Actual Finding**: Version compatibility manifest
- JWT signed by Rocket.Chat contains version info
- Payload: `timestamp`, `messages`, `versions` with expiration dates
- Used for client-side version checking
- NOT an authentication token

---

### 4. Mattermost iOS - ✅ ENTERPRISE SECURITY

**Initial Finding**: SendGrid prefix, multiple hashes
**Actual Finding**: All false positives

**Security Features Discovered**:
- **Jailbreak Detection**: 7 explicit path checks for Cydia, MobileSubstrate, etc.
- **SSL Pinning**: Alamofire + Starscream certificate pinning
- **MDM Integration**: Full Microsoft Intune with policy enforcement
- **WebRTC Security**: DTLS + SRTP with AES-GCM
- **Share Extension**: Isolated with App Groups

**Hashes**: Asset identifiers for fonts/icons, not secrets.

---

## Learnings and Improvements

### Issues Found

| Date | App | Issue | Severity | Status |
|------|-----|-------|----------|--------|
| 2026-02-05 | Mattermost iOS | IPA without Payload/ dir not handled | Medium | ✅ Fixed |
| 2026-02-05 | EteSync, Podverse | Apps with Hermes libs but plain JS bundles | Low | Known |
| 2026-02-05 | Joplin | RSA PRIVATE KEY in bundle | Medium | ✅ False Positive (PUBLIC key) |
| 2026-02-05 | Rocket.Chat | JWT token in bundle | Medium | ✅ Analyzed (version manifest) |
| 2026-02-05 | Expensify | Firebase key, Private key in staging | High | ⚠️ CONFIRMED - Consider report |

### Improvements to Implement

| Date | Description | Priority | Status |
|------|-------------|----------|--------|
| 2026-02-05 | Handle IPAs without Payload/ directory | High | ✅ Implemented |
| 2026-02-05 | Distinguish "has Hermes libs" vs "uses Hermes bytecode" | Medium | Open |
| 2026-02-05 | Add severity levels to secret findings | Medium | Open |
| 2026-02-05 | Auto-classify test/example keys vs real secrets | Low | Open |
| 2026-02-05 | Improve RSA key detection (distinguish PUBLIC vs PRIVATE) | Medium | Open |
| 2026-02-05 | Add JWT payload analysis for context | Low | Open |

### Script Changes Made

| Date | Script | Change | Reason |
|------|--------|--------|--------|
| 2026-02-05 | analyze_ipa.py | Added --enhanced flag | Parity with Android |
| 2026-02-05 | analyze_ipa.py | Fixed IPA extraction for non-standard structures | Mattermost iOS edge case |
| 2026-02-05 | SKILL-ios.md | Added obfuscation/anti-tamper sections | Learnings from test app |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total apps downloaded | 13 |
| Android APKs | 12 |
| iOS IPAs | 1 |
| **Apps tested** | **13** |
| Apps with Hermes bytecode | 10 (77%) |
| Apps with plain JS (has libs) | 2 |
| Apps passing cleanly | 11 |
| Apps with CONFIRMED secrets | 1 (Expensify staging) |
| False positives identified | 3 (Joplin, Rocket.Chat, Mattermost iOS) |
| Apps with anti-tampering | 9 |
| Improvements identified | 6 |
| Improvements implemented | 1 |

---

## Key Observations

1. **Hermes adoption**: 10/12 Android apps use Hermes bytecode v96 (RN 0.73+)
2. **Plain JS surprise**: 2 apps (EteSync, Podverse) have Hermes libraries but plain JS bundles
3. **Anti-tampering common**: 9/13 apps implement some form of root/jailbreak detection
4. **Large bundles work**: 28MB Joplin and 26MB Expensify analyzed successfully
5. **False positive rate**: 3/4 initial "secrets" were false positives after deep analysis
6. **iOS IPA edge case**: Non-standard IPA structure - now fixed in analyzer
7. **Enterprise security**: Mattermost iOS has enterprise-grade MDM, SSL pinning, and jailbreak detection

## Deep Analysis Learnings

### False Positive Patterns
- **RSA keys**: Always verify PUBLIC vs PRIVATE - "RSA" pattern alone is insufficient
- **JWT tokens**: Decode payload to determine purpose (auth vs version manifest vs config)
- **Hash-like strings**: MD5/SHA256 patterns often asset identifiers, not secrets
- **Bytecode noise**: Hermes string table can contain partial matches (e.g., "SG.")

### Real Secret Indicators
- Firebase keys (`AIza...`) - likely real but check API restrictions
- Complete PEM-encoded private keys with full structure
- API keys with recognizable vendor prefixes AND valid format

### Enterprise App Security Patterns (Mattermost iOS)
- Multiple layers of jailbreak detection (path checks, library checks)
- SSL pinning via Alamofire/Starscream
- MDM integration (Microsoft Intune)
- WebRTC with DTLS/SRTP for secure calls
- App Groups for secure extension communication

## Notes

- APKMirror blocks automated downloads - use GitHub releases or F-Droid instead
- iOS IPAs are rarely available - Mattermost is an exception
- Large bundles (>20MB) work fine with current implementation
- Some apps may require GMS bypass for dynamic analysis
- Staging builds (Expensify) may expose more than production
- **Deep analysis is essential** - 75% of initial "secrets" were false positives
