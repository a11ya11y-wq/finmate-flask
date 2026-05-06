import type { ApiError } from "./types";

export const toErrorMessage = (error: unknown) => {
  if (typeof error === "string") {
    return error;
  }

  if (error && typeof error === "object") {
    const apiError = error as ApiError;
    if (apiError.details) {
      if (Array.isArray(apiError.details)) {
        return apiError.details.join("\n");
      }
      return apiError.details;
    }
    if (apiError.message) {
      return apiError.message;
    }
    if (apiError.error) {
      return apiError.error;
    }
  }

  return "Something went wrong";
};

