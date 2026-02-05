/**
 * API Service
 *
 * Demonstrates various API patterns for testing toolkit detection.
 */

import {
  API_KEY_INTERNAL,
  JWT_ACCESS_TOKEN,
  AWS_ACCESS_KEY_ID,
  AWS_SECRET_ACCESS_KEY,
} from '../config/secrets';
import {ENDPOINTS, GRAPHQL_ENDPOINT} from '../config/endpoints';

// Headers with secrets (intentional for testing)
const getAuthHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${JWT_ACCESS_TOKEN}`,
  'X-API-Key': API_KEY_INTERNAL,
  'X-AWS-Access-Key': AWS_ACCESS_KEY_ID, // Bad practice - intentional
});

// REST API calls
export const api = {
  // Auth
  async login(email: string, password: string) {
    const response = await fetch(ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password}),
    });
    return response.json();
  },

  async logout() {
    const response = await fetch(ENDPOINTS.AUTH.LOGOUT, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return response.json();
  },

  // User
  async getProfile() {
    const response = await fetch(ENDPOINTS.USERS.PROFILE, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    return response.json();
  },

  async updateProfile(data: object) {
    const response = await fetch(ENDPOINTS.USERS.UPDATE, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Payments
  async createPaymentIntent(amount: number, currency: string) {
    const response = await fetch(ENDPOINTS.PAYMENTS.CREATE_INTENT, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({amount, currency}),
    });
    return response.json();
  },

  // Admin (intentional sensitive endpoint)
  async getAdminDashboard() {
    const response = await fetch(ENDPOINTS.ADMIN.DASHBOARD, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'X-Admin-Secret': 'admin_bypass_token_12345', // Hardcoded - intentional
      },
    });
    return response.json();
  },

  // Debug endpoint (should not exist in prod)
  async getDebugInfo() {
    const response = await fetch(ENDPOINTS.DEBUG.INFO, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    return response.json();
  },
};

// GraphQL queries (for testing GraphQL detection)
export const graphqlQueries = {
  GET_USER: `
    query GetUser($id: ID!) {
      user(id: $id) {
        id
        email
        name
        createdAt
      }
    }
  `,

  LOGIN_MUTATION: `
    mutation Login($email: String!, $password: String!) {
      login(email: $email, password: $password) {
        token
        user {
          id
          email
        }
      }
    }
  `,

  UPDATE_PROFILE: `
    mutation UpdateProfile($input: ProfileInput!) {
      updateProfile(input: $input) {
        success
        user {
          id
          name
          email
        }
      }
    }
  `,

  SUBSCRIBE_NOTIFICATIONS: `
    subscription OnNotification($userId: ID!) {
      notification(userId: $userId) {
        id
        type
        message
        timestamp
      }
    }
  `,
};

// GraphQL client
export const graphql = {
  async query(query: string, variables?: object) {
    const response = await fetch(GRAPHQL_ENDPOINT, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({query, variables}),
    });
    return response.json();
  },

  async getUser(id: string) {
    return this.query(graphqlQueries.GET_USER, {id});
  },

  async login(email: string, password: string) {
    return this.query(graphqlQueries.LOGIN_MUTATION, {email, password});
  },
};

// AWS S3 operations (with intentional credential exposure)
export const s3 = {
  async uploadFile(bucket: string, key: string, data: Blob) {
    // Intentionally bad practice - credentials in code
    const signedUrl = `https://${bucket}.s3.amazonaws.com/${key}?AWSAccessKeyId=${AWS_ACCESS_KEY_ID}&Signature=fake_signature`;

    const response = await fetch(signedUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/octet-stream',
        'x-amz-acl': 'private',
      },
      body: data,
    });
    return response.ok;
  },
};
