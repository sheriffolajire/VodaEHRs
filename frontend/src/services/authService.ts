import { apiClient } from "@/services/apiClient";
import { clearAccessToken, setAccessToken } from "@/services/tokenStorage";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser, LoginResponse } from "@/types/auth";

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data } = await apiClient.post<SuccessResponse<LoginResponse>>("/auth/login", {
    email,
    password,
  });
  setAccessToken(data.data.access_token);
  return data.data.user;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser>>("/users/me");
  return data.data;
}

export async function logout(): Promise<void> {
  // Server-side revocation is handled via HttpOnly cookie; we simply call logout.
  try {
    await apiClient.post("/auth/logout");
  } catch {
    // Ignore errors; we will clear local token regardless.
  }
  clearAccessToken();
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post("/auth/password-reset/request", { email });
}
