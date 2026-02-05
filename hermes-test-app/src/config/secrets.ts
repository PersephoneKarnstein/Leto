/**
 * INTENTIONAL TEST SECRETS
 *
 * These are fake/expired secrets intentionally included for testing
 * the Lêtô Hermes analysis toolkit. DO NOT use in production.
 *
 * The toolkit should detect ALL of these during analysis.
 */

// API Keys (fake but realistic format)
export const API_KEY_STRIPE = 'sk_test_51ABC123XYZ789DEF456GHI000111222333';
export const API_KEY_INTERNAL = 'api_key_hermestest_abc123def456ghi789';
export const API_KEY_SENDGRID = 'SG.fake_sendgrid_key_for_testing_purposes';

// AWS Credentials (fake but correct format - AKIA prefix)
export const AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE';
export const AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';
export const AWS_REGION = 'us-east-1';

// Firebase Configuration (fake project)
export const FIREBASE_CONFIG = {
  apiKey: 'AIzaSyA1B2C3D4E5F6G7H8I9J0-hermestest',
  authDomain: 'hermestest-fake.firebaseapp.com',
  projectId: 'hermestest-fake',
  storageBucket: 'hermestest-fake.appspot.com',
  messagingSenderId: '123456789012',
  appId: '1:123456789012:android:abc123def456',
};

// JWT Tokens (expired/fake - safe to include)
export const JWT_ACCESS_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidGVzdCI6Imhlcm1lcyIsImlhdCI6MTUxNjIzOTAyMn0.fake_signature_for_testing';
export const JWT_REFRESH_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE1MTYyMzkwMjJ9.fake_refresh_signature';

// OAuth Credentials (fake)
export const OAUTH_CLIENT_ID = 'hermestest-oauth-client-id-12345.apps.googleusercontent.com';
export const OAUTH_CLIENT_SECRET = 'GOCSPX-fake_oauth_secret_for_testing';

// Database Credentials (fake)
export const DATABASE_URL = 'postgresql://admin:SuperSecretPassword123!@db.hermestest.local:5432/testdb';
export const MONGODB_URI = 'mongodb+srv://admin:AnotherSecret456@cluster.hermestest.mongodb.net/testdb';
export const REDIS_URL = 'redis://:redis_password_789@cache.hermestest.local:6379';

// Encryption Keys (fake)
export const ENCRYPTION_KEY = 'aes256_encryption_key_0123456789abcdef';
export const HMAC_SECRET = 'hmac_secret_key_for_signing_requests_12345';

// Private Key (fake RSA header - truncated for safety)
export const PRIVATE_KEY_PEM = `-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBALRiMLAHudeSA2FAKE_KEY_FOR_TESTING_PURPOSES_ONLY
NOT_A_REAL_KEY_JUST_FOR_DETECTION_TESTING_1234567890abcdefghij
ANOTHER_LINE_OF_FAKE_KEY_DATA_klmnopqrstuvwxyz0123456789ABCDEF
-----END RSA PRIVATE KEY-----`;

// Password Hash (MD5 of "password" - for testing)
export const PASSWORD_HASH_MD5 = '5f4dcc3b5aa765d61d8327deb882cf99';
export const PASSWORD_HASH_SHA256 = '5e884898da28047d9178e7d6dab5d5c97da91c2e73d35b42b0e6fbf80f26a6e3';

// Misc Secrets
export const SLACK_WEBHOOK = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX';
export const TWILIO_AUTH_TOKEN = 'fake_twilio_auth_token_32chars_abc';
export const GITHUB_TOKEN = 'ghp_fake1234567890ABCDEFghijklmnopqrstuv';

// Debug/Internal Values
export const DEBUG_MODE = true;
export const INTERNAL_ADMIN_PASSWORD = 'admin123!@#';
export const BYPASS_AUTH_CODE = 'BYPASS_2024_TEST';
