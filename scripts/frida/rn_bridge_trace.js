/*
 * React Native Bridge Tracer
 *
 * Hooks the React Native bridge to trace native module calls,
 * track data flow between JS and native, and detect sensitive operations.
 *
 * Usage:
 *   frida -U -f com.target.app -l rn_bridge_trace.js
 *   frida -U -f com.target.app -l rn_bridge_trace.js --no-pause
 *
 * Configuration (edit below):
 *   TRACE_ALL: Log all bridge calls (verbose)
 *   TRACE_SENSITIVE: Only log sensitive modules
 *   LOG_PAYLOADS: Include full payloads in logs
 */

const CONFIG = {
    TRACE_ALL: false,           // Set true for verbose logging
    TRACE_SENSITIVE: true,      // Focus on sensitive modules
    LOG_PAYLOADS: true,         // Log method arguments
    MAX_PAYLOAD_LENGTH: 500,    // Truncate long payloads
};

// Sensitive modules to always trace
const SENSITIVE_MODULES = [
    // Authentication & Security
    'RNKeychainManager',
    'KeychainModule',
    'RNSecureStorage',
    'SecureStore',
    'BiometricModule',
    'RNBiometrics',
    'TouchID',
    'FaceID',
    'RNFingerprintScanner',

    // Crypto
    'RNCryptoModule',
    'Crypto',
    'RNRandomBytes',
    'RNPBKDF2',
    'RNAes',
    'RNRsa',

    // Storage
    'AsyncStorage',
    'RNCAsyncStorage',
    'MMKV',
    'RealmModule',
    'SQLite',

    // Network
    'Networking',
    'RCTNetworking',
    'WebSocketModule',

    // Device Info
    'RNDeviceInfo',
    'DeviceInfo',
    'PlatformConstants',

    // Push Notifications
    'RNPushNotification',
    'PushNotificationIOS',
    'RNFirebaseMessaging',

    // Analytics & Tracking
    'RNFirebaseAnalytics',
    'Analytics',

    // Clipboard
    'Clipboard',
    'RNCClipboard',

    // Location
    'Geolocation',
    'RNLocation',
];

// Highlight patterns in payloads
const HIGHLIGHT_PATTERNS = [
    /password/i,
    /token/i,
    /secret/i,
    /api[_-]?key/i,
    /auth/i,
    /bearer/i,
    /session/i,
    /credential/i,
    /private/i,
    /encrypt/i,
    /decrypt/i,
];

function shouldTrace(moduleName) {
    if (CONFIG.TRACE_ALL) return true;
    if (CONFIG.TRACE_SENSITIVE) {
        return SENSITIVE_MODULES.some(s =>
            moduleName.toLowerCase().includes(s.toLowerCase())
        );
    }
    return false;
}

function formatPayload(payload) {
    if (!CONFIG.LOG_PAYLOADS) return '';

    let str;
    try {
        str = JSON.stringify(payload);
    } catch (e) {
        str = String(payload);
    }

    // Check for sensitive patterns
    let highlighted = false;
    for (const pattern of HIGHLIGHT_PATTERNS) {
        if (pattern.test(str)) {
            highlighted = true;
            break;
        }
    }

    if (str.length > CONFIG.MAX_PAYLOAD_LENGTH) {
        str = str.substring(0, CONFIG.MAX_PAYLOAD_LENGTH) + '...[truncated]';
    }

    return highlighted ? `\x1b[31m${str}\x1b[0m` : str;
}

function log(level, message) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const prefix = {
        'INFO': '\x1b[36m[*]\x1b[0m',
        'CALL': '\x1b[32m[>]\x1b[0m',
        'RET': '\x1b[33m[<]\x1b[0m',
        'WARN': '\x1b[33m[!]\x1b[0m',
        'SENSITIVE': '\x1b[31m[!!!]\x1b[0m',
    }[level] || '[?]';

    console.log(`${timestamp} ${prefix} ${message}`);
}

// ============================================================================
// Android Hooks
// ============================================================================

