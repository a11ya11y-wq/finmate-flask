import type { ApiError } from "./types";

const stringifyValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }
  if (Array.isArray(value)) {
    return value.map((entry) => stringifyValue(entry)).filter(Boolean).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
};

const extractFieldErrors = (text: string) => {
  const matches = text.match(/[A-Za-z0-9_]+:\s[^:]+?(?=(\s+[A-Za-z0-9_]+:\s)|$)/g);
  if (matches && matches.length > 1) {
    return matches.map((entry) => entry.trim()).filter(Boolean);
  }
  return null;
};

const normalizeDetails = (details: string | string[]) => {
  if (Array.isArray(details)) {
    return details.map((entry) => stringifyValue(entry)).filter(Boolean);
  }

  const trimmed = details.trim();
  if (!trimmed) {
    return [];
  }

  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      if (Array.isArray(parsed)) {
        return parsed.map((entry) => stringifyValue(entry)).filter(Boolean);
      }
      if (parsed && typeof parsed === "object") {
        return Object.entries(parsed).map(([key, value]) => `${key}: ${stringifyValue(value)}`);
      }
      return [stringifyValue(parsed)].filter(Boolean);
    } catch {
      // Fall through to plain text parsing.
    }
  }

  const fieldErrors = extractFieldErrors(trimmed);
  if (fieldErrors) {
    return fieldErrors;
  }

  return trimmed
    .split(/\s*;\s*/)
    .map((entry) => entry.trim())
    .filter(Boolean);
};

const humanizeMessage = (message: string) => {
  const trimmed = message.trim();
  if (!trimmed) {
    return "";
  }

  const minLengthMatch = trimmed.match(/^(\w+):\s+String should have at least\s+(\d+)\s+characters$/i);
  if (minLengthMatch) {
    const field = minLengthMatch[1];
    const count = minLengthMatch[2];
    if (!field || !count) {
      return trimmed;
    }
    const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, " ");
    return `${label} must be at least ${count} characters`;
  }

  const greaterThanMatch = trimmed.match(/^(\w+):\s+Input should be greater than\s+(-?\d+(?:\.\d+)?)$/i);
  if (greaterThanMatch) {
    const field = greaterThanMatch[1];
    const value = greaterThanMatch[2];
    if (!field || !value) {
      return trimmed;
    }
    const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, " ");
    return `${label} must be greater than ${value}`;
  }

  const requiredMatch = trimmed.match(/^(\w+):\s+String should have at least\s+1\s+character$/i);
  if (requiredMatch) {
    const field = requiredMatch[1];
    if (!field) {
      return trimmed;
    }
    const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, " ");
    return `${label} cannot be empty`;
  }

  return trimmed
    .replace(/String should have at least\s+(\d+)\s+characters?/gi, "must be at least $1 characters")
    .replace(/Input should be greater than\s+(-?\d+(?:\.\d+)?)/gi, "must be greater than $1")
    .replace(/String should have at least\s+1\s+character/gi, "cannot be empty")
    .replace(/String should have at least\s+1\s+characters/gi, "cannot be empty")
    .replace(/String should have at least\s+1/gi, "cannot be empty");
};

export const toErrorMessage = (error: unknown) => {
  // Перехоплюємо офлайн-помилку від fetch
  if (!navigator.onLine || (error instanceof TypeError && error.message === 'Failed to fetch')) {
    return "No internet connection. Please check your network.";
  }

  if (typeof error === "string") {
    return error.trim();
  }

  if (error && typeof error === "object") {
    const apiError = error as ApiError;
    if (apiError.details) {
      const normalized = normalizeDetails(apiError.details).map(humanizeMessage).filter(Boolean);
      if (normalized.length > 0) {
        return normalized.join("\n");
      }
    }
    if (apiError.message) {
      return apiError.message.trim();
    }
    if (apiError.error) {
      return apiError.error.trim();
    }
  }

  return "Something went wrong";
};

