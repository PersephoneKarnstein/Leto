/**
 * iOS SSL Pinning Bypass
 *
 * Covers:
 * - NSURLSession TLS settings
 * - TrustKit pinning validation
 * - AFNetworking SSL pinning mode
 * - Alamofire ServerTrustManager
 * - SecTrust evaluation functions
 * - Custom URLSessionDelegate implementations
 *
 * Usage:
 *   frida -U -f com.target.app -l ios_ssl_bypass.js
 *
 * Based on techniques from:
 * - https://codeshare.frida.re/@snooze6/ios-pinning-disable/
 * - OWASP MASTG iOS SSL Pinning Bypass
 */

if (ObjC.available) {
    console.log("[*] iOS SSL Pinning Bypass loaded");
    console.log("[*] Objective-C runtime available");

    // ============================================
    // TrustKit Bypass
    // ============================================
    try {
        var TrustKit = ObjC.classes.TrustKit;
        if (TrustKit) {
            console.log("[*] TrustKit detected");

            var TSKPinningValidator = ObjC.classes.TSKPinningValidator;
            if (TSKPinningValidator) {
                Interceptor.attach(TSKPinningValidator['- evaluateTrust:forHostname:'].implementation, {
                    onLeave: function(retval) {
                        console.log("[+] TrustKit evaluateTrust bypassed");
                        retval.replace(0); // TSKTrustDecisionShouldAllowConnection
                    }
                });
            }

            var TSKPinningValidatorResult = ObjC.classes.TSKPinningValidatorResult;
            if (TSKPinningValidatorResult) {
                Interceptor.attach(TSKPinningValidatorResult['- finalTrustDecision'].implementation, {
                    onLeave: function(retval) {
                        console.log("[+] TrustKit finalTrustDecision bypassed");
                        retval.replace(0);
                    }
                });
            }
        }
    } catch(e) {
        console.log("[-] TrustKit not found or error: " + e.message);
    }

    // ============================================
    // AFNetworking Bypass
    // ============================================
    try {
        var AFSecurityPolicy = ObjC.classes.AFSecurityPolicy;
        if (AFSecurityPolicy) {
            console.log("[*] AFNetworking detected");

            Interceptor.attach(AFSecurityPolicy['- setSSLPinningMode:'].implementation, {
                onEnter: function(args) {
                    console.log("[+] AFNetworking setSSLPinningMode -> None");
                    args[2] = ptr(0); // AFSSLPinningModeNone
                }
            });

            Interceptor.attach(AFSecurityPolicy['- setAllowInvalidCertificates:'].implementation, {
                onEnter: function(args) {
                    console.log("[+] AFNetworking setAllowInvalidCertificates -> YES");
                    args[2] = ptr(1);
                }
            });

            Interceptor.attach(AFSecurityPolicy['- evaluateServerTrust:forDomain:'].implementation, {
                onLeave: function(retval) {
                    console.log("[+] AFNetworking evaluateServerTrust bypassed");
                    retval.replace(1);
                }
            });
        }
    } catch(e) {
        console.log("[-] AFNetworking not found or error: " + e.message);
    }

    // ============================================
    // Alamofire Bypass (Swift)
    // ============================================
    try {
        var ServerTrustManager = ObjC.classes.Alamofire_ServerTrustManager ||
                                  ObjC.classes["Alamofire.ServerTrustManager"];
        if (ServerTrustManager) {
            console.log("[*] Alamofire detected");
            // Alamofire uses Swift, hooks may need adjustment per version
        }
    } catch(e) {
        // Alamofire not present
    }

    // ============================================
    // NSURLSession Delegate Bypass
    // ============================================
    try {
        // Hook URLSession:didReceiveChallenge:completionHandler:
        var NSURLSessionDelegate = ObjC.protocols.NSURLSessionDelegate;

        // Find all classes implementing URLSession delegate
        ObjC.enumerateLoadedClasses({
            onMatch: function(className) {
                try {
                    var cls = ObjC.classes[className];
                    if (cls && cls['- URLSession:didReceiveChallenge:completionHandler:']) {
                        Interceptor.attach(cls['- URLSession:didReceiveChallenge:completionHandler:'].implementation, {
                            onEnter: function(args) {
                                var challenge = ObjC.Object(args[3]);
                                var host = challenge.protectionSpace().host().toString();
                                console.log("[+] URLSession challenge for: " + host);

                                // Get completionHandler and call with UseCredential
                                var completionHandler = new ObjC.Block(args[4]);
                                var credential = ObjC.classes.NSURLCredential.credentialForTrust_(
                                    challenge.protectionSpace().serverTrust()
                                );
                                completionHandler.implementation(0, credential); // NSURLSessionAuthChallengeUseCredential
                            }
                        });
                        console.log("[+] Hooked delegate: " + className);
                    }
                } catch(e) {}
            },
            onComplete: function() {}
        });
    } catch(e) {
        console.log("[-] NSURLSession delegate hook error: " + e.message);
    }

    // ============================================
    // SecTrust Functions Bypass
    // ============================================
    try {
        // SecTrustEvaluateWithError (iOS 12+)
        var SecTrustEvaluateWithError = Module.findExportByName("Security", "SecTrustEvaluateWithError");
        if (SecTrustEvaluateWithError) {
            Interceptor.attach(SecTrustEvaluateWithError, {
                onLeave: function(retval) {
                    console.log("[+] SecTrustEvaluateWithError -> true");
                    retval.replace(1);
                }
            });
        }

        // SecTrustEvaluate (deprecated but still used)
        var SecTrustEvaluate = Module.findExportByName("Security", "SecTrustEvaluate");
        if (SecTrustEvaluate) {
            Interceptor.attach(SecTrustEvaluate, {
                onLeave: function(retval) {
                    console.log("[+] SecTrustEvaluate -> success");
                    retval.replace(0); // errSecSuccess
                }
            });
        }

        // SecTrustGetTrustResult
        var SecTrustGetTrustResult = Module.findExportByName("Security", "SecTrustGetTrustResult");
        if (SecTrustGetTrustResult) {
            Interceptor.attach(SecTrustGetTrustResult, {
                onLeave: function(retval) {
                    // Set result to kSecTrustResultProceed
                    if (this.context && this.context.x1) {
                        Memory.writeU32(this.context.x1, 1);
                    }
                    retval.replace(0);
                }
            });
        }

        console.log("[+] SecTrust hooks installed");
    } catch(e) {
        console.log("[-] SecTrust hook error: " + e.message);
    }

    // ============================================
    // SSL_CTX Bypass (for apps using OpenSSL directly)
    // ============================================
    try {
        var SSL_CTX_set_verify = Module.findExportByName(null, "SSL_CTX_set_verify");
        if (SSL_CTX_set_verify) {
            Interceptor.attach(SSL_CTX_set_verify, {
                onEnter: function(args) {
                    console.log("[+] SSL_CTX_set_verify -> SSL_VERIFY_NONE");
                    args[1] = ptr(0); // SSL_VERIFY_NONE
                }
            });
        }

        var SSL_set_verify = Module.findExportByName(null, "SSL_set_verify");
        if (SSL_set_verify) {
            Interceptor.attach(SSL_set_verify, {
                onEnter: function(args) {
                    console.log("[+] SSL_set_verify -> SSL_VERIFY_NONE");
                    args[1] = ptr(0);
                }
            });
        }
    } catch(e) {
        // OpenSSL not used directly
    }

    console.log("[*] iOS SSL bypass hooks installed");
    console.log("[*] Intercepting HTTPS traffic should now work");

} else {
    console.log("[-] Objective-C runtime not available");
    console.log("[-] This script is for iOS only");
}
