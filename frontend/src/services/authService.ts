import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser, LoginResponse } from "@/types/auth";

export async function login(email: string, password: string): Promise<AuthUser> {
  const { data } = await apiClient.post<SuccessResponse<LoginResponse>>("/auth/login", {
    email,
    password,
  });
  // Access token is now stored in HttpOnly cookie by the server
  // No need to manually store it
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
    // Ignore errors; server will clear cookies
  }
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post("/auth/password-reset/request", { email });
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await apiClient.post("/auth/password-reset/confirm", { token, new_password: newPassword });
}
