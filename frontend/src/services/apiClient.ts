import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ErrorResponse } from "@/types/api";
import type { SuccessResponse } from "@/types/api";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/** Emitted when a protected request cannot be recovered with a token refresh. */
export const AUTH_SESSION_EXPIRED_EVENT = "voda:auth-session-expired";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // Important: Send cookies with requests
});

/**
 * Refresh runs on a bare axios instance so it never re-enters this interceptor.
 * A shared promise coalesces concurrent 401s into a single refresh call.
 */
type RefreshResult = "refreshed" | "expired" | "unavailable";

let refreshInFlight: Promise<RefreshResult> | null = null;

async function refreshAccessToken(): Promise<RefreshResult> {
  try {
    // Cookie is sent automatically with withCredentials: true
    await axios.post<SuccessResponse<void>>(
      `${baseURL}/auth/refresh`,
      undefined,
      {
        headers: { "Content-Type": "application/json" },
        withCredentials: true, // Important: Send cookies
      },
    );
    return "refreshed";
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      return "expired";
    }
    return "unavailable";
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
      const refreshResult = await refreshInFlight;
      refreshInFlight = null;

      if (refreshResult === "refreshed") {
        // Cookie is automatically sent, just retry the request
        return apiClient(original);
      }

      // Let React clear the session and route protected pages to login. A hard
      // navigation here would remount AuthProvider on /login and repeat the
      // unauthenticated request cycle forever.
      if (refreshResult === "expired" && typeof window !== "undefined") {
        window.dispatchEvent(new Event(AUTH_SESSION_EXPIRED_EVENT));
      }
    }

    const message = error.response?.data?.message ?? error.message ?? "Unexpected error";
    return Promise.reject(new Error(message));
  },
);
