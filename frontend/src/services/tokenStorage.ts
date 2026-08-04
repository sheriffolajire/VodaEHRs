/**
 * Token persistence.
 *
 * Tokens are kept in localStorage so a page refresh preserves the session.
 * A single module owns these keys so the API client and auth context never
 * disagree about where the session lives.
 */

const ACCESS_KEY = "voda-access-token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function setAccessToken(accessToken: string): void {
  localStorage.setItem(ACCESS_KEY, accessToken);
}

export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_KEY);
}
