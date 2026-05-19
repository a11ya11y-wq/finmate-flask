import { create } from "zustand";
import type { User } from "../api/types";
import { getProfile } from "../api/profile";
import { login as loginRequest, logout as logoutRequest, refresh } from "../api/auth";
import { queryClient } from "../lib/queryClient";
import { queryKeys } from "../api/queryKeys";

type AuthState = {
  accessToken: string | null;
  user: User | null;
  status: "idle" | "loading";
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  refreshSession: () => Promise<boolean>;
  logout: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  status: "idle",
  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user }),
  clearAuth: () => set({ accessToken: null, user: null }),
  login: async (email, password, rememberMe) => {
    set({ status: "loading" });
    try {
      const result = await loginRequest({ email, password, remember_me: rememberMe });
      set({ accessToken: result.access_token });
      const profile = await queryClient.fetchQuery({
        queryKey: queryKeys.profile,
        queryFn: getProfile
      });
      set({ user: profile, status: "idle" });
    } catch (error) {
      set({ status: "idle" });
      throw error;
    }
  },
  refreshSession: async () => {
    set({ status: "loading" });
    try {
      const result = await refresh();
      set({ accessToken: result.access_token });
      const profile = await queryClient.fetchQuery({
        queryKey: queryKeys.profile,
        queryFn: getProfile
      });
      set({ user: profile, status: "idle" });
      return true;
    } catch (error) {
      set({ status: "idle" });
      return false;
    }
  },
  logout: async () => {
    const { clearAuth } = get();
    try {
      await logoutRequest();
    } finally {
      queryClient.removeQueries({ queryKey: queryKeys.profile });
      clearAuth();
    }
  }
}));

