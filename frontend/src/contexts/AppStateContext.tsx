import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';

interface AppState {
  globalLoading: boolean;
  errors: string[];
  notifications: Array<{ id: string; message: string; type: 'success' | 'error' }>;
}

type AppAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'ADD_ERROR'; payload: string }
  | { type: 'CLEAR_ERROR'; payload: string }
  | { type: 'ADD_NOTIFICATION'; payload: { message: string; type: 'success' | 'error' } }
  | { type: 'REMOVE_NOTIFICATION'; payload: string };

const initialState: AppState = {
  globalLoading: false,
  errors: [],
  notifications: [],
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, globalLoading: action.payload };
    case 'ADD_ERROR':
      return { ...state, errors: [...state.errors, action.payload] };
    case 'CLEAR_ERROR':
      return { ...state, errors: state.errors.filter(e => e !== action.payload) };
    case 'ADD_NOTIFICATION':
      return { 
        ...state, 
        notifications: [...state.notifications, { 
          id: Date.now().toString(), 
          message: action.payload.message, 
          type: action.payload.type 
        }] 
      };
    case 'REMOVE_NOTIFICATION':
      return { 
        ...state, 
        notifications: state.notifications.filter(n => n.id !== action.payload) 
      };
    default:
      return state;
  }
}

const AppStateContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider');
  }
  return context;
} 