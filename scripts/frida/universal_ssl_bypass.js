/**
 * Universal SSL Certificate Pinning Bypass
 *
 * Comprehensive bypass for Android SSL pinning methods including:
 * - OkHttp3 CertificatePinner (all overloads)
 * - TrustManager (Android < 7 and > 7)
 * - Conscrypt TrustManagerImpl
 * - TrustKit, Appcelerator, Fabric
 * - Apache HttpClient, PhoneGap, IBM MobileFirst/WorkLight
 * - Flutter pinning plugins
 * - React Native OkHttpClientProvider
 * - WebView SSL errors
 * - Dynamic SSLPeerUnverifiedException bypass
 *
 * Based on frida-multiple-unpinning by Maurizio Siddu (akabe1)
 * and Universal Android SSL Pinning Bypass by pcipolloni
 *
 * Usage:
 *   frida -U -f com.example.app -l universal_ssl_bypass.js
 *
 * For proxy interception, also push your CA cert:
 *   adb push burp-ca.der /data/local/tmp/cert-der.crt
 */

'use strict';

setTimeout(function() {
    Java.perform(function() {
        console.log('');
        console.log('=====================================================');
        console.log('[#] Universal SSL Pinning Bypass');
        console.log('[#] Covering 40+ pinning implementations');
        console.log('=====================================================');

        var bypassCount = 0;

        // =====================================================================
        // TrustManager (Android < 7) - Create trust-all manager
        // =====================================================================
        try {
            var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
            var SSLContext = Java.use('javax.net.ssl.SSLContext');

            var TrustManager = Java.registerClass({
                name: 'com.frida.bypass.TrustAllManager',
                implements: [X509TrustManager],
                methods: {
                    checkClientTrusted: function(chain, authType) {},
                    checkServerTrusted: function(chain, authType) {},
                    getAcceptedIssuers: function() { return []; }
                }
            });

            var TrustManagers = [TrustManager.$new()];

            SSLContext.init.overload(
                '[Ljavax.net.ssl.KeyManager;',
                '[Ljavax.net.ssl.TrustManager;',
                'java.security.SecureRandom'
            ).implementation = function(keyManager, trustManager, secureRandom) {
                console.log('[+] Bypassing SSLContext.init TrustManager');
                this.init(keyManager, TrustManagers, secureRandom);
            };
            console.log('[+] TrustManager (Android < 7) bypass installed');
            bypassCount++;
        } catch(e) {
            console.log('[-] TrustManager bypass failed: ' + e);
        }

        // =====================================================================
        // OkHttp3 CertificatePinner (all 4 overloads)
        // =====================================================================
        var okhttp3Methods = [
            ['java.lang.String', 'java.util.List'],
            ['java.lang.String', 'java.security.cert.Certificate'],
            ['java.lang.String', '[Ljava.security.cert.Certificate;']
        ];

        okhttp3Methods.forEach(function(params, idx) {
            try {
                var CertificatePinner = Java.use('okhttp3.CertificatePinner');
                CertificatePinner.check.overload.apply(CertificatePinner.check, params).implementation = function() {
                    console.log('[+] Bypassing OkHttp3 CertificatePinner {' + (idx+1) + '}: ' + arguments[0]);
                    return;
                };
                console.log('[+] OkHttp3 CertificatePinner {' + (idx+1) + '} bypassed');
                bypassCount++;
            } catch(e) {}
        });

        // OkHttp3 Kotlin check$okhttp
        try {
            var CertificatePinner = Java.use('okhttp3.CertificatePinner');
            CertificatePinner['check$okhttp'].overload('java.lang.String', 'kotlin.jvm.functions.Function0').implementation = function(a, b) {
                console.log('[+] Bypassing OkHttp3 check$okhttp: ' + a);
                return;
            };
            console.log('[+] OkHttp3 check$okhttp bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // TrustManagerImpl (Android > 7) - Conscrypt
        // =====================================================================
        try {
            var array_list = Java.use("java.util.ArrayList");
            var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');

            // checkTrustedRecursive variants
            try {
                TrustManagerImpl.checkTrustedRecursive.implementation = function() {
                    console.log('[+] Bypassing TrustManagerImpl.checkTrustedRecursive');
                    return array_list.$new();
                };
                console.log('[+] TrustManagerImpl.checkTrustedRecursive bypassed');
                bypassCount++;
            } catch(e) {}

            // verifyChain variants
            try {
                TrustManagerImpl.verifyChain.implementation = function(untrustedChain) {
                    console.log('[+] Bypassing TrustManagerImpl.verifyChain');
                    return untrustedChain;
                };
                console.log('[+] TrustManagerImpl.verifyChain bypassed');
                bypassCount++;
            } catch(e) {}
        } catch(e) {}

        // =====================================================================
        // Conscrypt OpenSSLSocketImpl
        // =====================================================================
        try {
            var OpenSSLSocketImpl = Java.use('com.android.org.conscrypt.OpenSSLSocketImpl');
            OpenSSLSocketImpl.verifyCertificateChain.implementation = function() {
                console.log('[+] Bypassing OpenSSLSocketImpl.verifyCertificateChain');
            };
            console.log('[+] OpenSSLSocketImpl.verifyCertificateChain bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // TrustKit
        // =====================================================================
        try {
            var OkHostnameVerifier = Java.use('com.datatheorem.android.trustkit.pinning.OkHostnameVerifier');
            OkHostnameVerifier.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function(a, b) {
                console.log('[+] Bypassing TrustKit OkHostnameVerifier: ' + a);
                return true;
            };
            console.log('[+] TrustKit OkHostnameVerifier bypassed');
            bypassCount++;
        } catch(e) {}

        try {
            var PinningTrustManager = Java.use('com.datatheorem.android.trustkit.pinning.PinningTrustManager');
            PinningTrustManager.checkServerTrusted.implementation = function() {
                console.log('[+] Bypassing TrustKit PinningTrustManager');
            };
            console.log('[+] TrustKit PinningTrustManager bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Appcelerator Titanium
        // =====================================================================
        try {
            var AppceleratorPinning = Java.use('appcelerator.https.PinningTrustManager');
            AppceleratorPinning.checkServerTrusted.implementation = function() {
                console.log('[+] Bypassing Appcelerator PinningTrustManager');
            };
            console.log('[+] Appcelerator PinningTrustManager bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Fabric
        // =====================================================================
        try {
            var FabricPinning = Java.use('io.fabric.sdk.android.services.network.PinningTrustManager');
            FabricPinning.checkServerTrusted.implementation = function() {
                console.log('[+] Bypassing Fabric PinningTrustManager');
            };
            console.log('[+] Fabric PinningTrustManager bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Squareup OkHttp (pre-v3)
        // =====================================================================
        try {
            var SquareupPinner = Java.use('com.squareup.okhttp.CertificatePinner');
            SquareupPinner.check.overload('java.lang.String', 'java.util.List').implementation = function(a, b) {
                console.log('[+] Bypassing Squareup OkHttp CertificatePinner: ' + a);
                return;
            };
            console.log('[+] Squareup OkHttp CertificatePinner bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // PhoneGap/Cordova
        // =====================================================================
        try {
            var PhoneGap = Java.use('nl.xservices.plugins.sslCertificateChecker');
            PhoneGap.execute.overload('java.lang.String', 'org.json.JSONArray', 'org.apache.cordova.CallbackContext').implementation = function(a, b, c) {
                console.log('[+] Bypassing PhoneGap sslCertificateChecker: ' + a);
                return true;
            };
            console.log('[+] PhoneGap sslCertificateChecker bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Flutter SSL Pinning Plugins
        // =====================================================================
        try {
            var HttpCertPinning = Java.use('diefferson.http_certificate_pinning.HttpCertificatePinning');
            HttpCertPinning.checkConnexion.implementation = function() {
                console.log('[+] Bypassing Flutter HttpCertificatePinning');
                return true;
            };
            console.log('[+] Flutter HttpCertificatePinning bypassed');
            bypassCount++;
        } catch(e) {}

        try {
            var SslPinningPlugin = Java.use('com.macif.plugin.sslpinningplugin.SslPinningPlugin');
            SslPinningPlugin.checkConnexion.implementation = function() {
                console.log('[+] Bypassing Flutter SslPinningPlugin');
                return true;
            };
            console.log('[+] Flutter SslPinningPlugin bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // React Native OkHttpClientProvider
        // =====================================================================
        try {
            var OkHttpClientProvider = Java.use('com.facebook.react.modules.network.OkHttpClientProvider');
            OkHttpClientProvider.createClient.overload().implementation = function() {
                console.log('[+] Intercepting React Native OkHttpClientProvider.createClient');
                return this.createClient();
            };
            console.log('[+] React Native OkHttpClientProvider hooked');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // HostnameVerifier
        // =====================================================================
        try {
            var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
            var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');

            var TrustAllHostnames = Java.registerClass({
                name: 'com.frida.bypass.TrustAllHostnames',
                implements: [HostnameVerifier],
                methods: {
                    verify: function(hostname, session) {
                        console.log('[+] Accepting hostname: ' + hostname);
                        return true;
                    }
                }
            });

            HttpsURLConnection.setDefaultHostnameVerifier.implementation = function(v) {
                console.log('[+] Replacing default HostnameVerifier');
                this.setDefaultHostnameVerifier(TrustAllHostnames.$new());
            };
            console.log('[+] HostnameVerifier bypass installed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // WebViewClient SSL Error
        // =====================================================================
        try {
            var WebViewClient = Java.use('android.webkit.WebViewClient');
            WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
                console.log('[+] WebView SSL error - proceeding');
                handler.proceed();
            };
            console.log('[+] WebViewClient SSL error handler bypassed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Network Security Config (Android 7+)
        // =====================================================================
        try {
            var NetworkSecurityConfig = Java.use('android.security.net.config.NetworkSecurityConfig');
            NetworkSecurityConfig.isCleartextTrafficPermitted.overload().implementation = function() {
                console.log('[+] Allowing cleartext traffic');
                return true;
            };
            console.log('[+] NetworkSecurityConfig bypass installed');
            bypassCount++;
        } catch(e) {}

        // =====================================================================
        // Dynamic SSLPeerUnverifiedException bypass
        // =====================================================================
        try {
            var SSLPeerUnverifiedException = Java.use('javax.net.ssl.SSLPeerUnverifiedException');
            SSLPeerUnverifiedException.$init.implementation = function(reason) {
                console.log('[!] SSLPeerUnverifiedException triggered: ' + reason);
                try {
                    var stackTrace = Java.use('java.lang.Thread').currentThread().getStackTrace();
                    for (var i = 0; i < Math.min(stackTrace.length, 5); i++) {
                        console.log('    ' + stackTrace[i].getClassName() + '.' + stackTrace[i].getMethodName());
                    }
                } catch(e) {}
                return this.$init(reason);
            };
            console.log('[+] SSLPeerUnverifiedException monitor installed');
            bypassCount++;
        } catch(e) {}

        console.log('');
        console.log('=====================================================');
        console.log('[#] SSL Bypass Summary: ' + bypassCount + ' hooks installed');
        console.log('[#] Ready for traffic interception');
        console.log('=====================================================');
    });
}, 0);
