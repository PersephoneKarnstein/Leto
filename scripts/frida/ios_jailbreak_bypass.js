/**
 * iOS Jailbreak Detection Bypass
 *
 * Covers:
 * - File existence checks (Cydia, Sileo, ssh, etc.)
 * - URL scheme checks (cydia://, sileo://)
 * - Fork/sandbox checks
 * - Dylib injection checks
 * - System call hooks
 *
 * Usage:
 *   frida -U -f com.target.app -l ios_jailbreak_bypass.js
 *
 * Based on techniques from:
 * - https://codeshare.frida.re/@DevTraleski/ios-jailbreak-detection-bypass-palera1n/
 * - OWASP MASTG Jailbreak Detection Bypass
 */

if (ObjC.available) {
    console.log("[*] iOS Jailbreak Detection Bypass loaded");

    // ============================================
    // Common jailbreak file paths
    // ============================================
    var jailbreakPaths = [
        // Jailbreak apps
        "/Applications/Cydia.app",
        "/Applications/Sileo.app",
        "/Applications/Zebra.app",
        "/Applications/Installer.app",
        "/Applications/Unc0ver.app",
        "/Applications/checkra1n.app",
        "/Applications/blackb0x.app",
        "/Applications/FakeCarrier.app",
        "/Applications/MxTube.app",
        "/Applications/RockApp.app",
        "/Applications/SBSettings.app",
        "/Applications/WinterBoard.app",

        // SSH and shell
        "/usr/sbin/sshd",
        "/usr/bin/ssh",
        "/usr/bin/sshd",
        "/bin/bash",
        "/bin/sh",
        "/usr/libexec/ssh-keysign",
        "/usr/libexec/sftp-server",

        // Package managers
        "/etc/apt",
        "/etc/apt/sources.list.d",
        "/private/var/lib/apt",
        "/private/var/lib/apt/",
        "/private/var/lib/cydia",
        "/private/var/mobile/Library/Cydia",
        "/private/var/stash",
        "/var/lib/dpkg/info",

        // Jailbreak-specific paths
        "/var/jb",
        "/var/jb/",
        "/private/var/jb",
        "/usr/lib/TweakInject",
        "/Library/MobileSubstrate",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/Library/MobileSubstrate/DynamicLibraries",
        "/var/mobile/Library/SBSettings/Themes",

        // Substrate/Substitute
        "/usr/lib/libsubstrate.dylib",
        "/usr/lib/substrate",
        "/usr/lib/libsubstitute.dylib",
        "/usr/lib/substitute-loader.dylib",

        // Cydia files
        "/private/var/cache/apt/",
        "/private/var/log/syslog",
        "/private/var/tmp/cydia.log",
        "/System/Library/LaunchDaemons/com.ikey.bbot.plist",
        "/System/Library/LaunchDaemons/com.saurik.Cydia.Startup.plist",

        // Other
        "/private/etc/dpkg/origins/debian",
        "/jb/lzma",
        "/.cydia_no_stash",
        "/.installed_unc0ver",
        "/usr/bin/cycript"
    ];

    // ============================================
    // NSFileManager hooks
    // ============================================
    try {
        var NSFileManager = ObjC.classes.NSFileManager;

        // fileExistsAtPath:
        Interceptor.attach(NSFileManager['- fileExistsAtPath:'].implementation, {
            onEnter: function(args) {
                this.path = ObjC.Object(args[2]).toString();
            },
            onLeave: function(retval) {
                if (this.path) {
                    for (var i = 0; i < jailbreakPaths.length; i++) {
                        if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                            console.log("[+] Blocked fileExistsAtPath: " + this.path);
                            retval.replace(0);
                            return;
                        }
                    }
                }
            }
        });

        // fileExistsAtPath:isDirectory:
        Interceptor.attach(NSFileManager['- fileExistsAtPath:isDirectory:'].implementation, {
            onEnter: function(args) {
                this.path = ObjC.Object(args[2]).toString();
            },
            onLeave: function(retval) {
                if (this.path) {
                    for (var i = 0; i < jailbreakPaths.length; i++) {
                        if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                            console.log("[+] Blocked fileExistsAtPath:isDirectory: " + this.path);
                            retval.replace(0);
                            return;
                        }
                    }
                }
            }
        });

        console.log("[+] NSFileManager hooks installed");
    } catch(e) {
        console.log("[-] NSFileManager hook error: " + e.message);
    }

    // ============================================
    // UIApplication canOpenURL: hook
    // ============================================
    try {
        var UIApplication = ObjC.classes.UIApplication;
        Interceptor.attach(UIApplication['- canOpenURL:'].implementation, {
            onEnter: function(args) {
                this.url = ObjC.Object(args[2]).toString();
            },
            onLeave: function(retval) {
                if (this.url) {
                    var blockedSchemes = ["cydia://", "sileo://", "zbra://", "filza://", "undecimus://"];
                    for (var i = 0; i < blockedSchemes.length; i++) {
                        if (this.url.indexOf(blockedSchemes[i]) !== -1) {
                            console.log("[+] Blocked canOpenURL: " + this.url);
                            retval.replace(0);
                            return;
                        }
                    }
                }
            }
        });
        console.log("[+] UIApplication canOpenURL hook installed");
    } catch(e) {
        console.log("[-] canOpenURL hook error: " + e.message);
    }

    // ============================================
    // C function hooks
    // ============================================

    // stat/lstat - file existence check
    try {
        var stat = Module.findExportByName(null, "stat");
        if (stat) {
            Interceptor.attach(stat, {
                onEnter: function(args) {
                    this.path = args[0].readUtf8String();
                },
                onLeave: function(retval) {
                    if (this.path) {
                        for (var i = 0; i < jailbreakPaths.length; i++) {
                            if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                                console.log("[+] Blocked stat: " + this.path);
                                retval.replace(-1);
                                return;
                            }
                        }
                    }
                }
            });
        }

        var lstat = Module.findExportByName(null, "lstat");
        if (lstat) {
            Interceptor.attach(lstat, {
                onEnter: function(args) {
                    this.path = args[0].readUtf8String();
                },
                onLeave: function(retval) {
                    if (this.path) {
                        for (var i = 0; i < jailbreakPaths.length; i++) {
                            if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                                console.log("[+] Blocked lstat: " + this.path);
                                retval.replace(-1);
                                return;
                            }
                        }
                    }
                }
            });
        }
        console.log("[+] stat/lstat hooks installed");
    } catch(e) {
        console.log("[-] stat hook error: " + e.message);
    }

    // access() - file access check
    try {
        var access = Module.findExportByName(null, "access");
        if (access) {
            Interceptor.attach(access, {
                onEnter: function(args) {
                    this.path = args[0].readUtf8String();
                },
                onLeave: function(retval) {
                    if (this.path) {
                        for (var i = 0; i < jailbreakPaths.length; i++) {
                            if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                                console.log("[+] Blocked access: " + this.path);
                                retval.replace(-1);
                                return;
                            }
                        }
                    }
                }
            });
        }
        console.log("[+] access hook installed");
    } catch(e) {
        console.log("[-] access hook error: " + e.message);
    }

    // fopen() - file open check
    try {
        var fopen = Module.findExportByName(null, "fopen");
        if (fopen) {
            Interceptor.attach(fopen, {
                onEnter: function(args) {
                    this.path = args[0].readUtf8String();
                },
                onLeave: function(retval) {
                    if (this.path) {
                        for (var i = 0; i < jailbreakPaths.length; i++) {
                            if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                                console.log("[+] Blocked fopen: " + this.path);
                                retval.replace(ptr(0));
                                return;
                            }
                        }
                    }
                }
            });
        }
        console.log("[+] fopen hook installed");
    } catch(e) {
        console.log("[-] fopen hook error: " + e.message);
    }

    // fork() - sandbox escape check
    try {
        var fork = Module.findExportByName(null, "fork");
        if (fork) {
            Interceptor.attach(fork, {
                onLeave: function(retval) {
                    console.log("[+] fork() blocked");
                    retval.replace(-1);
                }
            });
        }
        console.log("[+] fork hook installed");
    } catch(e) {
        console.log("[-] fork hook error: " + e.message);
    }

    // system() - command execution check
    try {
        var system = Module.findExportByName(null, "system");
        if (system) {
            Interceptor.attach(system, {
                onEnter: function(args) {
                    var cmd = args[0].readUtf8String();
                    console.log("[!] system() called: " + cmd);
                },
                onLeave: function(retval) {
                    retval.replace(-1);
                }
            });
        }
    } catch(e) {}

    // ============================================
    // dyld hooks (detect injected libraries)
    // ============================================
    try {
        var _dyld_get_image_name = Module.findExportByName(null, "_dyld_get_image_name");
        if (_dyld_get_image_name) {
            Interceptor.attach(_dyld_get_image_name, {
                onLeave: function(retval) {
                    var name = retval.readUtf8String();
                    if (name) {
                        var blockedLibs = ["substrate", "substitute", "frida", "cycript", "SSLKillSwitch"];
                        for (var i = 0; i < blockedLibs.length; i++) {
                            if (name.toLowerCase().indexOf(blockedLibs[i].toLowerCase()) !== -1) {
                                console.log("[+] Hiding dylib: " + name);
                                retval.replace(ptr(0));
                                return;
                            }
                        }
                    }
                }
            });
        }
    } catch(e) {}

    console.log("[*] iOS jailbreak detection bypass installed");
    console.log("[*] App should now run on jailbroken device");

} else {
    console.log("[-] Objective-C runtime not available");
    console.log("[-] This script is for iOS only");
}
