# [APP_NAME] Security Analysis

## Application Info
- Package: com.example.app
- Version: X.X.X
- Min SDK: XX, Target SDK: XX
- Framework: React Native with Hermes bytecode

## Analysis Status
- [ ] AndroidManifest.xml reviewed
- [ ] JADX decompiled sources analyzed
- [ ] Hermes bytecode analyzed
- [ ] Secrets/credentials search
- [ ] Network security analysis
- [ ] Native libraries analysis
- [ ] Exported components tested
- [ ] Traffic interception verified

---

## VULNERABILITY FINDINGS

### CRITICAL SEVERITY

#### 1. [FINDING TITLE]
**Location**: `path/to/file.java:line`

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
```java
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

| Secret | Value | Risk |
|--------|-------|------|
| API_KEY | `[REDACTED]` | HIGH/MEDIUM/LOW |

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
- AndroidManifest.xml
- BuildConfig.java
- [Other key files]

---

## TOOLS USED
- JADX - APK decompilation
- r2hermes - Hermes bytecode analysis
- Burp Suite - Traffic interception
- Frida - Runtime instrumentation

---

Analysis performed: [DATE]
Analyst: [NAME]
