/**
 * INTENTIONAL TEST ENDPOINTS
 *
 * These endpoints are intentionally included for testing
 * the Lêtô Hermes analysis toolkit's endpoint extraction.
 *
 * Mix of secure and insecure endpoints for testing.
 */

// Base URLs
export const API_BASE_URL = 'https://api.hermestest.local';
export const API_BASE_URL_V2 = 'https://api.hermestest.local/v2';
export const INSECURE_API_URL = 'http://insecure.hermestest.local'; // Intentionally HTTP

// REST API Endpoints
export const ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: `${API_BASE_URL}/v1/auth/login`,
    LOGOUT: `${API_BASE_URL}/v1/auth/logout`,
    REGISTER: `${API_BASE_URL}/v1/auth/register`,
    REFRESH: `${API_BASE_URL}/v1/auth/refresh`,
    FORGOT_PASSWORD: `${API_BASE_URL}/v1/auth/forgot-password`,
    RESET_PASSWORD: `${API_BASE_URL}/v1/auth/reset-password`,
    VERIFY_EMAIL: `${API_BASE_URL}/v1/auth/verify-email`,
    MFA_SETUP: `${API_BASE_URL}/v1/auth/mfa/setup`,
    MFA_VERIFY: `${API_BASE_URL}/v1/auth/mfa/verify`,
  },

  // User endpoints
  USERS: {
    PROFILE: `${API_BASE_URL}/v1/users/profile`,
    UPDATE: `${API_BASE_URL}/v1/users/update`,
    DELETE: `${API_BASE_URL}/v1/users/delete`,
    LIST: `${API_BASE_URL}/v1/users`,
    GET_BY_ID: `${API_BASE_URL}/v1/users/:id`,
    UPLOAD_AVATAR: `${API_BASE_URL}/v1/users/avatar`,
  },

  // Payment endpoints (sensitive)
  PAYMENTS: {
    CREATE_INTENT: `${API_BASE_URL}/v1/payments/intent`,
    CONFIRM: `${API_BASE_URL}/v1/payments/confirm`,
    HISTORY: `${API_BASE_URL}/v1/payments/history`,
    REFUND: `${API_BASE_URL}/v1/payments/refund`,
    CARDS: `${API_BASE_URL}/v1/payments/cards`,
    ADD_CARD: `${API_BASE_URL}/v1/payments/cards/add`,
  },

  // Data endpoints
  DATA: {
    SYNC: `${API_BASE_URL}/v1/data/sync`,
    EXPORT: `${API_BASE_URL}/v1/data/export`,
    IMPORT: `${API_BASE_URL}/v1/data/import`,
  },

  // Admin endpoints (should be protected)
  ADMIN: {
    DASHBOARD: `${API_BASE_URL}/v1/admin/dashboard`,
    USERS: `${API_BASE_URL}/v1/admin/users`,
    LOGS: `${API_BASE_URL}/v1/admin/logs`,
    CONFIG: `${API_BASE_URL}/v1/admin/config`,
  },

  // Debug endpoints (should not exist in production)
  DEBUG: {
    INFO: `${API_BASE_URL}/debug/info`,
    LOGS: `${API_BASE_URL}/debug/logs`,
    ENV: `${API_BASE_URL}/debug/env`,
    RESET: `${API_BASE_URL}/debug/reset`,
  },

  // Insecure endpoints (intentionally HTTP)
  INSECURE: {
    LEGACY: `${INSECURE_API_URL}/legacy/data`,
    OLD_API: `${INSECURE_API_URL}/api/v0/users`,
  },
};

// GraphQL endpoint
export const GRAPHQL_ENDPOINT = `${API_BASE_URL}/graphql`;
export const GRAPHQL_WS_ENDPOINT = 'wss://api.hermestest.local/graphql/subscriptions';

// WebSocket endpoints
export const WEBSOCKET_ENDPOINTS = {
  CHAT: 'wss://ws.hermestest.local/chat',
  NOTIFICATIONS: 'wss://ws.hermestest.local/notifications',
  REALTIME: 'wss://ws.hermestest.local/realtime',
};

// Third-party integrations
export const THIRD_PARTY = {
  ANALYTICS: 'https://analytics.hermestest.local/collect',
  CRASH_REPORTING: 'https://crashes.hermestest.local/report',
  FEATURE_FLAGS: 'https://flags.hermestest.local/api/flags',
  CDN: 'https://cdn.hermestest.local/assets',
};

// Internal/private endpoints
export const INTERNAL = {
  HEALTH_CHECK: `${API_BASE_URL}/internal/health`,
  METRICS: `${API_BASE_URL}/internal/metrics`,
  SERVICE_DISCOVERY: `${API_BASE_URL}/internal/services`,
};
