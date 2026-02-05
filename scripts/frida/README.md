# Frida Scripts for Hermes/React Native Analysis

This directory contains Frida scripts for dynamic analysis of React Native and Hermes-based Android and iOS applications.

## Scripts Overview

### Android Scripts

| Script | Purpose |
|--------|---------|
| `universal_ssl_bypass.js` | Comprehensive SSL/TLS pinning bypass (40+ methods) |
| `root_bypass.js` | Root detection and emulator detection bypass |
| `gms_firebase_bypass.js` | Google Play Services and Firebase bypass |
| `detect_frameworks.js` | Detect frameworks, libraries, and SDKs |
| `hermes_hooks.js` | React Native bridge and network hooks |
| `ssl_bypass.js` | Basic SSL pinning bypass (original) |

### iOS Scripts

| Script | Purpose |
|--------|---------|
| `ios_ssl_bypass.js` | iOS SSL pinning bypass (TrustKit, AFNetworking, SecTrust) |
| `ios_jailbreak_bypass.js` | iOS jailbreak detection bypass |

## Usage

### Basic Usage

```bash
# Spawn app with script
frida -U -f com.example.app -l universal_ssl_bypass.js

# Attach to running app
frida -U -n "App Name" -l root_bypass.js

# Load multiple scripts
frida -U -f com.example.app -l universal_ssl_bypass.js -l root_bypass.js
```

### Combined Bypass (SSL + Root + GMS)

```bash
# Create a combined script
cat universal_ssl_bypass.js root_bypass.js gms_firebase_bypass.js > /tmp/all_bypass.js
frida -U -f com.example.app -l /tmp/all_bypass.js
```

### Framework Detection

```bash
# Identify what the app uses
frida -U -f com.example.app -l detect_frameworks.js
```

## Script Details

### universal_ssl_bypass.js

Bypasses SSL certificate pinning for:
- OkHttp3 (all overloads including Kotlin)
- TrustManager (Android < 7 and > 7)
- Conscrypt TrustManagerImpl
- TrustKit
- Appcelerator Titanium
- Fabric
- Apache HttpClient
- PhoneGap/Cordova
- Flutter pinning plugins
- React Native OkHttpClientProvider
- WebView SSL errors
- Network Security Config

Based on [frida-multiple-unpinning](https://codeshare.frida.re/@akabe1/frida-multiple-unpinning/).

### root_bypass.js

Bypasses root/emulator detection:
- Package checks (Magisk, SuperSU, Xposed, etc.)
- Binary checks (su, busybox)
- System property checks (ro.debuggable, ro.secure)
- Build tag checks (test-keys)
- Native fopen/access hooks
- Runtime.exec and ProcessBuilder
- TelephonyManager (IMEI, IMSI spoofing)

Based on [fridantiroot](https://codeshare.frida.re/@dzonerzy/fridantiroot/).

### gms_firebase_bypass.js

For apps that require GMS but testing on emulators without Play Services:
- GoogleApiAvailability.isGooglePlayServicesAvailable → SUCCESS
- Firebase Messaging token generation bypass
- SyncTask.maybeRefreshToken blocking bypass
- Firebase Analytics stubbing
- GMS Tasks.await timeout handling

**Note**: This provides stub returns. Full functionality requires actual GMS or MicroG.

### detect_frameworks.js

Detects:
- **Frameworks**: React Native, Hermes, Flutter, Xamarin, Cordova, Unity
- **Networking**: OkHttp, Retrofit, Volley, Apollo GraphQL
- **Analytics**: Firebase, Google Analytics, Facebook SDK, Mixpanel, Amplitude, Segment
- **Security**: TrustKit, RootBeer, SafetyNet, Play Integrity, DexGuard
- **Storage**: Room, Realm, SQLCipher, EncryptedSharedPreferences

## Troubleshooting

### Script doesn't work

1. Check if the app uses obfuscation (ProGuard/R8)
2. Try attaching vs spawning
3. Check Frida version compatibility
4. Use `detect_frameworks.js` to identify what libraries are actually present

### App crashes on startup

1. The app may have anti-tampering checks
2. Try loading scripts after the app starts:
   ```bash
   frida -U -n "App Name" -l script.js
   ```

### SSL bypass not working

1. The app may use a custom pinning implementation
2. Try hooking specific classes:
   ```javascript
   Java.perform(function() {
       Java.enumerateLoadedClasses({
           onMatch: function(className) {
               if (className.toLowerCase().includes('pin') ||
                   className.toLowerCase().includes('cert') ||
                   className.toLowerCase().includes('ssl')) {
                   console.log(className);
               }
           },
           onComplete: function() {}
       });
   });
   ```

## iOS Usage

### Jailbroken Device

```bash
# Install Frida on jailbroken device via Sileo/Cydia
# Add repo: https://build.frida.re/

# Connect from computer
frida -U -f com.example.app -l ios_ssl_bypass.js

# Combined iOS bypass
frida -U -f com.example.app -l ios_ssl_bypass.js -l ios_jailbreak_bypass.js
```

### Non-Jailbroken (Gadget Injection)

```bash
# Use objection to patch IPA
objection patchipa --source app.ipa --codesign-signature "Your Cert"

# Install patched IPA and connect
objection -g "App Name" explore
```

### ios_ssl_bypass.js

Bypasses iOS SSL certificate pinning for:
- TrustKit (TSKPinningValidator)
- AFNetworking (AFSecurityPolicy)
- NSURLSession delegates
- SecTrustEvaluate/SecTrustEvaluateWithError
- OpenSSL direct usage

### ios_jailbreak_bypass.js

Bypasses iOS jailbreak detection:
- NSFileManager file existence checks
- UIApplication canOpenURL (cydia://, sileo://)
- stat/lstat/access/fopen hooks
- fork() sandbox escape check
- dyld library enumeration

## Sources

These scripts are based on popular scripts from [Frida CodeShare](https://codeshare.frida.re/):

- [frida-multiple-unpinning](https://codeshare.frida.re/@akabe1/frida-multiple-unpinning/) by @akabe1
- [fridantiroot](https://codeshare.frida.re/@dzonerzy/fridantiroot/) by @dzonerzy
- [Universal Android SSL Pinning Bypass](https://codeshare.frida.re/@pcipolloni/universal-android-ssl-pinning-bypass-with-frida/) by @pcipolloni
- [iOS Jailbreak Detection Bypass](https://codeshare.frida.re/@DevTraleski/ios-jailbreak-detection-bypass-palera1n/) by @DevTraleski
- [iOS Pinning Disable](https://codeshare.frida.re/@snooze6/ios-pinning-disable/) by @snooze6

## License

Scripts are provided for authorized security testing only. Use responsibly.
