import { apiRequest } from "./client";
import type { User } from "./types";

export type LoginPayload = {
  email: string;
  password: string;
  remember_me: boolean;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
};

export const login = async (payload: LoginPayload) => {
  return apiRequest<{ access_token: string; message: string }>("/auth/login", {
    method: "POST",
    body: payload,
    auth: false
  });
};

export const register = async (payload: RegisterPayload) => {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: payload,
    auth: false
  });
};

export const logout = async () => {
  return apiRequest<{ message: string }>("/auth/logout", {
    method: "POST"
  });
};

export const refresh = async () => {
  return apiRequest<{ access_token: string }>("/auth/refresh", {
    method: "POST",
    auth: false
  });
};

