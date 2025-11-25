/**
 * API configuration for frontend
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export const API_ENDPOINTS = {
  // Auth
  AUTH_REGISTER: `${API_BASE_URL}/auth/register`,
  AUTH_LOGIN: `${API_BASE_URL}/auth/login`,
  AUTH_ME: `${API_BASE_URL}/auth/me`,
  AUTH_LOGOUT: `${API_BASE_URL}/auth/logout`,
  AUTH_STEAM_LOGIN: `${API_BASE_URL}/auth/steam/login`,
  AUTH_FACEIT_LOGIN: `${API_BASE_URL}/auth/faceit/login`,
  
  // Demo analysis
  DEMO_ANALYZE: `${API_BASE_URL}/demo/analyze`,
  // Player analysis
  PLAYER_ANALYSIS: (nickname: string) => `${API_BASE_URL}/players/${encodeURIComponent(nickname)}/analysis`,
  
  // Payments
  PAYMENTS_CREATE: `${API_BASE_URL}/payments/create`,
  PAYMENTS_STATUS: (paymentId: string) => `${API_BASE_URL}/payments/status/${paymentId}`,
  PAYMENTS_METHODS: (region: string) => `${API_BASE_URL}/payments/methods/${region}`,
  
  // Subscriptions
  SUBSCRIPTIONS_PLANS: `${API_BASE_URL}/subscriptions/plans`,
  SUBSCRIPTIONS_USER: (userId: string) => `${API_BASE_URL}/subscriptions/${userId}`,
  SUBSCRIPTIONS_CHECK_FEATURE: (userId: string, feature: string) => 
    `${API_BASE_URL}/subscriptions/${userId}/check-feature?feature=${feature}`,
  
  // Teammates
  TEAMMATES_SEARCH: `${API_BASE_URL}/teammates/search`,
  TEAMMATES_PREFERENCES: `${API_BASE_URL}/teammates/preferences`,
  
  // Admin
  ADMIN_RATE_LIMIT_BANS: `${API_BASE_URL}/admin/rate-limit/bans`,
  ADMIN_RATE_LIMIT_VIOLATIONS: `${API_BASE_URL}/admin/rate-limit/violations`,
  ADMIN_RATE_LIMIT_BAN: (kind: string, value: string) =>
    `${API_BASE_URL}/admin/rate-limit/bans/${encodeURIComponent(kind)}/${encodeURIComponent(value)}`,
  
  // Health
  HEALTH: `${API_BASE_URL}/health`,
} as const;

export default API_ENDPOINTS;

