/**
 * Hermes Runtime Hooks for Frida
 *
 * Usage:
 *   frida -U -f com.example.app -l hermes_hooks.js --no-pause
 *
 * Note: Hermes internals are not easily hookable. This script provides
 * alternative approaches via React Native bridge and network layer.
 */

'use strict';

const CONFIG = {
    logNetworkRequests: true,
    logJSExceptions: true,
    hookReactNativeBridge: true,
    dumpStrings: false,
};

console.log('[Hermes Hooks] Initializing...');

// ============================================================================
// React Native Bridge Hooks
// ============================================================================

if (CONFIG.hookReactNativeBridge) {
    Java.perform(function() {
        try {
            // Hook CatalystInstance for bridge calls
            const CatalystInstanceImpl = Java.use('com.facebook.react.bridge.CatalystInstanceImpl');

            CatalystInstanceImpl.jniCallJSFunction.implementation = function(module, method, args) {
                console.log('[RN Bridge] ' + module + '.' + method);
                if (args) {
                    try {
                        console.log('  Args: ' + args.toString().substring(0, 200));
                    } catch(e) {}
                }
                return this.jniCallJSFunction(module, method, args);
            };
            console.log('[+] Hooked CatalystInstanceImpl.jniCallJSFunction');
        } catch(e) {
            console.log('[-] CatalystInstanceImpl hook failed: ' + e);
        }

        try {
            // Hook NativeModule calls
            const JavaModuleWrapper = Java.use('com.facebook.react.bridge.JavaModuleWrapper');

            JavaModuleWrapper.invoke.implementation = function(reactContext, executorToken, methodId, args) {
                const name = this.getName();
                console.log('[NativeModule] ' + name + ' method #' + methodId);
                return this.invoke(reactContext, executorToken, methodId, args);
            };
            console.log('[+] Hooked JavaModuleWrapper.invoke');
        } catch(e) {
            console.log('[-] JavaModuleWrapper hook failed: ' + e);
        }
    });
}

// ============================================================================
// Network Request Hooks (OkHttp)
// ============================================================================

if (CONFIG.logNetworkRequests) {
    Java.perform(function() {
        try {
            const OkHttpClient = Java.use('okhttp3.OkHttpClient');
            const Request = Java.use('okhttp3.Request');
            const Response = Java.use('okhttp3.Response');
            const Call = Java.use('okhttp3.Call');
            const RealCall = Java.use('okhttp3.RealCall');

            RealCall.execute.implementation = function() {
                const request = this.request();
                const url = request.url().toString();
                const method = request.method();

                console.log('[HTTP] ' + method + ' ' + url);

                // Log headers
                const headers = request.headers();
                for (let i = 0; i < headers.size(); i++) {
                    const name = headers.name(i);
                    const value = headers.value(i);
                    if (name.toLowerCase().includes('auth') ||
                        name.toLowerCase().includes('token') ||
                        name.toLowerCase().includes('api')) {
                        console.log('  [Header] ' + name + ': ' + value.substring(0, 50));
                    }
                }

                const response = this.execute();
                console.log('  [Response] ' + response.code());
                return response;
            };
            console.log('[+] Hooked OkHttp RealCall.execute');

        } catch(e) {
            console.log('[-] OkHttp hook failed: ' + e);
        }

        // Hook React Native's NetworkingModule
        try {
            const NetworkingModule = Java.use('com.facebook.react.modules.network.NetworkingModule');

            NetworkingModule.sendRequest.overload(
                'java.lang.String', 'java.lang.String', 'int',
                'com.facebook.react.bridge.ReadableArray',
                'com.facebook.react.bridge.ReadableMap',
                'java.lang.String', 'boolean', 'int', 'boolean'
            ).implementation = function(method, url, requestId, headers, data, responseType,
                                        useIncrementalUpdates, timeout, withCredentials) {
                console.log('[RN Fetch] ' + method + ' ' + url);
                return this.sendRequest(method, url, requestId, headers, data, responseType,
                                        useIncrementalUpdates, timeout, withCredentials);
            };
            console.log('[+] Hooked NetworkingModule.sendRequest');
        } catch(e) {
            console.log('[-] NetworkingModule hook failed: ' + e);
        }
    });
}

// ============================================================================
// JavaScript Exception Logging
// ============================================================================

if (CONFIG.logJSExceptions) {
    Java.perform(function() {
        try {
            const JSException = Java.use('com.facebook.react.bridge.JSException');

            JSException.$init.overload('java.lang.String').implementation = function(message) {
                console.log('[JS Exception] ' + message);
                return this.$init(message);
            };
            console.log('[+] Hooked JSException');
        } catch(e) {
            console.log('[-] JSException hook failed: ' + e);
        }
    });
}

// ============================================================================
// Hermes Library Analysis
// ============================================================================

// Find and log Hermes library info
setTimeout(function() {
    const modules = Process.enumerateModules();
    modules.forEach(function(m) {
        if (m.name.toLowerCase().includes('hermes')) {
            console.log('[Hermes Module] ' + m.name);
            console.log('  Base: ' + m.base);
            console.log('  Size: ' + m.size);
            console.log('  Path: ' + m.path);

            // Enumerate exports (limited)
            try {
                const exports = m.enumerateExports().slice(0, 20);
                console.log('  Exports (first 20):');
                exports.forEach(function(e) {
                    console.log('    ' + e.type + ' ' + e.name);
                });
            } catch(e) {}
        }
    });
}, 1000);

// ============================================================================
// Utility Functions
// ============================================================================

// Export helper to evaluate JS in app context (experimental)
rpc.exports = {
    // List loaded React Native modules
    listModules: function() {
        const modules = [];
        Java.perform(function() {
            try {
                const ReactContext = Java.use('com.facebook.react.bridge.ReactContext');
                // This is limited - full module list requires deeper hooks
            } catch(e) {}
        });
        return modules;
    },

    // Get app package info
    getPackageInfo: function() {
        let info = {};
        Java.perform(function() {
            const ActivityThread = Java.use('android.app.ActivityThread');
            const app = ActivityThread.currentApplication();
            const context = app.getApplicationContext();
            const pm = context.getPackageManager();
            const packageName = context.getPackageName();
            const packageInfo = pm.getPackageInfo(packageName, 0);

            info = {
                packageName: packageName,
                versionName: packageInfo.versionName.value,
                versionCode: packageInfo.versionCode.value,
            };
        });
        return info;
    }
};

console.log('[Hermes Hooks] Ready. Use frida REPL to call rpc.exports functions.');
