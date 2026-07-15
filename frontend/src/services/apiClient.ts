import axios, { AxiosError } from "axios";
import type { ErrorResponse } from "@/types/api";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

/** Shared error handling stub: normalizes backend error envelopes. */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    const message = error.response?.data?.message ?? error.message ?? "Unexpected error";
    return Promise.reject(new Error(message));
  },
);