function hookAndroidBridge() {
    log('INFO', 'Hooking Android React Native bridge...');

    // Hook CatalystInstance.callFunction (JS -> Native)
    try {
        const CatalystInstanceImpl = Java.use('com.facebook.react.bridge.CatalystInstanceImpl');

        CatalystInstanceImpl.callFunction.overload('java.lang.String', 'java.lang.String', 'com.facebook.react.bridge.NativeArray').implementation = function(module, method, args) {
            if (shouldTrace(module)) {
                const isSensitive = SENSITIVE_MODULES.some(s => module.toLowerCase().includes(s.toLowerCase()));
                const level = isSensitive ? 'SENSITIVE' : 'CALL';

                log(level, `${module}.${method}()`);
                if (CONFIG.LOG_PAYLOADS && args) {
                    try {
                        const argsStr = formatPayload(args.toString());
                        if (argsStr) log('INFO', `    Args: ${argsStr}`);
                    } catch (e) {}
                }
            }
            return this.callFunction(module, method, args);
        };

        log('INFO', '  [+] Hooked CatalystInstanceImpl.callFunction');
    } catch (e) {
        log('WARN', `  [-] Failed to hook CatalystInstanceImpl: ${e}`);
    }

    // Hook NativeModule invocations
    try {
        const JavaMethodWrapper = Java.use('com.facebook.react.bridge.JavaMethodWrapper');

        JavaMethodWrapper.invoke.implementation = function(instance, args) {
            const moduleName = instance.getClass().getName();
            const methodName = this.getName();

            if (shouldTrace(moduleName) || shouldTrace(methodName)) {
                const isSensitive = SENSITIVE_MODULES.some(s =>
                    moduleName.toLowerCase().includes(s.toLowerCase()) ||
                    methodName.toLowerCase().includes(s.toLowerCase())
                );

                const level = isSensitive ? 'SENSITIVE' : 'CALL';
                log(level, `Native: ${moduleName}.${methodName}()`);

                if (CONFIG.LOG_PAYLOADS && args) {
                    try {
                        const argsArray = Java.array('java.lang.Object', args);
                        for (let i = 0; i < argsArray.length; i++) {
                            const argStr = formatPayload(argsArray[i]);
                            if (argStr) log('INFO', `    Arg[${i}]: ${argStr}`);
                        }
                    } catch (e) {}
                }
            }

            return this.invoke(instance, args);
        };

        log('INFO', '  [+] Hooked JavaMethodWrapper.invoke');
    } catch (e) {
        log('WARN', `  [-] Failed to hook JavaMethodWrapper: ${e}`);
    }

    // Hook specific sensitive modules
    hookAndroidKeychain();
    hookAndroidCrypto();
    hookAndroidStorage();
    hookAndroidNetwork();
}

function hookAndroidKeychain() {
    // Hook Android Keystore
    try {
        const KeyStore = Java.use('java.security.KeyStore');

        KeyStore.getEntry.overload('java.lang.String', 'java.security.KeyStore$ProtectionParameter').implementation = function(alias, param) {
            log('SENSITIVE', `KeyStore.getEntry("${alias}")`);
            return this.getEntry(alias, param);
        };

        KeyStore.setEntry.overload('java.lang.String', 'java.security.KeyStore$Entry', 'java.security.KeyStore$ProtectionParameter').implementation = function(alias, entry, param) {
            log('SENSITIVE', `KeyStore.setEntry("${alias}")`);
            return this.setEntry(alias, entry, param);
        };

        log('INFO', '  [+] Hooked Android KeyStore');
    } catch (e) {
        log('WARN', `  [-] Failed to hook KeyStore: ${e}`);
    }

    // Hook SharedPreferences (often used for tokens)
    try {
        const SharedPreferencesImpl = Java.use('android.app.SharedPreferencesImpl');

        SharedPreferencesImpl.getString.implementation = function(key, defValue) {
            const value = this.getString(key, defValue);
            if (HIGHLIGHT_PATTERNS.some(p => p.test(key))) {
                log('SENSITIVE', `SharedPreferences.getString("${key}") = "${value}"`);
            }
            return value;
        };

        SharedPreferencesImpl.edit.implementation = function() {
            const editor = this.edit();
            // We'd need to hook the editor too for full coverage
            return editor;
        };

        log('INFO', '  [+] Hooked SharedPreferences');
    } catch (e) {
        log('WARN', `  [-] Failed to hook SharedPreferences: ${e}`);
    }
}

function hookAndroidCrypto() {
    // Hook Cipher
    try {
        const Cipher = Java.use('javax.crypto.Cipher');

        Cipher.doFinal.overload('[B').implementation = function(input) {
            const mode = this.getOpmode() === 1 ? 'ENCRYPT' : 'DECRYPT';
            log('SENSITIVE', `Cipher.doFinal() - ${mode} (${input.length} bytes)`);
            return this.doFinal(input);
        };

        log('INFO', '  [+] Hooked Cipher');
    } catch (e) {
        log('WARN', `  [-] Failed to hook Cipher: ${e}`);
    }
}

function hookAndroidStorage() {
    // Hook AsyncStorage / MMKV common patterns
    try {
        const classes = [
            'com.facebook.react.modules.storage.AsyncStorageModule',
            'com.reactnativecommunity.asyncstorage.AsyncStorageModule',
            'com.tencent.mmkv.MMKV',
        ];

        for (const className of classes) {
            try {
                const StorageClass = Java.use(className);
                log('INFO', `  [+] Found storage: ${className}`);
            } catch (e) {}
        }
    } catch (e) {}
}

