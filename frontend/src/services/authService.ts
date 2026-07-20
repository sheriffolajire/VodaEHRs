import { apiClient } from "@/services/apiClient";
import { clearTokens, getRefreshToken, setTokens } from "@/services/tokenStorage";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser, LoginResponse } from "@/types/auth";

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data } = await apiClient.post<SuccessResponse<LoginResponse>>("/auth/login", {
    email,
    password,
  });
  setTokens(data.data.access_token, data.data.refresh_token);
  return data.data.user;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser>>("/users/me");
  return data.data;
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  // Best-effort server-side revocation; the local session is cleared regardless.
  if (refreshToken) {
    try {
      await apiClient.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Ignore network/logout errors; clearing local tokens ends the session.
    }
  }
  clearTokens();
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post("/auth/password-reset/request", { email });
}
