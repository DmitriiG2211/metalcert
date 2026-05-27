"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api, { getErrorMessage } from "@/lib/api";
import {
  getToken,
  setToken,
  removeToken,
  getStoredUser,
  setStoredUser,
} from "@/lib/auth";
import { User, LoginRequest, LoginResponse } from "@/types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export function useAuth() {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    const token = getToken();
    const storedUser = getStoredUser();
    if (token && storedUser) {
      setState({
        user: storedUser as unknown as User,
        isLoading: false,
        isAuthenticated: true,
      });
      // Verify token validity by fetching current user
      api
        .get<User>("/auth/me")
        .then((res) => {
          setStoredUser(res.data as unknown as Record<string, unknown>);
          setState({
            user: res.data,
            isLoading: false,
            isAuthenticated: true,
          });
        })
        .catch(() => {
          removeToken();
          setState({ user: null, isLoading: false, isAuthenticated: false });
          router.push("/login");
        });
    } else {
      setState({ user: null, isLoading: false, isAuthenticated: false });
    }
  }, [router]);

  const login = useCallback(
    async (credentials: LoginRequest): Promise<void> => {
      const formData = new FormData();
      formData.append("username", credentials.email);
      formData.append("password", credentials.password);

      const response = await api.post<LoginResponse>(
        "/auth/login",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setToken(response.data.access_token);
      setStoredUser(response.data.user as unknown as Record<string, unknown>);
      setState({
        user: response.data.user,
        isLoading: false,
        isAuthenticated: true,
      });
      router.push("/dashboard");
    },
    [router]
  );

  const logout = useCallback(() => {
    removeToken();
    setState({ user: null, isLoading: false, isAuthenticated: false });
    router.push("/login");
  }, [router]);

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.get<User>("/auth/me");
      setStoredUser(res.data as unknown as Record<string, unknown>);
      setState((prev) => ({ ...prev, user: res.data }));
    } catch {
      // ignore
    }
  }, []);

  return {
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    login,
    logout,
    refreshUser,
    getErrorMessage,
  };
}
