import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { login as apiLogin, getMe } from "../services/apiClient";

const AuthContext = createContext(null);
const TOKEN_KEY = "coordination_engine_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const applyToken = useCallback(async (token) => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
      try {
        const res = await getMe();
        setUser(res.data);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      }
    } else {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      applyToken(token).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [applyToken]);

  async function login(email, password) {
    const res = await apiLogin({ email, password });
    await applyToken(res.data.access_token);
    return res.data.user;
  }

  function logout() {
    applyToken(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
