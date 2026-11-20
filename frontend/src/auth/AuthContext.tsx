import { createContext, useState, type ReactNode } from "react";
import { login as apiLogin, clearToken, getToken } from "../api/client";

interface JwtPayload {
  sub: string;
  role: "admin" | "advisor";
  exp: number;
}

function decodeJwt(token: string): JwtPayload | null {
  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return decoded as JwtPayload;
  } catch {
    return null;
  }
}

interface AuthState {
  token: string | null;
  role: "admin" | "advisor" | null;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(getToken());
  const [role, setRole] = useState<"admin" | "advisor" | null>(() => {
    const t = getToken();
    return t ? (decodeJwt(t)?.role ?? null) : null;
  });
  const [username, setUsername] = useState<string | null>(() => {
    const t = getToken();
    return t ? (decodeJwt(t)?.sub ?? null) : null;
  });

  async function login(user: string, password: string) {
    const t = await apiLogin(user, password);
    const payload = decodeJwt(t);
    setToken(t);
    setRole(payload?.role ?? null);
    setUsername(payload?.sub ?? null);
  }

  function logout() {
    clearToken();
    setToken(null);
    setRole(null);
    setUsername(null);
  }

  return (
    <AuthContext.Provider value={{ token, role, username, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}