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
| Joplin | ✅ v96 | 28MB | 100 | **RSA PRIVATE KEY** | 0 |
| Rocket.Chat | ✅ v96 | 11MB | 98 | **JWT token** | 4 (isRooted) |
| Streamyfin | ✅ v96 | 6.3MB | 44 | 0 | 2 (isRooted) |
| Expensify | ✅ v96 | 26MB | 100 | **Firebase key, PRIVATE KEY** | 1 |
| Mattermost iOS | ✅ v96 | 27MB | 26 | SendGrid prefix | 3 (isRooted, xposed) |

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
**Status:** ⚠️ Pass with Findings

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 28MB (large)
- [x] Endpoints found: 100
- [x] Secrets found: **RSA PRIVATE KEY header**
- [x] Enhanced scan: 66 findings

#### Key Findings
- **RSA PRIVATE KEY header detected** - likely test/example key
- Large bundle handled correctly
- Popular note-taking app

#### Potential Security Issue
- Private key header in bundle needs investigation
- May be sample/test key for documentation

---

### Rocket.Chat (4.69.0) - 141MB

**Tested:** 2026-02-05
**Status:** ⚠️ Pass with Findings

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 11MB
- [x] Endpoints found: 98
- [x] Secrets found: **JWT token**
- [x] Enhanced scan: 50 findings
- [x] Anti-tampering: 4 indicators (isRooted)

#### Key Findings
- **JWT token detected** in bundle (eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...)
- Root detection implemented
- Enterprise chat platform

#### Potential Security Issue
- JWT token in bundle - may be example/placeholder

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
**Status:** ⚠️ Pass with Findings

#### Static Analysis
- [x] analyze_apk.py completed without errors
- [x] Hermes version correctly detected: v96 (RN 0.73+)
- [x] Bundle size: 26MB (large)
- [x] Endpoints found: 100
- [x] Secrets found: **Firebase key, PRIVATE KEY header, SendGrid reference**
- [x] Enhanced scan: 118 findings (highest)

#### Key Findings
- **Firebase API key detected**: AIzaSyBrLKgCuo6Vem6Xi5RPokdumssW8HaWBow
- **PRIVATE KEY header** in bundle
- **SendGrid key reference**
- Staging build may have more exposed than production

#### Potential Security Issues
- Firebase key should be verified if restricted
- Private key header needs investigation
- This is a staging build - production may differ

---

### Mattermost iOS (2.36.4) - 40MB

**Tested:** 2026-02-05
**Status:** ⚠️ Partial (IPA structure issue)

#### Static Analysis
- [ ] analyze_ipa.py failed - unusual IPA structure
- [x] Manual extraction successful
- [x] Hermes version: v96 (RN 0.73+)
- [x] Bundle size: 27MB
- [x] Endpoints found: 26
- [x] Secrets found: SendGrid prefix ('SG.')
- [x] Enhanced scan: 50 findings (20 hashes)
- [x] Anti-tampering: 3 indicators (isRooted, verifySignature, xposed)

#### Key Findings
- IPA has non-standard structure (Mattermost.app/ at root instead of Payload/)
- Many MD5/SHA256 hashes in bundle
- Root and Xposed detection

#### Issues Encountered
- **analyze_ipa.py bug**: Doesn't handle IPAs without Payload/ directory
- Workaround: Manual extraction works

---

## Learnings and Improvements

### Issues Found

| Date | App | Issue | Severity | Status |
|------|-----|-------|----------|--------|
| 2026-02-05 | Mattermost iOS | IPA without Payload/ dir not handled | Medium | Open |
| 2026-02-05 | EteSync, Podverse | Apps with Hermes libs but plain JS bundles | Low | Known |
| 2026-02-05 | Joplin | RSA PRIVATE KEY in bundle | Medium | Investigate |
| 2026-02-05 | Rocket.Chat | JWT token in bundle | Medium | Investigate |
| 2026-02-05 | Expensify | Firebase key, Private key in staging | High | Report? |

### Improvements to Implement

| Date | Description | Priority | Status |
|------|-------------|----------|--------|
| 2026-02-05 | Handle IPAs without Payload/ directory | High | Open |
| 2026-02-05 | Distinguish "has Hermes libs" vs "uses Hermes bytecode" | Medium | Open |
| 2026-02-05 | Add severity levels to secret findings | Medium | Open |
| 2026-02-05 | Auto-classify test/example keys vs real secrets | Low | Open |

### Script Changes Made

| Date | Script | Change | Reason |
|------|--------|--------|--------|
| 2026-02-05 | analyze_ipa.py | Added --enhanced flag | Parity with Android |
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
| Apps passing cleanly | 9 |
| Apps with potential secrets | 4 |
| Apps with anti-tampering | 9 |
| Improvements identified | 4 |
| Improvements implemented | 0 |

---

## Key Observations

1. **Hermes adoption**: 10/12 Android apps use Hermes bytecode v96 (RN 0.73+)
2. **Plain JS surprise**: 2 apps (EteSync, Podverse) have Hermes libraries but plain JS bundles
3. **Anti-tampering common**: 9/13 apps implement some form of root/jailbreak detection
4. **Large bundles work**: 28MB Joplin and 26MB Expensify analyzed successfully
5. **Secrets found**: 4 apps have potential secrets requiring investigation
6. **iOS IPA edge case**: Non-standard IPA structure breaks analyzer

## Notes

- APKMirror blocks automated downloads - use GitHub releases or F-Droid instead
- iOS IPAs are rarely available - Mattermost is an exception
- Large bundles (>20MB) work fine with current implementation
- Some apps may require GMS bypass for dynamic analysis
- Staging builds (Expensify) may expose more than production