function hookAndroidNetwork() {
    // Hook OkHttp for network monitoring
    try {
        const OkHttpClient = Java.use('okhttp3.OkHttpClient');
        const Request = Java.use('okhttp3.Request');

        // This is covered by ssl_bypass but we log here for completeness
        log('INFO', '  [+] Network hooks available via ssl_bypass.js');
    } catch (e) {}
}

// ============================================================================
// iOS Hooks
// ============================================================================

function hookiOSBridge() {
    log('INFO', 'Hooking iOS React Native bridge...');

    // Hook RCTBridge
    try {
        const RCTBridge = ObjC.classes.RCTBridge;
        if (RCTBridge) {
            // Hook module calls
            Interceptor.attach(RCTBridge['- enqueueJSCall:method:args:completion:'].implementation, {
                onEnter: function(args) {
                    const module = ObjC.Object(args[2]).toString();
                    const method = ObjC.Object(args[3]).toString();

                    if (shouldTrace(module)) {
                        const isSensitive = SENSITIVE_MODULES.some(s =>
                            module.toLowerCase().includes(s.toLowerCase())
                        );
                        const level = isSensitive ? 'SENSITIVE' : 'CALL';

                        log(level, `RCTBridge: ${module}.${method}()`);

                        if (CONFIG.LOG_PAYLOADS) {
                            try {
                                const argsObj = ObjC.Object(args[4]);
                                log('INFO', `    Args: ${formatPayload(argsObj.toString())}`);
                            } catch (e) {}
                        }
                    }
                }
            });
            log('INFO', '  [+] Hooked RCTBridge');
        }
    } catch (e) {
        log('WARN', `  [-] Failed to hook RCTBridge: ${e}`);
    }

    // Hook specific sensitive modules
    hookiOSKeychain();
    hookiOSCrypto();
    hookiOSBiometrics();
}

function hookiOSKeychain() {
    // Hook Keychain Services
    try {
        const SecItemCopyMatching = Module.findExportByName('Security', 'SecItemCopyMatching');
        if (SecItemCopyMatching) {
            Interceptor.attach(SecItemCopyMatching, {
                onEnter: function(args) {
                    log('SENSITIVE', 'SecItemCopyMatching() - Keychain read');
                },
                onLeave: function(retval) {
                    log('INFO', `    Result: ${retval}`);
                }
            });
            log('INFO', '  [+] Hooked SecItemCopyMatching');
        }

        const SecItemAdd = Module.findExportByName('Security', 'SecItemAdd');
        if (SecItemAdd) {
            Interceptor.attach(SecItemAdd, {
                onEnter: function(args) {
                    log('SENSITIVE', 'SecItemAdd() - Keychain write');
                }
            });
            log('INFO', '  [+] Hooked SecItemAdd');
        }
    } catch (e) {
        log('WARN', `  [-] Failed to hook Keychain: ${e}`);
    }
}

function hookiOSCrypto() {
    // Hook CommonCrypto
    try {
        const CCCrypt = Module.findExportByName('libcommonCrypto.dylib', 'CCCrypt');
        if (CCCrypt) {
            Interceptor.attach(CCCrypt, {
                onEnter: function(args) {
                    const op = args[0].toInt32() === 0 ? 'ENCRYPT' : 'DECRYPT';
                    const dataLen = args[4].toInt32();
                    log('SENSITIVE', `CCCrypt() - ${op} (${dataLen} bytes)`);
                }
            });
            log('INFO', '  [+] Hooked CCCrypt');
        }
    } catch (e) {
        log('WARN', `  [-] Failed to hook CommonCrypto: ${e}`);
    }
}

function hookiOSBiometrics() {
    // Hook Local Authentication
    try {
        const LAContext = ObjC.classes.LAContext;
        if (LAContext) {
            Interceptor.attach(LAContext['- evaluatePolicy:localizedReason:reply:'].implementation, {
                onEnter: function(args) {
                    const reason = ObjC.Object(args[3]).toString();
                    log('SENSITIVE', `LAContext.evaluatePolicy() - Biometric auth: "${reason}"`);
                }
            });
            log('INFO', '  [+] Hooked LAContext (biometrics)');
        }
    } catch (e) {
        log('WARN', `  [-] Failed to hook LAContext: ${e}`);
    }
}

// ============================================================================
// Main
// ============================================================================

log('INFO', '========================================');
log('INFO', 'React Native Bridge Tracer');
log('INFO', '========================================');
log('INFO', `Config: TRACE_ALL=${CONFIG.TRACE_ALL}, TRACE_SENSITIVE=${CONFIG.TRACE_SENSITIVE}`);
log('INFO', '');

if (Java.available) {
    Java.perform(function() {
        hookAndroidBridge();
    });
} else if (ObjC.available) {
    hookiOSBridge();
} else {
    log('WARN', 'Neither Java nor ObjC runtime available');
}

log('INFO', '');
log('INFO', 'Bridge tracer initialized. Monitoring calls...');
log('INFO', '========================================');
