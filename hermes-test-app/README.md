# Hermes Test App

A purpose-built React Native application for validating the Lêtô Hermes analysis toolkit.

**DO NOT USE IN PRODUCTION** - This app contains intentional vulnerabilities.

## Purpose

This app includes:
- Hardcoded API keys, AWS credentials, JWT tokens
- Known API endpoints (REST, GraphQL, WebSocket)
- Insecure HTTP endpoints
- Debug configuration exposed

All secrets are fake but formatted realistically to test detection.

## Building

### Prerequisites
- Node.js 18+
- Android SDK (for Android builds)
- Xcode (for iOS builds)

### Android

```bash
cd hermes-test-app
npm install
cd android
./gradlew assembleRelease
```

APK output: `android/app/build/outputs/apk/release/app-release.apk`

### iOS

```bash
cd hermes-test-app
npm install
cd ios
pod install
xcodebuild -workspace HermesTestApp.xcworkspace -scheme HermesTestApp -configuration Release
```

## Testing with Lêtô Toolkit

```bash
# Analyze the APK
python scripts/analyze_apk.py builds/hermestest-release.apk --decompile

# Verify Hermes version
file builds/hermestest-release_analysis/extracted/assets/index.android.bundle

# Search for secrets
strings builds/hermestest-release_analysis/extracted/assets/index.android.bundle | grep -iE 'AKIA|api_key|sk_test'

# Run obfuscation detection
python scripts/detect_obfuscation.py builds/hermestest-release.apk
```

## Expected Findings

See `EXPECTED_FINDINGS.json` for the complete list of secrets and endpoints that should be detected.

### Secrets (should detect)
- API Keys: `sk_test_51ABC123...`, `api_key_hermestest_abc123def456ghi789`
- AWS: `AKIAIOSFODNN7EXAMPLE`
- Firebase: `AIzaSyA1B2C3D4E5F6G7H8I9J0-hermestest`
- JWT tokens (2)
- Database URLs (PostgreSQL, MongoDB, Redis)
- Private key header

### Endpoints (should detect)
- REST: `https://api.hermestest.local/v1/auth/login` etc.
- GraphQL: `https://api.hermestest.local/graphql`
- WebSocket: `wss://ws.hermestest.local/chat`
- Insecure: `http://insecure.hermestest.local/legacy/data`

## Files

```
hermes-test-app/
├── src/
│   ├── config/
│   │   ├── secrets.ts      # Intentional secrets
│   │   └── endpoints.ts    # API endpoints
│   └── services/
│       └── api.ts          # API client
├── App.tsx                 # Main app component
├── EXPECTED_FINDINGS.json  # Validation checklist
├── builds/                 # Built artifacts
│   └── hermestest-release.apk
└── README.md
```

## Notes

- Hermes is enabled by default (React Native 0.73)
- Bundle compiles to bytecode version 96
- No obfuscation applied (release build with standard Metro bundling)
