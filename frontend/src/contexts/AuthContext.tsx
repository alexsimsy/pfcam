import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getToken, getUser, logout as doLogout, isAuthenticated } from '../services/auth';

type AuthContextType = {
  user: any;
  isAuthenticated: boolean;
  logout: () => void;
  login: (token: string) => void;
  isAdmin: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState(getUser());
  const [auth, setAuth] = useState(isAuthenticated());

  useEffect(() => {
    setUser(getUser());
    setAuth(isAuthenticated());
  }, []);

  const login = (token: string) => {
    // The token is already stored by the auth service
    // Just update the context state
    setUser(getUser());
    setAuth(true);
  };

  const logout = () => {
    doLogout();
    setUser(null);
    setAuth(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: auth, logout, login, isAdmin: user?.role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
} 