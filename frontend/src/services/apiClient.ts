import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ErrorResponse } from "@/types/api";
import type { SuccessResponse } from "@/types/api";
import type { AccessTokenResponse } from "@/types/auth";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/services/tokenStorage";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Attach the current access token to every outgoing request.
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Refresh runs on a bare axios instance so it never re-enters this interceptor.
 * A shared promise coalesces concurrent 401s into a single refresh call.
 */
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  try {
    const { data } = await axios.post<SuccessResponse<AccessTokenResponse>>(
      `${baseURL}/auth/refresh`,
      undefined,
      { headers: { "Content-Type": "application/json" } },
    );
    setAccessToken(data.data.access_token);
    return data.data.access_token;
  } catch {
    clearAccessToken();
    return null;
  }
}

// On a 401, attempt a single token refresh and retry the original request once.
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const original = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    const isAuthCall = original?.url?.includes("/auth/");

    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      refreshInFlight = refreshInFlight ?? refreshAccessToken();
      const newToken = await refreshInFlight;
      refreshInFlight = null;

      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(original);
      }
      // Refresh failed: force a clean logout by redirecting to the login page.
      window.location.assign("/login");
    }

    const message = error.response?.data?.message ?? error.message ?? "Unexpected error";
    return Promise.reject(new Error(message));
  },
);
