import { useAuthStore } from "../store/authStore";
import type { ApiError } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5000/api/v1";

const parseError = async (response: Response): Promise<ApiError> => {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as ApiError;
  }
  return {
    error: "Unexpected error",
    message: await response.text()
  };
};

const shouldRetryWithRefresh = (error: ApiError) => {
  return error.error === "Token expired" || error.error === "Missing token";
};

const refreshAccessToken = async (): Promise<string | null> => {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include"
  });

  if (!response.ok) {
    return null;
  }

  const data = (await response.json()) as { access_token: string };
  return data.access_token;
};

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  auth?: boolean;
  retryCount?: number;
};

export const apiRequest = async <T>(
  path: string,
  { method = "GET", body, auth = true, retryCount = 0 }: RequestOptions = {}
): Promise<T> => {
  const { accessToken, setAccessToken, clearAuth } = useAuthStore.getState();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(auth && accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
    },
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined
  });

  if (response.status === 204) {
    return null as T;
  }

  if (response.ok) {
    return (await response.json()) as T;
  }

  const error = await parseError(response);

  if (response.status === 401 && auth && retryCount < 1) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      setAccessToken(refreshed);
      return apiRequest<T>(path, { method, body, auth, retryCount: retryCount + 1 });
    }
    clearAuth();
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("auth:logout", {
          detail: { message: "Session expired. Please sign in again." }
        })
      );
    }
  }

  throw error;
};

