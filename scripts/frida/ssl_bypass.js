/**
 * SSL Certificate Pinning Bypass for React Native / Hermes Apps
 *
 * Usage:
 *   frida -U -f com.example.app -l ssl_bypass.js --no-pause
 *
 * Covers:
 *   - OkHttp CertificatePinner
 *   - TrustManager
 *   - React Native TLS config
 *   - Common pinning libraries
 */

'use strict';

console.log('[SSL Bypass] Initializing...');

Java.perform(function() {

    // ========================================================================
    // OkHttp3 CertificatePinner Bypass
    // ========================================================================

    try {
        const CertificatePinner = Java.use('okhttp3.CertificatePinner');

        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {
            console.log('[SSL] Bypassing CertificatePinner.check for: ' + hostname);
            return;
        };

        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(hostname, peerCertificates) {
            console.log('[SSL] Bypassing CertificatePinner.check (cert[]) for: ' + hostname);
            return;
        };

        console.log('[+] OkHttp3 CertificatePinner bypassed');
    } catch(e) {
        console.log('[-] OkHttp3 CertificatePinner not found');
    }

    // OkHttp3 Builder - remove pinning during build
    try {
        const Builder = Java.use('okhttp3.OkHttpClient$Builder');

        Builder.certificatePinner.implementation = function(certificatePinner) {
            console.log('[SSL] Ignoring CertificatePinner configuration');
            return this;
        };

        console.log('[+] OkHttp3 Builder.certificatePinner bypassed');
    } catch(e) {}

    // ========================================================================
    // TrustManager Bypass (Universal)
    // ========================================================================

    try {
        const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        const SSLContext = Java.use('javax.net.ssl.SSLContext');

        // Create a TrustManager that trusts everything
        const TrustAllManager = Java.registerClass({
            name: 'com.frida.TrustAllManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {
                    // Trust all
                },
                checkServerTrusted: function(chain, authType) {
                    console.log('[SSL] TrustAllManager: accepting server cert');
                },
                getAcceptedIssuers: function() {
                    return [];
                }
            }
        });

        // Hook SSLContext.init to inject our TrustManager
        SSLContext.init.overload(
            '[Ljavax.net.ssl.KeyManager;',
            '[Ljavax.net.ssl.TrustManager;',
            'java.security.SecureRandom'
        ).implementation = function(keyManagers, trustManagers, secureRandom) {
            console.log('[SSL] SSLContext.init intercepted - injecting TrustAllManager');
            const trustAll = [TrustAllManager.$new()];
            this.init(keyManagers, trustAll, secureRandom);
        };

        console.log('[+] TrustManager bypass installed');
    } catch(e) {
        console.log('[-] TrustManager bypass failed: ' + e);
    }

    // ========================================================================
    // HostnameVerifier Bypass
    // ========================================================================

    try {
        const HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
        const HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');

        // Create verifier that accepts all hostnames
        const TrustAllHostnames = Java.registerClass({
            name: 'com.frida.TrustAllHostnames',
            implements: [HostnameVerifier],
            methods: {
                verify: function(hostname, session) {
                    console.log('[SSL] Accepting hostname: ' + hostname);
                    return true;
                }
            }
        });

        HttpsURLConnection.setDefaultHostnameVerifier.implementation = function(verifier) {
            console.log('[SSL] Replacing HostnameVerifier');
            this.setDefaultHostnameVerifier(TrustAllHostnames.$new());
        };

        console.log('[+] HostnameVerifier bypass installed');
    } catch(e) {}

    // ========================================================================
    // TrustKit Bypass (if present)
    // ========================================================================

    try {
        const TrustKit = Java.use('com.datatheorem.android.trustkit.TrustKit');

        TrustKit.initializeWithNetworkSecurityConfiguration.overload(
            'android.content.Context', 'int'
        ).implementation = function(context, resId) {
            console.log('[SSL] TrustKit.initializeWithNetworkSecurityConfiguration bypassed');
            return;
        };

        console.log('[+] TrustKit bypassed');
    } catch(e) {}

    // ========================================================================
    // React Native SSL Hooks
    // ========================================================================

    // OkHttpClientProvider (React Native networking)
    try {
        const OkHttpClientProvider = Java.use('com.facebook.react.modules.network.OkHttpClientProvider');

        OkHttpClientProvider.createClient.overload().implementation = function() {
            console.log('[SSL] OkHttpClientProvider.createClient called');
            const client = this.createClient();
            return client;
        };

        console.log('[+] React Native OkHttpClientProvider hooked');
    } catch(e) {}

    // ========================================================================
    // Network Security Config Bypass (Android 7+)
    // ========================================================================

    try {
        const NetworkSecurityConfig = Java.use('android.security.net.config.NetworkSecurityConfig');

        NetworkSecurityConfig.isCleartextTrafficPermitted.overload().implementation = function() {
            console.log('[SSL] Allowing cleartext traffic');
            return true;
        };

        NetworkSecurityConfig.isCleartextTrafficPermitted.overload('java.lang.String').implementation = function(hostname) {
            console.log('[SSL] Allowing cleartext traffic to: ' + hostname);
            return true;
        };

        console.log('[+] NetworkSecurityConfig bypassed');
    } catch(e) {}

    // ========================================================================
    // WebView SSL Error Handler
    // ========================================================================

    try {
        const WebViewClient = Java.use('android.webkit.WebViewClient');

        WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
            console.log('[SSL] WebView SSL error - proceeding anyway');
            handler.proceed();
        };

        console.log('[+] WebViewClient SSL error handler bypassed');
    } catch(e) {}

});

console.log('[SSL Bypass] Ready - all certificate checks should be bypassed');
console.log('[SSL Bypass] You can now use mitmproxy/Charles to intercept HTTPS traffic');
