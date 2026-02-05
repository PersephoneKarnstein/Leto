/**
 * INTENTIONAL TEST SECRETS - HARDENED VERSION
 *
 * These are fake/expired secrets with additional obfuscation
 * techniques applied for testing the Lêtô analysis toolkit.
 *
 * Techniques used:
 * - String splitting
 * - Base64 encoding
 * - Character code arrays
 * - Concatenation at runtime
 * - Hex encoding
 *
 * DO NOT USE IN PRODUCTION.
 */

// String utilities for obfuscation
const _0xd3c4 = (arr: number[]): string => String.fromCharCode(...arr);
const _0xa1b2 = (hex: string): string =>
  hex.match(/.{2}/g)?.map(b => String.fromCharCode(parseInt(b, 16))).join('') || '';
const _0xf5e6 = (b64: string): string => {
  try { return atob(b64); } catch { return b64; }
};

// Split strings that get joined at runtime
const _p1 = 'sk_test_';
const _p2 = '51ABC123XYZ789DEF456';
const _p3 = 'GHI000111222333';

// API Keys (fake but realistic format)
export const API_KEY_STRIPE = _p1 + _p2 + _p3;
export const API_KEY_INTERNAL = ['api', '_key_', 'hermestest', '_abc123', 'def456', 'ghi789'].join('');
export const API_KEY_SENDGRID = _0xf5e6('U0cuZmFrZV9zZW5kZ3JpZF9rZXlfZm9yX3Rlc3RpbmdfcHVycG9zZXM=');

// AWS Credentials - character code array
const _aws_key_codes = [65,75,73,65,73,79,83,70,79,68,78,78,55,69,88,65,77,80,76,69];
export const AWS_ACCESS_KEY_ID = _0xd3c4(_aws_key_codes);
export const AWS_SECRET_ACCESS_KEY = _0xf5e6('d0phbHJYVXRuRkVNSS9LN01ERU5HL2JQeFJmaUNZRVhBTVBMRUtFWQ==');
export const AWS_REGION = 'us-' + 'east-' + '1';

// Firebase Configuration (hex encoded api key)
const _fb_key_hex = '41497a6153794131423243334434453546364737483849394a302d6865726d6573746573742d66616b652e617070';
export const FIREBASE_CONFIG = {
  apiKey: _0xa1b2(_fb_key_hex).slice(0, 43),
  authDomain: ['hermestest', '-fake', '.firebase', 'app.com'].join(''),
  projectId: 'hermestest' + '-' + 'fake',
  storageBucket: `${'hermestest'}-${'fake'}.${'appspot'}.com`,
  messagingSenderId: String(123456789012),
  appId: '1:123456789012:android:' + 'abc123def456',
};

// JWT Tokens - split across multiple variables
const _jwt_header = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';
const _jwt_payload_1 = 'eyJzdWIiOiIxMjM0NTY3ODkwIiwidGVzdCI6Imhlcm1lcyIsImlhdCI6MTUxNjIzOTAyMn0';
const _jwt_payload_2 = 'eyJzdWIiOiIxMjM0NTY3ODkwIiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE1MTYyMzkwMjJ9';
const _jwt_sig_1 = 'fake_signature_for_testing';
const _jwt_sig_2 = 'fake_refresh_signature';

export const JWT_ACCESS_TOKEN = [_jwt_header, _jwt_payload_1, _jwt_sig_1].join('.');
export const JWT_REFRESH_TOKEN = [_jwt_header, _jwt_payload_2, _jwt_sig_2].join('.');

// OAuth Credentials - mixed obfuscation
const _oauth_parts = {
  prefix: 'hermestest-oauth-client-id-',
  id: '12345',
  suffix: '.apps.googleusercontent.com',
};
export const OAUTH_CLIENT_ID = _oauth_parts.prefix + _oauth_parts.id + _oauth_parts.suffix;
export const OAUTH_CLIENT_SECRET = _0xf5e6('R09DU1BYLWZha2Vfb2F1dGhfc2VjcmV0X2Zvcl90ZXN0aW5n');

