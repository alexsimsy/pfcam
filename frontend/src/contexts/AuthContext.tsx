import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getToken, getUser, logout as doLogout, isAuthenticated } from '../services/auth';
import { useAppState } from './AppStateContext';

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
  const { dispatch } = useAppState ? useAppState() : { dispatch: () => {} };

  // Session and inactivity timeouts
  const SESSION_MAX_HOURS = 8;
  const INACTIVITY_MINUTES = 30;
  const SESSION_KEY = 'eventcam_login_time';
  const INACTIVITY_KEY = 'eventcam_last_activity';
  let inactivityTimeout: ReturnType<typeof setTimeout>;

  useEffect(() => {
    setUser(getUser());
    setAuth(isAuthenticated());
    // On mount, set up session/inactivity checks
    const checkSession = () => {
      const loginTime = localStorage.getItem(SESSION_KEY);
      if (loginTime) {
        const loginDate = new Date(Number(loginTime));
        const now = new Date();
        const hours = (now.getTime() - loginDate.getTime()) / (1000 * 60 * 60);
        if (hours >= SESSION_MAX_HOURS) {
          doLogout();
          setUser(null);
          setAuth(false);
          localStorage.removeItem(SESSION_KEY);
          localStorage.removeItem(INACTIVITY_KEY);
          if (dispatch) dispatch({ type: 'ADD_NOTIFICATION', payload: { message: 'Your session has expired. Please log in again.', type: 'error' } });
        }
      }
    };
    const checkInactivity = () => {
      const lastActivity = localStorage.getItem(INACTIVITY_KEY);
      if (lastActivity) {
        const last = new Date(Number(lastActivity));
        const now = new Date();
        const mins = (now.getTime() - last.getTime()) / (1000 * 60);
        if (mins >= INACTIVITY_MINUTES) {
          doLogout();
          setUser(null);
          setAuth(false);
          localStorage.removeItem(SESSION_KEY);
          localStorage.removeItem(INACTIVITY_KEY);
          if (dispatch) dispatch({ type: 'ADD_NOTIFICATION', payload: { message: 'You have been logged out due to inactivity.', type: 'error' } });
        }
      }
    };
    // Check on mount and every minute
    checkSession();
    checkInactivity();
    const interval = setInterval(() => {
      checkSession();
      checkInactivity();
    }, 60 * 1000);
    // Listen for user activity
    const activity = () => {
      localStorage.setItem(INACTIVITY_KEY, Date.now().toString());
    };
    window.addEventListener('mousemove', activity);
    window.addEventListener('keydown', activity);
    window.addEventListener('mousedown', activity);
    window.addEventListener('touchstart', activity);
    // Set initial activity time
    if (auth) localStorage.setItem(INACTIVITY_KEY, Date.now().toString());
    return () => {
      clearInterval(interval);
      window.removeEventListener('mousemove', activity);
      window.removeEventListener('keydown', activity);
      window.removeEventListener('mousedown', activity);
      window.removeEventListener('touchstart', activity);
    };
  }, []);

  const login = (token: string) => {
    // The token is already stored by the auth service
    // Just update the context state
    setUser(getUser());
    setAuth(true);
    localStorage.setItem(SESSION_KEY, Date.now().toString());
    localStorage.setItem(INACTIVITY_KEY, Date.now().toString());
  };

  const logout = () => {
    doLogout();
    setUser(null);
    setAuth(false);
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(INACTIVITY_KEY);
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