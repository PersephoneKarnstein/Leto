# [APP_NAME] Security Analysis

## Application Info
- Package: com.example.app
- Version: X.X.X
- Platform: Android / iOS
- Framework: React Native with Hermes bytecode

### Android-Specific
- Min SDK: XX, Target SDK: XX

### iOS-Specific
- Deployment target: iOS XX
- Architecture: arm64 / arm64 + x86_64

## Analysis Status
- [ ] Package extracted and inspected
- [ ] Hermes bytecode analyzed
- [ ] Configuration files reviewed (Manifest/Info.plist)
- [ ] Secret/credential search (automated + manual triage)
- [ ] Network security analysis
- [ ] Native code analysis
- [ ] Exported/URL scheme handlers tested
- [ ] Traffic interception verified

---

## VULNERABILITY FINDINGS

### CRITICAL SEVERITY

#### 1. [FINDING TITLE]
**Location**: `path/to/file:line`

**Description**:
[What is vulnerable and why]

**Proof of Concept**:
```bash
# Commands to reproduce
```

**Impact**:
- [Impact 1]
- [Impact 2]

**CVSS 3.1**: X.X (CRITICAL/HIGH/MEDIUM/LOW)

**Remediation**:
```
// Fixed code example
```

---

### HIGH SEVERITY

#### 2. [FINDING TITLE]
...

---

### MEDIUM SEVERITY
...

---

### LOW SEVERITY
...

---

## POSITIVE SECURITY CONTROLS
- [Control 1]
- [Control 2]

---

## API ENDPOINTS DISCOVERED

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/endpoint1` | POST | Description |

---

## HARDCODED SECRETS

| Secret | Value | Risk | Verified? |
|--------|-------|------|-----------|
| API_KEY | `[REDACTED]` | HIGH/MEDIUM/LOW | Yes/False Positive |

**Note:** Automated scanners produce ~75% false positive rate on Hermes bundles. All findings above have been manually verified.

---

## RECOMMENDATIONS

### Critical Priority
1. [Recommendation]

### High Priority
2. [Recommendation]

### Medium Priority
3. [Recommendation]

---

## FILES ANALYZED
- AndroidManifest.xml / Info.plist
- Hermes bundle (index.android.bundle / main.jsbundle)
- [Other key files]

---

## TOOLS USED
- r2hermes / hermes-dec -- Hermes bytecode analysis
- jadx / JADX (Android) -- APK decompilation
- gitleaks + enhanced_secret_scan.py -- Secret scanning
- Burp Suite / mitmproxy -- Traffic interception
- Frida -- Runtime instrumentation

---

Analysis performed: [DATE]
Analyst: [NAME]