// Database Credentials - template literals with splits
const _db = {proto: 'postgresql', user: 'admin', pass: 'SuperSecretPassword123!', host: 'db.hermestest.local', port: 5432, name: 'testdb'};
export const DATABASE_URL = `${_db.proto}://${_db.user}:${_db.pass}@${_db.host}:${_db.port}/${_db.name}`;

const _mongo = {user: 'admin', pass: 'AnotherSecret456', cluster: 'cluster.hermestest.mongodb.net', db: 'testdb'};
export const MONGODB_URI = `mongodb+srv://${_mongo.user}:${_mongo.pass}@${_mongo.cluster}/${_mongo.db}`;

const _redis = {pass: 'redis_password_789', host: 'cache.hermestest.local', port: 6379};
export const REDIS_URL = `redis://:${_redis.pass}@${_redis.host}:${_redis.port}`;

// Encryption Keys - hex encoded
export const ENCRYPTION_KEY = _0xa1b2('616573323536') + '_encryption_key_' + '0123456789abcdef';
export const HMAC_SECRET = ['hmac', '_secret', '_key', '_for', '_signing', '_requests', '_12345'].join('');

// Private Key - split lines
const _pem_start = '-----BEGIN RSA PRIVATE KEY-----';
const _pem_body_1 = 'MIIBOgIBAAJBALRiMLAHudeSA2FAKE_KEY_FOR_TESTING_PURPOSES_ONLY';
const _pem_body_2 = 'NOT_A_REAL_KEY_JUST_FOR_DETECTION_TESTING_1234567890abcdefghij';
const _pem_body_3 = 'ANOTHER_LINE_OF_FAKE_KEY_DATA_klmnopqrstuvwxyz0123456789ABCDEF';
const _pem_end = '-----END RSA PRIVATE KEY-----';
export const PRIVATE_KEY_PEM = [_pem_start, _pem_body_1, _pem_body_2, _pem_body_3, _pem_end].join('\n');

// Password Hashes - computed at build time (simulated)
export const PASSWORD_HASH_MD5 = ['5f4dcc3b', '5aa765d6', '1d8327de', 'b882cf99'].join('');
export const PASSWORD_HASH_SHA256 = [
  '5e884898', 'da28047d', '9178e7d6', 'dab5d5c9',
  '7da91c2e', '73d35b42', 'b0e6fbf8', '0f26a6e3'
].join('');

// Misc Secrets - various encodings
export const SLACK_WEBHOOK = _0xf5e6('aHR0cHM6Ly9ob29rcy5zbGFjay5jb20vc2VydmljZXMvVDAwMDAwMDAwL0IwMDAwMDAwMC9YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFg=');
export const TWILIO_AUTH_TOKEN = 'fake_twilio_auth_token_' + '32chars_abc';
export const GITHUB_TOKEN = 'ghp_' + _0xf5e6('ZmFrZTEyMzQ1Njc4OTBBQ0RFRmdoaWprbG1ub3BxcnN0dXY=');

// Debug/Internal Values - obfuscated names
const _0x8f2a = { m: true, p: 'admin123!@#', c: 'BYPASS_2024_TEST' };
export const DEBUG_MODE = _0x8f2a.m;
export const INTERNAL_ADMIN_PASSWORD = _0x8f2a.p;
export const BYPASS_AUTH_CODE = _0x8f2a.c;

// Additional obfuscated secrets for detection testing
export const SECURE_API_URL = (() => {
  const parts = ['https://', 'secure', '.api.', 'hermestest', '.local'];
  return parts.reduce((acc, p) => acc + p, '');
})();

// Runtime-computed credential (IIFE pattern)
export const DYNAMIC_TOKEN = (() => {
  const chars = 'DYN_TOKEN_'.split('');
  const suffix = Array.from({length: 20}, (_, i) => String.fromCharCode(65 + (i % 26)));
  return chars.join('') + suffix.join('');
})();
