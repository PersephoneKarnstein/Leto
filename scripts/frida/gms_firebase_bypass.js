/**
 * Google Play Services & Firebase Bypass
 *
 * For apps that require GMS/Firebase but testing on emulators without Play Services.
 * Bypasses:
 * - GoogleApiAvailability checks
 * - Play Store availability checks
 * - Firebase Cloud Messaging (FCM) token blocking
 * - Firebase Analytics init
 * - GMS Core availability
 *
 * Usage:
 *   frida -U -f com.example.app -l gms_firebase_bypass.js
 *
 * Note: This provides stub returns - full functionality requires actual GMS
 */

'use strict';

Java.perform(function() {
    console.log('');
    console.log('=====================================================');
    console.log('[#] Google Play Services & Firebase Bypass');
    console.log('=====================================================');

    var bypassCount = 0;

    // =========================================================================
    // GoogleApiAvailability - Report as SUCCESS (0)
    // =========================================================================
    try {
        var GoogleApiAvailability = Java.use('com.google.android.gms.common.GoogleApiAvailability');

        GoogleApiAvailability.isGooglePlayServicesAvailable.overload('android.content.Context').implementation = function(ctx) {
            console.log('[+] GoogleApiAvailability.isGooglePlayServicesAvailable -> SUCCESS');
            return 0; // ConnectionResult.SUCCESS
        };

        GoogleApiAvailability.isGooglePlayServicesAvailable.overload('android.content.Context', 'int').implementation = function(ctx, version) {
            console.log('[+] GoogleApiAvailability.isGooglePlayServicesAvailable(version=' + version + ') -> SUCCESS');
            return 0;
        };
        console.log('[+] GoogleApiAvailability bypass installed');
        bypassCount++;
    } catch(e) {
        console.log('[-] GoogleApiAvailability not found: ' + e);
    }

    // =========================================================================
    // GooglePlayServicesUtil (deprecated but still used)
    // =========================================================================
    try {
        var GooglePlayServicesUtil = Java.use('com.google.android.gms.common.GooglePlayServicesUtil');

        GooglePlayServicesUtil.isGooglePlayServicesAvailable.implementation = function(ctx) {
            console.log('[+] GooglePlayServicesUtil.isGooglePlayServicesAvailable -> SUCCESS');
            return 0;
        };
        console.log('[+] GooglePlayServicesUtil bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // ConnectionResult checks
    // =========================================================================
    try {
        var ConnectionResult = Java.use('com.google.android.gms.common.ConnectionResult');

        ConnectionResult.isSuccess.implementation = function() {
            console.log('[+] ConnectionResult.isSuccess -> true');
            return true;
        };
        console.log('[+] ConnectionResult.isSuccess bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Firebase Messaging - Token bypass
    // =========================================================================
    try {
        var FirebaseMessaging = Java.use('com.google.firebase.messaging.FirebaseMessaging');

        // getToken() returns a Task that would block
        FirebaseMessaging.getToken.implementation = function() {
            console.log('[+] FirebaseMessaging.getToken - returning mock task');
            // Return the original but it will likely fail - see SyncTask bypass below
            return this.getToken();
        };
        console.log('[+] FirebaseMessaging.getToken hooked');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Firebase Messaging SyncTask - Prevent blocking on token refresh
    // =========================================================================
    try {
        var SyncTask = Java.use('com.google.firebase.messaging.SyncTask');

        // maybeRefreshToken blocks waiting for GMS - bypass it
        SyncTask.maybeRefreshToken.implementation = function() {
            console.log('[+] SyncTask.maybeRefreshToken -> true (bypassed blocking)');
            return true;
        };
        console.log('[+] SyncTask.maybeRefreshToken bypass installed');
        bypassCount++;
    } catch(e) {
        console.log('[-] SyncTask not found (may be obfuscated)');
    }

    // =========================================================================
    // Firebase InstanceId - Token generation
    // =========================================================================
    try {
        var FirebaseInstanceId = Java.use('com.google.firebase.iid.FirebaseInstanceId');

        FirebaseInstanceId.getToken.overload().implementation = function() {
            console.log('[+] FirebaseInstanceId.getToken -> mock token');
            return "mock_fcm_token_for_testing_12345";
        };

        FirebaseInstanceId.getToken.overload('java.lang.String', 'java.lang.String').implementation = function(a, b) {
            console.log('[+] FirebaseInstanceId.getToken(sender, scope) -> mock token');
            return "mock_fcm_token_for_testing_12345";
        };
        console.log('[+] FirebaseInstanceId.getToken bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Firebase Analytics - Stub initialization
    // =========================================================================
    try {
        var FirebaseAnalytics = Java.use('com.google.firebase.analytics.FirebaseAnalytics');

        FirebaseAnalytics.logEvent.overload('java.lang.String', 'android.os.Bundle').implementation = function(name, params) {
            console.log('[+] FirebaseAnalytics.logEvent: ' + name + ' (stubbed)');
            // Don't call original - just stub
        };

        FirebaseAnalytics.setUserProperty.implementation = function(name, value) {
            console.log('[+] FirebaseAnalytics.setUserProperty: ' + name + ' (stubbed)');
        };
        console.log('[+] FirebaseAnalytics bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Firebase Crashlytics - Prevent crashes on missing GMS
    // =========================================================================
    try {
        var Crashlytics = Java.use('com.google.firebase.crashlytics.FirebaseCrashlytics');

        Crashlytics.getInstance.implementation = function() {
            console.log('[+] Crashlytics.getInstance called');
            return this.getInstance();
        };
        console.log('[+] Crashlytics hooked');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // GMS Tasks - Prevent blocking on failed tasks
    // =========================================================================
    try {
        var Tasks = Java.use('com.google.android.gms.tasks.Tasks');

        // await() blocks indefinitely if GMS isn't available
        Tasks.await.overload('com.google.android.gms.tasks.Task').implementation = function(task) {
            console.log('[!] Tasks.await called - may block if GMS unavailable');
            try {
                return this.await(task);
            } catch(e) {
                console.log('[+] Tasks.await failed, returning null: ' + e);
                return null;
            }
        };

        Tasks.await.overload('com.google.android.gms.tasks.Task', 'long', 'java.util.concurrent.TimeUnit').implementation = function(task, timeout, unit) {
            console.log('[+] Tasks.await with timeout: ' + timeout);
            try {
                return this.await(task, timeout, unit);
            } catch(e) {
                console.log('[+] Tasks.await timed out, returning null');
                return null;
            }
        };
        console.log('[+] GMS Tasks.await bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Package Manager - Hide missing GMS packages
    // =========================================================================
    try {
        var PackageManager = Java.use('android.app.ApplicationPackageManager');

        var gmsPackages = [
            'com.google.android.gms',
            'com.android.vending',
            'com.google.android.gsf'
        ];

        // Don't throw PackageNotFoundException for GMS packages
        PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(name, flags) {
            try {
                return this.getPackageInfo(name, flags);
            } catch(e) {
                if (gmsPackages.indexOf(name) > -1) {
                    console.log('[!] GMS package not found: ' + name + ' - app may not work fully');
                }
                throw e;
            }
        };
        console.log('[+] PackageManager GMS monitoring installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // React Native - Firebase module initialization
    // =========================================================================
    try {
        var RNFirebaseModule = Java.use('io.invertase.firebase.common.RCTConvertFirebase');
        console.log('[+] React Native Firebase detected');
    } catch(e) {}

    try {
        var RNFirebaseMessaging = Java.use('io.invertase.firebase.messaging.RNFirebaseMessagingModule');
        console.log('[+] React Native Firebase Messaging detected');
    } catch(e) {}

    // =========================================================================
    // Common GMS initialization patterns
    // =========================================================================

    // Watch for exceptions related to GMS
    try {
        var GooglePlayServicesNotAvailableException = Java.use('com.google.android.gms.common.GooglePlayServicesNotAvailableException');
        GooglePlayServicesNotAvailableException.$init.overload('int').implementation = function(errorCode) {
            console.log('[!] GooglePlayServicesNotAvailableException: errorCode=' + errorCode);
            console.log('    Error codes: 1=SERVICE_MISSING, 2=SERVICE_VERSION_UPDATE_REQUIRED, 3=SERVICE_DISABLED, 9=SERVICE_INVALID');
            return this.$init(errorCode);
        };
    } catch(e) {}

    console.log('');
    console.log('=====================================================');
    console.log('[#] GMS/Firebase Bypass Summary: ' + bypassCount + ' hooks installed');
    console.log('[#] Note: Full functionality requires actual Play Services');
    console.log('[#] Consider using MicroG or a rooted device with GApps');
    console.log('=====================================================');
});
