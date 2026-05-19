import { apiRequest } from "./client";
import type { User } from "./types";

export type UpdateProfilePayload = {
  username?: string;
  currency?: "USD" | "EUR" | "UAH";
  avatar?: string;
};

export const getProfile = async () => {
  return apiRequest<User>("/profile/me");
};

export const updateProfile = async (payload: UpdateProfilePayload) => {
  return apiRequest<User>("/profile/me", {
    method: "PUT",
    body: payload
  });
};

export const deleteProfile = async () => {
  return apiRequest<void>("/profile/me", {
    method: "DELETE"
  });
};

export const changePassword = async (payload: {
  old_password: string;
  new_password: string;
  confirm_password: string;
}) => {
  return apiRequest<{ message: string }>("/profile/change-password", {
    method: "POST",
    body: payload
  });
};

export const setMonobankToken = async (token: string) => {
  return apiRequest<User>("/profile/monobank", {
    method: "PUT",
    body: { token }
  });
};

export const removeMonobankToken = async () => {
  return apiRequest<void>("/profile/monobank", {
    method: "DELETE"
  });
};

