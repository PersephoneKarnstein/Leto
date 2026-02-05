/**
 * Framework Detection Script
 *
 * Detects what frameworks and libraries an Android app is using:
 * - React Native / Hermes
 * - Flutter
 * - Xamarin
 * - Cordova/PhoneGap
 * - Unity
 * - Native libraries
 * - Common SDKs (Firebase, Analytics, Crash reporting, etc.)
 *
 * Usage:
 *   frida -U -f com.example.app -l detect_frameworks.js
 */

'use strict';

setTimeout(function() {
    Java.perform(function() {
        console.log('');
        console.log('=====================================================');
        console.log('[#] Framework & Library Detection');
        console.log('=====================================================');

        var detected = {
            frameworks: [],
            networking: [],
            analytics: [],
            security: [],
            storage: [],
            other: []
        };

        // =====================================================================
        // Framework Detection
        // =====================================================================

        // React Native
        try {
            Java.use('com.facebook.react.ReactApplication');
            detected.frameworks.push('React Native');
        } catch(e) {}

        try {
            Java.use('com.facebook.react.bridge.CatalystInstance');
            detected.frameworks.push('React Native (CatalystInstance)');
        } catch(e) {}

        // Hermes
        try {
            Java.use('com.facebook.hermes.reactexecutor.HermesExecutor');
            detected.frameworks.push('Hermes JS Engine');
        } catch(e) {}

        // Check native Hermes library
        var modules = Process.enumerateModules();
        modules.forEach(function(m) {
            if (m.name.toLowerCase().includes('hermes')) {
                detected.frameworks.push('Hermes Native: ' + m.name);
            }
            if (m.name.toLowerCase().includes('flutter')) {
                detected.frameworks.push('Flutter Native: ' + m.name);
            }
            if (m.name.toLowerCase().includes('mono')) {
                detected.frameworks.push('Mono (Xamarin): ' + m.name);
            }
            if (m.name.toLowerCase().includes('unity')) {
                detected.frameworks.push('Unity: ' + m.name);
            }
        });

        // Flutter
        try {
            Java.use('io.flutter.embedding.engine.FlutterEngine');
            detected.frameworks.push('Flutter');
        } catch(e) {}

        try {
            Java.use('io.flutter.app.FlutterApplication');
            detected.frameworks.push('Flutter (FlutterApplication)');
        } catch(e) {}

        // Xamarin
        try {
            Java.use('mono.MonoPackageManager');
            detected.frameworks.push('Xamarin');
        } catch(e) {}

        try {
            Java.use('xamarin.android.net.OldAndroidClientHandler');
            detected.frameworks.push('Xamarin.Android');
        } catch(e) {}

        // Cordova/PhoneGap
        try {
            Java.use('org.apache.cordova.CordovaActivity');
            detected.frameworks.push('Apache Cordova');
        } catch(e) {}

        try {
            Java.use('org.apache.cordova.CordovaWebView');
            detected.frameworks.push('Cordova WebView');
        } catch(e) {}

        // =====================================================================
        // Networking Libraries
        // =====================================================================

        // OkHttp
        try {
            var okhttp = Java.use('okhttp3.OkHttpClient');
            detected.networking.push('OkHttp3');
        } catch(e) {}

        try {
            Java.use('com.squareup.okhttp.OkHttpClient');
            detected.networking.push('OkHttp (legacy)');
        } catch(e) {}

        // Retrofit
        try {
            Java.use('retrofit2.Retrofit');
            detected.networking.push('Retrofit2');
        } catch(e) {}

        // Volley
        try {
            Java.use('com.android.volley.RequestQueue');
            detected.networking.push('Volley');
        } catch(e) {}

        // Apollo GraphQL
        try {
            Java.use('com.apollographql.apollo.ApolloClient');
            detected.networking.push('Apollo GraphQL');
        } catch(e) {}

        // =====================================================================
        // Analytics & Tracking
        // =====================================================================

        // Firebase Analytics
        try {
            Java.use('com.google.firebase.analytics.FirebaseAnalytics');
            detected.analytics.push('Firebase Analytics');
        } catch(e) {}

        // Google Analytics
        try {
            Java.use('com.google.android.gms.analytics.GoogleAnalytics');
            detected.analytics.push('Google Analytics');
        } catch(e) {}

        // Facebook SDK
        try {
            Java.use('com.facebook.FacebookSdk');
            detected.analytics.push('Facebook SDK');
        } catch(e) {}

        // Mixpanel
        try {
            Java.use('com.mixpanel.android.mpmetrics.MixpanelAPI');
            detected.analytics.push('Mixpanel');
        } catch(e) {}

        // Amplitude
        try {
            Java.use('com.amplitude.api.Amplitude');
            detected.analytics.push('Amplitude');
        } catch(e) {}

        // Segment
        try {
            Java.use('com.segment.analytics.Analytics');
            detected.analytics.push('Segment');
        } catch(e) {}

        // Adjust
        try {
            Java.use('com.adjust.sdk.Adjust');
            detected.analytics.push('Adjust');
        } catch(e) {}

        // =====================================================================
        // Crash Reporting
        // =====================================================================

        // Firebase Crashlytics
        try {
            Java.use('com.google.firebase.crashlytics.FirebaseCrashlytics');
            detected.analytics.push('Firebase Crashlytics');
        } catch(e) {}

        // Sentry
        try {
            Java.use('io.sentry.android.core.SentryAndroid');
            detected.analytics.push('Sentry');
        } catch(e) {}

        // Bugsnag
        try {
            Java.use('com.bugsnag.android.Bugsnag');
            detected.analytics.push('Bugsnag');
        } catch(e) {}

        // =====================================================================
        // Security Libraries
        // =====================================================================

        // TrustKit
        try {
            Java.use('com.datatheorem.android.trustkit.TrustKit');
            detected.security.push('TrustKit (SSL Pinning)');
        } catch(e) {}

        // RootBeer
        try {
            Java.use('com.scottyab.rootbeer.RootBeer');
            detected.security.push('RootBeer (Root Detection)');
        } catch(e) {}

        // SafetyNet
        try {
            Java.use('com.google.android.gms.safetynet.SafetyNetClient');
            detected.security.push('SafetyNet');
        } catch(e) {}

        // Play Integrity
        try {
            Java.use('com.google.android.play.core.integrity.IntegrityManager');
            detected.security.push('Play Integrity API');
        } catch(e) {}

        // Dexguard
        try {
            Java.use('com.guardsquare.dexguard.runtime.detection.RootDetector');
            detected.security.push('DexGuard');
        } catch(e) {}

        // =====================================================================
        // Storage & Database
        // =====================================================================

        // Room
        try {
            Java.use('androidx.room.RoomDatabase');
            detected.storage.push('Room Database');
        } catch(e) {}

        // Realm
        try {
            Java.use('io.realm.Realm');
            detected.storage.push('Realm');
        } catch(e) {}

        // SQLCipher
        try {
            Java.use('net.sqlcipher.database.SQLiteDatabase');
            detected.storage.push('SQLCipher (Encrypted DB)');
        } catch(e) {}

        // SharedPreferences (encrypted)
        try {
            Java.use('androidx.security.crypto.EncryptedSharedPreferences');
            detected.storage.push('EncryptedSharedPreferences');
        } catch(e) {}

        // =====================================================================
        // Other
        // =====================================================================

        // Gson
        try {
            Java.use('com.google.gson.Gson');
            detected.other.push('Gson');
        } catch(e) {}

        // Moshi
        try {
            Java.use('com.squareup.moshi.Moshi');
            detected.other.push('Moshi');
        } catch(e) {}

        // Glide
        try {
            Java.use('com.bumptech.glide.Glide');
            detected.other.push('Glide (Images)');
        } catch(e) {}

        // Picasso
        try {
            Java.use('com.squareup.picasso.Picasso');
            detected.other.push('Picasso (Images)');
        } catch(e) {}

        // ExoPlayer
        try {
            Java.use('com.google.android.exoplayer2.ExoPlayer');
            detected.other.push('ExoPlayer');
        } catch(e) {}

        // =====================================================================
        // Print Results
        // =====================================================================

        console.log('');
        console.log('[Frameworks]');
        if (detected.frameworks.length > 0) {
            detected.frameworks.forEach(function(f) { console.log('  - ' + f); });
        } else {
            console.log('  - Native Android (no cross-platform framework detected)');
        }

        console.log('');
        console.log('[Networking]');
        if (detected.networking.length > 0) {
            detected.networking.forEach(function(f) { console.log('  - ' + f); });
        } else {
            console.log('  - None detected');
        }

        console.log('');
        console.log('[Analytics & Tracking]');
        if (detected.analytics.length > 0) {
            detected.analytics.forEach(function(f) { console.log('  - ' + f); });
        } else {
            console.log('  - None detected');
        }

        console.log('');
        console.log('[Security]');
        if (detected.security.length > 0) {
            detected.security.forEach(function(f) { console.log('  - ' + f); });
        } else {
            console.log('  - None detected');
        }

        console.log('');
        console.log('[Storage]');
        if (detected.storage.length > 0) {
            detected.storage.forEach(function(f) { console.log('  - ' + f); });
        } else {
            console.log('  - Standard SQLite/SharedPreferences');
        }

        console.log('');
        console.log('[Other Libraries]');
        if (detected.other.length > 0) {
            detected.other.forEach(function(f) { console.log('  - ' + f); });
        }

        console.log('');
        console.log('=====================================================');

        // Export for programmatic access
        rpc.exports = {
            getDetected: function() { return detected; }
        };
    });
}, 1000); // Delay to let classes load
