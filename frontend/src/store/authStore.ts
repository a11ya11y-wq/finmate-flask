import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../api/types";
import { getProfile } from "../api/profile";
import { login as loginRequest, logout as logoutRequest, refresh } from "../api/auth";
import { queryClient } from "../lib/queryClient";
import { queryKeys } from "../api/queryKeys";

let restoreSessionPromise: Promise<boolean> | null = null;

type AuthState = {
  accessToken: string | null;
  user: User | null;
  status: "idle" | "loading";
  isRestoring: boolean;
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  restoreSession: () => Promise<boolean>;
  logout: () => Promise<void>;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
  accessToken: null,
  user: null,
  status: "idle",
  isRestoring: true,
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
  restoreSession: async () => {
    if (restoreSessionPromise) {
      return restoreSessionPromise;
    }

    set({ isRestoring: true });
    restoreSessionPromise = (async () => {
      try {
        const result = await refresh();
        set({ accessToken: result.access_token });
        const profile = await queryClient.fetchQuery({
          queryKey: queryKeys.profile,
          queryFn: getProfile
        });
        set({ user: profile });
        return true;
      } catch (error) {
        // Якщо помилка через відсутність інтернету — не розлогінюємо юзера!
        if (!navigator.onLine || (error instanceof TypeError && error.message === 'Failed to fetch')) {
          console.warn('Offline mode: skipping auth clear');
          return false;
        }
        
        queryClient.removeQueries({ queryKey: queryKeys.profile });
        get().clearAuth();
        return false;
      } finally {
        set({ isRestoring: false });
        restoreSessionPromise = null;
      }
    })();

    return restoreSessionPromise;
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
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken }),
    }
  )
);

