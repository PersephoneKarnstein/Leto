/**
 * Anti-Tampering Protection Module
 *
 * This module demonstrates common anti-tampering techniques
 * used to protect React Native apps. These are intentionally
 * included to test the toolkit's bypass capabilities.
 *
 * DO NOT USE IN PRODUCTION - This is for testing purposes only.
 */

import {NativeModules, Platform} from 'react-native';

// Obfuscated check names to make static analysis harder
const _0x4a8f = ['frida', 'substrate', 'xposed', 'magisk', 'supersu'];
const _0x9c2e = ['debugger', 'debug_mode', 'developer'];

/**
 * Check for common root/jailbreak indicators
 */
export const checkRootStatus = (): boolean => {
  try {
    if (Platform.OS === 'android') {
      // Check for root binaries
      const rootPaths = [
        '/system/bin/su',
        '/system/xbin/su',
        '/sbin/su',
        '/data/local/xbin/su',
        '/data/local/bin/su',
        '/system/sd/xbin/su',
        '/system/bin/failsafe/su',
        '/data/local/su',
        '/su/bin/su',
        '/data/adb/magisk',
      ];

      // Check for root management apps
      const rootApps = [
        'com.topjohnwu.magisk',
        'eu.chainfire.supersu',
        'com.koushikdutta.superuser',
        'com.noshufou.android.su',
        'com.thirdparty.superuser',
        'com.yellowes.su',
      ];

      // These would be native checks in a real app
      console.log('[AntiTamper] Root check performed');
      return false;
    }
    return false;
  } catch (e) {
    return true; // Assume rooted if check fails
  }
};

/**
 * Check for Frida instrumentation
 */
export const checkFridaPresence = (): boolean => {
  try {
    // Check for Frida-specific artifacts
    const fridaIndicators = [
      'frida-server',
      'frida-agent',
      'frida-gadget',
      'linjector',
    ];

    // Check for Frida ports (27042, 27043)
    const fridaPorts = [27042, 27043];

    // Check for Frida-specific memory patterns
    const fridaSignatures = [
      'LIBFRIDA',
      'frida:rpc',
      'gum-js-loop',
    ];

    // String-based detection (easily bypassed)
    const globalCheck = typeof (global as any).frida !== 'undefined';
    const hooksCheck = typeof (global as any).__frida__ !== 'undefined';

    console.log('[AntiTamper] Frida detection performed');
    return globalCheck || hooksCheck;
  } catch (e) {
    return false;
  }
};

/**
 * Check for debugging
 */
export const checkDebuggerAttached = (): boolean => {
  try {
    // Check __DEV__ flag
    if (__DEV__) {
      return true;
    }

    // Timing-based detection
    const start = Date.now();
    // Debugger breakpoint would cause delay
    const elapsed = Date.now() - start;
    if (elapsed > 100) {
      return true;
    }

    console.log('[AntiTamper] Debugger check performed');
    return false;
  } catch (e) {
    return true;
  }
};

/**
 * Check for emulator
 */
export const checkEmulator = (): boolean => {
  try {
    if (Platform.OS === 'android') {
      // Check for emulator fingerprints
      const emulatorIndicators = [
        'goldfish',
        'ranchu',
        'sdk_gphone',
        'generic',
        'vbox86',
        'ttVM_Hdragon',
        'andy',
        'nox',
        'bluestacks',
      ];

      // Check build properties (would be native)
      console.log('[AntiTamper] Emulator check performed');
      return false;
    }
    return false;
  } catch (e) {
    return false;
  }
};

/**
 * Verify app integrity
 */
export const checkIntegrity = (): boolean => {
  try {
    // In a real app, this would:
    // 1. Verify APK signature
    // 2. Check package name
    // 3. Verify certificate hash
    // 4. Check for repackaging

    const expectedPackage = 'com.hermestestapp';
    const expectedSignature = 'SHA256:AB:CD:EF:...'; // Truncated for demo

    // Checksum of critical files
    const bundleChecksum = 'expected_checksum_here';

    console.log('[AntiTamper] Integrity check performed');
    return true;
  } catch (e) {
    return false;
  }
};

/**
 * Check for hooking frameworks (Xposed, etc.)
 */
export const checkHookingFrameworks = (): boolean => {
  try {
    // Check for Xposed
    const xposedIndicators = [
      'de.robv.android.xposed.installer',
      'de.robv.android.xposed',
      'io.va.exposed',
      'com.saurik.substrate',
    ];

    // Check for modified system libraries
    const systemLibs = [
      '/system/lib/libxposed_art.so',
      '/system/lib/libsubstrate.so',
      '/system/lib/libsubstrate-dvm.so',
    ];

    // Stack trace analysis (looking for Xposed frames)
    const stackTrace = new Error().stack || '';
    const suspiciousFrames = _0x4a8f.some(
      indicator => stackTrace.toLowerCase().includes(indicator)
    );

    console.log('[AntiTamper] Hooking framework check performed');
    return suspiciousFrames;
  } catch (e) {
    return false;
  }
};

/**
 * SSL Certificate Pinning Configuration
 */
export const SSL_PINS = {
  'api.hermestest.local': [
    'sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',
    'sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=',
  ],
  'ws.hermestest.local': [
    'sha256/CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=',
  ],
};

/**
 * Run all security checks
 */
export const performSecurityChecks = (): {
  passed: boolean;
  details: Record<string, boolean>;
} => {
  const results = {
    root: !checkRootStatus(),
    frida: !checkFridaPresence(),
    debugger: !checkDebuggerAttached(),
    emulator: !checkEmulator(),
    integrity: checkIntegrity(),
    hooks: !checkHookingFrameworks(),
  };

  const passed = Object.values(results).every(v => v);

  console.log('[AntiTamper] Security check results:', results);

  return {passed, details: results};
};

/**
 * Encrypted storage for sensitive data
 * In a real app, this would use platform-specific secure storage
 */
export const SecureStorage = {
  // XOR-based "encryption" (intentionally weak for testing)
  _xorKey: 0x42,

  encrypt: (data: string): string => {
    return data
      .split('')
      .map(c => String.fromCharCode(c.charCodeAt(0) ^ 0x42))
      .join('');
  },

  decrypt: (data: string): string => {
    return data
      .split('')
      .map(c => String.fromCharCode(c.charCodeAt(0) ^ 0x42))
      .join('');
  },

  // Obfuscated API key retrieval
  getApiKey: (): string => {
    // Base64 encoded then XOR'd key
    const encoded = 'cWsndGUqYiQxQUJDMTIzWFlaLi4u';
    return SecureStorage.decrypt(atob(encoded));
  },
};

export default {
  checkRootStatus,
  checkFridaPresence,
  checkDebuggerAttached,
  checkEmulator,
  checkIntegrity,
  checkHookingFrameworks,
  performSecurityChecks,
  SSL_PINS,
  SecureStorage,
};
