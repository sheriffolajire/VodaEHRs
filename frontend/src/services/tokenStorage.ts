/**
 * Token persistence.
 *
 * Tokens are kept in localStorage so a page refresh preserves the session.
 * A single module owns these keys so the API client and auth context never
 * disagree about where the session lives.
 */

const ACCESS_KEY = "voda-access-token";
const REFRESH_KEY = "voda-refresh-token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
