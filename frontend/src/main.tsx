import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { AppStateProvider } from './contexts/AppStateContext'
import App from './App.tsx'
import './index.css'

// Remove StrictMode to prevent double execution
createRoot(document.getElementById('root')!).render(
  <AppStateProvider>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </AppStateProvider>,
)
