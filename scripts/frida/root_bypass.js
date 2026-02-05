/**
 * Root/Emulator Detection Bypass
 *
 * Comprehensive bypass for Android root detection methods including:
 * - Package checks (su apps, Magisk, Xposed, etc.)
 * - Binary file checks (su, busybox, etc.)
 * - System property checks (ro.debuggable, ro.secure, etc.)
 * - Build tag checks (test-keys)
 * - Native fopen/system calls
 * - ProcessBuilder and Runtime.exec
 * - SafetyNet/Play Integrity (basic)
 *
 * Based on fridantiroot by dzonerzy
 *
 * Usage:
 *   frida -U -f com.example.app -l root_bypass.js
 */

'use strict';

Java.perform(function() {
    console.log('');
    console.log('=====================================================');
    console.log('[#] Root/Emulator Detection Bypass');
    console.log('=====================================================');

    // Known root-related packages
    var RootPackages = [
        "com.noshufou.android.su",
        "com.noshufou.android.su.elite",
        "eu.chainfire.supersu",
        "com.koushikdutta.superuser",
        "com.thirdparty.superuser",
        "com.yellowes.su",
        "com.topjohnwu.magisk",
        "com.kingroot.kinguser",
        "com.kingo.root",
        "com.smedialink.oneclickroot",
        "com.zhiqupk.root.global",
        "com.alephzain.framaroot",
        "com.koushikdutta.rommanager",
        "com.koushikdutta.rommanager.license",
        "com.dimonvideo.luckypatcher",
        "com.chelpus.lackypatch",
        "com.ramdroid.appquarantine",
        "com.ramdroid.appquarantinepro",
        "com.devadvance.rootcloak",
        "com.devadvance.rootcloakplus",
        "de.robv.android.xposed.installer",
        "com.saurik.substrate",
        "com.zachspong.temprootremovejb",
        "com.amphoras.hidemyroot",
        "com.amphoras.hidemyrootadfree",
        "com.formyhm.hiderootPremium",
        "com.formyhm.hideroot",
        "me.phh.superuser",
        "eu.chainfire.supersu.pro",
        "com.kingouser.com"
    ];

    // Root-related binaries
    var RootBinaries = [
        "su",
        "busybox",
        "supersu",
        "Superuser.apk",
        "KingoUser.apk",
        "SuperSu.apk",
        "magisk",
        "magiskhide",
        "magiskpolicy",
        ".magisk"
    ];

    // Root-related paths
    var RootPaths = [
        "/system/app/Superuser.apk",
        "/sbin/su",
        "/system/bin/su",
        "/system/xbin/su",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/system/sd/xbin/su",
        "/system/bin/failsafe/su",
        "/data/local/su",
        "/su/bin/su",
        "/system/xbin/busybox",
        "/sbin/.magisk",
        "/data/adb/magisk"
    ];

    // Properties to spoof
    var RootProperties = {
        "ro.build.selinux": "1",
        "ro.debuggable": "0",
        "service.adb.root": "0",
        "ro.secure": "1",
        "ro.build.type": "user",
        "ro.build.tags": "release-keys"
    };

    var bypassCount = 0;

    // =========================================================================
    // PackageManager.getPackageInfo - Hide root packages
    // =========================================================================
    try {
        var PackageManager = Java.use("android.app.ApplicationPackageManager");

        PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pname, flags) {
            if (RootPackages.indexOf(pname) > -1) {
                console.log('[+] Hiding root package: ' + pname);
                pname = "com.nonexistent.package.fake";
            }
            return this.getPackageInfo(pname, flags);
        };
        console.log('[+] PackageManager.getPackageInfo bypass installed');
        bypassCount++;
    } catch(e) {
        console.log('[-] PackageManager bypass failed: ' + e);
    }

    // =========================================================================
    // File.exists - Hide root binaries/paths
    // =========================================================================
    try {
        var NativeFile = Java.use('java.io.File');

        NativeFile.exists.implementation = function() {
            var path = this.getAbsolutePath();
            var name = this.getName();

            // Check against binary names
            if (RootBinaries.indexOf(name) > -1) {
                console.log('[+] Hiding binary: ' + name);
                return false;
            }

            // Check against full paths
            for (var i = 0; i < RootPaths.length; i++) {
                if (path.indexOf(RootPaths[i]) > -1) {
                    console.log('[+] Hiding path: ' + path);
                    return false;
                }
            }

            return this.exists();
        };
        console.log('[+] File.exists bypass installed');
        bypassCount++;
    } catch(e) {
        console.log('[-] File.exists bypass failed: ' + e);
    }

    // =========================================================================
    // Runtime.exec - Block root-related commands
    // =========================================================================
    try {
        var Runtime = Java.use('java.lang.Runtime');

        var blockCommands = function(cmd) {
            if (typeof cmd === 'string') {
                if (cmd.indexOf("su") > -1 ||
                    cmd.indexOf("which") > -1 ||
                    cmd.indexOf("busybox") > -1 ||
                    cmd.indexOf("mount") > -1 ||
                    cmd.indexOf("/system") > -1) {
                    return true;
                }
            }
            return false;
        };

        Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
            if (blockCommands(cmd)) {
                console.log('[+] Blocking exec: ' + cmd);
                return Runtime.exec.call(this, "echo blocked");
            }
            return this.exec(cmd);
        };

        Runtime.exec.overload('[Ljava.lang.String;').implementation = function(cmdArray) {
            for (var i = 0; i < cmdArray.length; i++) {
                if (blockCommands(cmdArray[i])) {
                    console.log('[+] Blocking exec array: ' + cmdArray.join(' '));
                    return Runtime.exec.call(this, ["echo", "blocked"]);
                }
            }
            return this.exec(cmdArray);
        };
        console.log('[+] Runtime.exec bypass installed');
        bypassCount++;
    } catch(e) {
        console.log('[-] Runtime.exec bypass failed: ' + e);
    }

    // =========================================================================
    // ProcessBuilder - Block root commands
    // =========================================================================
    try {
        var ProcessBuilder = Java.use('java.lang.ProcessBuilder');

        ProcessBuilder.start.implementation = function() {
            var cmd = this.command();
            var cmdStr = '';
            for (var i = 0; i < cmd.size(); i++) {
                cmdStr += cmd.get(i) + ' ';
                var c = cmd.get(i).toString();
                if (c.indexOf("su") > -1 || c.indexOf("which") > -1 || c.indexOf("busybox") > -1) {
                    console.log('[+] Blocking ProcessBuilder: ' + cmdStr);
                    this.command(["echo", "blocked"]);
                    return this.start();
                }
            }
            return this.start();
        };
        console.log('[+] ProcessBuilder.start bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // SystemProperties.get - Spoof root-related properties
    // =========================================================================
    try {
        var SystemProperties = Java.use('android.os.SystemProperties');

        SystemProperties.get.overload('java.lang.String').implementation = function(name) {
            if (RootProperties.hasOwnProperty(name)) {
                console.log('[+] Spoofing property: ' + name + ' = ' + RootProperties[name]);
                return RootProperties[name];
            }
            return this.get(name);
        };

        SystemProperties.get.overload('java.lang.String', 'java.lang.String').implementation = function(name, def) {
            if (RootProperties.hasOwnProperty(name)) {
                console.log('[+] Spoofing property: ' + name + ' = ' + RootProperties[name]);
                return RootProperties[name];
            }
            return this.get(name, def);
        };
        console.log('[+] SystemProperties.get bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // String.contains - Block test-keys detection
    // =========================================================================
    try {
        var JavaString = Java.use('java.lang.String');

        JavaString.contains.implementation = function(seq) {
            if (seq === "test-keys") {
                console.log('[+] Blocking test-keys detection');
                return false;
            }
            return this.contains(seq);
        };
        console.log('[+] String.contains (test-keys) bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // Build.TAGS - Spoof to release-keys
    // =========================================================================
    try {
        var Build = Java.use('android.os.Build');
        var buildTags = Build.TAGS.value;

        if (buildTags && buildTags.indexOf("test-keys") > -1) {
            Build.TAGS.value = "release-keys";
            console.log('[+] Build.TAGS spoofed to release-keys');
            bypassCount++;
        }
    } catch(e) {}

    // =========================================================================
    // Native hooks - fopen, access, stat
    // =========================================================================
    try {
        Interceptor.attach(Module.findExportByName("libc.so", "fopen"), {
            onEnter: function(args) {
                var path = Memory.readCString(args[0]);
                for (var i = 0; i < RootBinaries.length; i++) {
                    if (path.indexOf(RootBinaries[i]) > -1) {
                        console.log('[+] Native fopen blocked: ' + path);
                        Memory.writeUtf8String(args[0], "/dev/null");
                        break;
                    }
                }
            }
        });
        console.log('[+] Native fopen bypass installed');
        bypassCount++;
    } catch(e) {}

    try {
        Interceptor.attach(Module.findExportByName("libc.so", "access"), {
            onEnter: function(args) {
                var path = Memory.readCString(args[0]);
                this.shouldBlock = false;
                for (var i = 0; i < RootPaths.length; i++) {
                    if (path.indexOf(RootPaths[i]) > -1) {
                        console.log('[+] Native access blocked: ' + path);
                        this.shouldBlock = true;
                        break;
                    }
                }
            },
            onLeave: function(retval) {
                if (this.shouldBlock) {
                    retval.replace(-1);
                }
            }
        });
        console.log('[+] Native access bypass installed');
        bypassCount++;
    } catch(e) {}

    // =========================================================================
    // SafetyNet Basic Bypass (limited effectiveness)
    // =========================================================================
    try {
        var SafetyNetClient = Java.use('com.google.android.gms.safetynet.SafetyNetClient');
        SafetyNetClient.attest.implementation = function(nonce, apiKey) {
            console.log('[!] SafetyNet attest called - basic bypass may not work');
            return this.attest(nonce, apiKey);
        };
        console.log('[+] SafetyNet attest hook installed (monitoring only)');
    } catch(e) {}

    // =========================================================================
    // Emulator Detection Bypass
    // =========================================================================
    try {
        var Build = Java.use('android.os.Build');

        // Common emulator fingerprints to hide
        var emulatorIndicators = {
            'FINGERPRINT': ['generic', 'unknown', 'google_sdk', 'emulator', 'Android SDK'],
            'MODEL': ['sdk', 'Emulator', 'Android SDK built for'],
            'MANUFACTURER': ['Genymotion', 'unknown'],
            'BRAND': ['generic', 'generic_x86'],
            'DEVICE': ['generic', 'generic_x86', 'vbox86p'],
            'PRODUCT': ['sdk', 'google_sdk', 'sdk_x86', 'vbox86p'],
            'HARDWARE': ['goldfish', 'ranchu', 'vbox86']
        };

        // Note: These are read-only fields, so we hook methods that read them instead
        // Hook TelephonyManager for IMEI checks
        try {
            var TelephonyManager = Java.use('android.telephony.TelephonyManager');

            TelephonyManager.getDeviceId.overload().implementation = function() {
                console.log('[+] Spoofing getDeviceId');
                return "358240051111110"; // Fake IMEI
            };

            TelephonyManager.getSubscriberId.implementation = function() {
                console.log('[+] Spoofing getSubscriberId');
                return "310260000000000"; // Fake IMSI
            };

            TelephonyManager.getLine1Number.implementation = function() {
                console.log('[+] Spoofing getLine1Number');
                return "+15551234567"; // Fake phone
            };

            TelephonyManager.getNetworkOperatorName.implementation = function() {
                console.log('[+] Spoofing getNetworkOperatorName');
                return "T-Mobile";
            };

            TelephonyManager.getSimOperatorName.implementation = function() {
                console.log('[+] Spoofing getSimOperatorName');
                return "T-Mobile";
            };
            console.log('[+] TelephonyManager emulator bypass installed');
            bypassCount++;
        } catch(e) {}

    } catch(e) {}

    console.log('');
    console.log('=====================================================');
    console.log('[#] Root/Emulator Bypass Summary: ' + bypassCount + ' hooks installed');
    console.log('=====================================================');
});
