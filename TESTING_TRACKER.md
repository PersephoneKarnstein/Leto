# Testing Tracker - Hermes Analysis Toolkit

This document tracks progress testing the toolkit against real-world React Native apps.

**Last Updated:** 2026-02-05

---

## Downloaded Test Apps

### Android APKs (12 apps, ~1.2GB total)

| App | Version | Size | Source | Hermes | Status |
|-----|---------|------|--------|--------|--------|
| Expensify | staging | 230MB | GitHub | Yes | Pending |
| Streamyfin | 0.51.0 | 177MB | GitHub | Yes | Pending |
| Rocket.Chat | 4.69.0 | 141MB | GitHub | Yes | Pending |
| Joplin | 3.5.9 | 121MB | F-Droid | Yes | Pending |
| Fintunes | 2.4.6 | 121MB | GitHub | Yes | Pending |
| Standard Notes | 3.201.4 | 85MB | F-Droid | Yes | Pending |
| Mattermost | 2.36.4 | 75MB | GitHub | Yes | Pending |
| BlueWallet | 7.2.3 | 68MB | GitHub | Yes | Pending |
| Podverse | 4.16.3 | 46MB | F-Droid | Yes | Pending |
| Jellify | 1.0.15 | 41MB | GitHub | Yes | Pending |
| Notesnook | arm64 | 35MB | GitHub | Yes | Pending |
| EteSync Notes | 1.7.0 | 27MB | F-Droid | Yes | Pending |

### iOS IPAs (1 app)

| App | Version | Size | Source | Hermes | Status |
|-----|---------|------|--------|--------|--------|
| Mattermost | 2.36.4 | 40MB | GitHub | Yes | Pending |

**Note:** iOS IPAs are rarely published publicly. Most apps only distribute via App Store.

---

## Test Matrix

For each app, track results of:

### Static Analysis Tests

| Test | Script/Command | Notes |
|------|----------------|-------|
| Tool check | `check_tools.py` | Verify all tools available |
| APK/IPA analysis | `analyze_apk.py --enhanced` | Full automated analysis |
| Hermes version | `file bundle` | Verify correct detection |
| Bundle size handling | - | Test with >20MB bundles |
| Obfuscation detection | `detect_obfuscation.py` | Identify obfuscation techniques |
| Secret scanning | `enhanced_secret_scan.py` | Check for obfuscated secrets |
| API endpoint extraction | - | Count endpoints found |

### Dynamic Analysis Tests (where possible)

| Test | Script/Command | Notes |
|------|----------------|-------|
| App launches | Emulator/device | Document GMS issues |
| Frida attaches | `frida -U -f ...` | Test connection |
| SSL bypass | `universal_ssl_bypass.js` | Verify bypass works |
| Root bypass | `root_bypass.js` | If needed |
| RN bridge trace | `rn_bridge_trace.js` | Capture bridge calls |

---

## Detailed Test Results

### Template for Each App

```markdown
## [App Name] - [Version]

**Tested:** YYYY-MM-DD
**Status:** Pass / Partial / Fail

### Static Analysis
- [ ] analyze_apk.py completed without errors
- [ ] Hermes version correctly detected: vXX
- [ ] Bundle size: XXX MB
- [ ] Endpoints found: XX
- [ ] Secrets/interesting strings: XX
- [ ] Enhanced scan findings: XX

### Findings
- Finding 1
- Finding 2

### Issues Encountered
- Issue 1 (and workaround if any)

### Improvements Identified
- Improvement 1
```

---

## Test Results by App

### Expensify (staging) - 230MB

**Tested:** Not yet
**Status:** Pending

---

### Streamyfin (0.51.0) - 177MB

**Tested:** Not yet
**Status:** Pending

---

### Rocket.Chat (4.69.0) - 141MB

**Tested:** Not yet
**Status:** Pending

---

### Joplin (3.5.9) - 121MB

**Tested:** Not yet
**Status:** Pending

---

### Fintunes (2.4.6) - 121MB

**Tested:** Not yet
**Status:** Pending

---

### Standard Notes (3.201.4) - 85MB

**Tested:** Not yet
**Status:** Pending

---

### Mattermost Android (2.36.4) - 75MB

**Tested:** Not yet
**Status:** Pending

---

### BlueWallet (7.2.3) - 68MB

**Tested:** Not yet
**Status:** Pending

---

### Podverse (4.16.3) - 46MB

**Tested:** Not yet
**Status:** Pending

---

### Jellify (1.0.15) - 41MB

**Tested:** Not yet
**Status:** Pending

---

### Notesnook (arm64) - 35MB

**Tested:** Not yet
**Status:** Pending

---

### EteSync Notes (1.7.0) - 27MB

**Tested:** Not yet
**Status:** Pending

---

### Mattermost iOS (2.36.4) - 40MB

**Tested:** Not yet
**Status:** Pending

---

## Learnings and Improvements

Track issues found during testing and improvements to implement.

### Issues Found

| Date | App | Issue | Severity | Status |
|------|-----|-------|----------|--------|
| | | | | |

### Improvements to Implement

| Date | Description | Priority | Status |
|------|-------------|----------|--------|
| | | | |

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
| Apps tested | 0 |
| Apps passing | 0 |
| Apps with issues | 0 |
| Improvements identified | 0 |
| Improvements implemented | 0 |

---

## Notes

- APKMirror blocks automated downloads - use GitHub releases or F-Droid instead
- iOS IPAs are rarely available - Mattermost is an exception
- Large bundles (>100MB) may cause r2hermes issues - use strings command instead
- Some apps may require GMS bypass for dynamic analysis
