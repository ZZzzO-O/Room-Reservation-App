// file: src/api/authApi.js
// purpose: Handles authentication requests, session management, and local fallback
// author: Zin Zin Zaw Win
// date: 2026-10-20

const API_BASE_URL = '/api';

const TOKEN_STORAGE_KEY = 'vibranium_auth_token';
const USER_STORAGE_KEY = 'vibranium_auth_user';

/**
 * Test accounts from the Vibranium Functional Test Plan.
 */
export const SEED_USERS = import.meta.env.DEV ? [
  {
    email: 'staff1@cmkl.ac.th',
    password: 'Test@1234',
    user: {
      user_id: 'USR-STAFF1',
      email: 'staff1@cmkl.ac.th',
      name: 'CMKL Staff Member',
      role: 'Staff',
    },
  },
  {
    email: 'prof1@cmkl.ac.th',
    password: 'Test@1234',
    user: {
      user_id: 'USR-PROF1',
      email: 'prof1@cmkl.ac.th',
      name: 'CMKL Professor',
      role: 'Professor',
    },
  },
] : [];

/**
 * Retrieve the active session token from browser localStorage.
 * @returns {string|null} The token string or null.
 */
export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Retrieve the active user object from browser localStorage.
 * @returns {Object|null} The user object or null.
 */
export function getStoredUser() {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * Save authentication token and user profile in browser storage.
 * @param {string} token - The session token.
 * @param {Object} user - The user profile object.
 */
export function setStoredSession(token, user) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

/**
 * Clear authentication token and profile from browser storage.
 */
export function clearStoredSession() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

/**
 * Generate default authorization headers for API requests.
 * @returns {Object} Request headers containing Authorization Bearer token if present.
 */
export function getAuthHeaders() {
  const token = getStoredToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Authenticate against the backend API Gateway, with offline seed fallback.
 * @param {string} email - User email address.
 * @param {string} password - User password.
 * @returns {Promise<{token: string, user: Object}>} The authentication result.
 */
export async function loginUser(email, password) {
  const trimmedEmail = email.trim();
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: trimmedEmail, password }),
    });

    // A stopped API gateway makes Vite return an empty proxy response. Read
    // the body first so that case can use the offline test-account fallback
    // instead of leaking a JSON parser error into the sign-in dialog.
    const responseText = await response.text();
    let data = {};
    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error('Authentication service is temporarily unavailable.');
      }
    }

    if (!response.ok) {
      if (response.status >= 500) {
        throw new Error('Authentication service is temporarily unavailable.');
      }
      throw new Error(data.error || 'Authentication failed.');
    }

    if (!data.token || !data.user) {
      throw new Error('Authentication service is temporarily unavailable.');
    }

    setStoredSession(data.token, data.user);
    return data;
  } catch (err) {
    if (!import.meta.env.DEV) {
      throw err;
    }

    // Backend refused or offline: fall back to the test accounts
    const matched = SEED_USERS.find(
      (entry) => entry.email.toLowerCase() === trimmedEmail.toLowerCase()
    );

    const canUseOfflineFallback = [
      'Failed to fetch',
      'Authentication service is temporarily unavailable.',
    ].includes(err.message) || err.message?.includes('NetworkError');

    if (!canUseOfflineFallback) {
      throw err;
    }

    if (!matched) {
      throw new Error('Account not found.');
    }
    if (matched.password !== password) {
      throw new Error('Incorrect email or password.');
    }

    const fallbackToken = `mock-token-${matched.user.role.toLowerCase()}-${Date.now()}`;
    setStoredSession(fallbackToken, matched.user);
    return { token: fallbackToken, user: matched.user };
  }
}

/**
 * Terminate user session via the API Gateway and clear local state.
 * @returns {Promise<void>}
 */
export async function logoutUser() {
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
  } catch {
    // Ignore network errors on logout
  } finally {
    clearStoredSession();
  }
}

/**
 * Fetch the current user profile from the server to verify token validity.
 * @returns {Promise<Object|null>} The user profile, or null if unauthenticated.
 */
export async function fetchCurrentUser() {
  const token = getStoredToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (response.ok) {
      const data = await response.json();
      if (data.user) {
        setStoredSession(token, data.user);
        return data.user;
      }
    } else if (response.status === 401) {
      clearStoredSession();
      return null;
    }
  } catch {
    if (!import.meta.env.DEV) {
      clearStoredSession();
      return null;
    }
    // Return cached user if backend is momentarily unreachable in development.
  }
  if (!import.meta.env.DEV) {
    clearStoredSession();
    return null;
  }
  return getStoredUser();
}
