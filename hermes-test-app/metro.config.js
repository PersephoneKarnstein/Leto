const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

/**
 * Metro configuration with obfuscation for hardened build
 * https://facebook.github.io/metro/docs/configuration
 *
 * @type {import('metro-config').MetroConfig}
 */

// Only enable obfuscation for release builds
const enableObfuscation = process.env.OBFUSCATE === 'true';

let config = {};

if (enableObfuscation) {
  config = {
    transformer: {
      babelTransformerPath: require.resolve('react-native-obfuscating-transformer'),
      obfuscatorOptions: {
        // String protection
        stringArray: true,
        stringArrayEncoding: ['rc4'],
        stringArrayThreshold: 0.8,
        stringArrayRotate: true,
        stringArrayShuffle: true,
        stringArrayWrappersCount: 2,
        stringArrayWrappersType: 'function',

        // Control flow
        controlFlowFlattening: true,
        controlFlowFlatteningThreshold: 0.5,

        // Dead code injection
        deadCodeInjection: true,
        deadCodeInjectionThreshold: 0.3,

        // Identifier obfuscation
        identifierNamesGenerator: 'hexadecimal',
        renameGlobals: false,

        // Split strings
        splitStrings: true,
        splitStringsChunkLength: 5,

        // Disable console
        disableConsoleOutput: false,

        // Unicode escapes
        unicodeEscapeSequence: true,

        // Compact output
        compact: true,
        simplify: true,

        // Self-defending (anti-debugging)
        selfDefending: true,

        // Debug protection
        debugProtection: true,
        debugProtectionInterval: 2000,
      },
      // Only obfuscate app code, not node_modules
      obfuscatorSourceFilter: (filename) => {
        return filename.includes('/src/') ||
               filename.includes('App.tsx') ||
               filename.includes('secrets.ts') ||
               filename.includes('endpoints.ts');
      },
    },
  };
  console.log('🔒 Obfuscation ENABLED for release build');
} else {
  console.log('📝 Obfuscation disabled (set OBFUSCATE=true to enable)');
}

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
