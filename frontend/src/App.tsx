import React from 'react';
import { Link, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Events from './pages/Events';
import Streams from './pages/Streams';
import Settings from './pages/Settings';
import NotificationSettings from './pages/NotificationSettings';

import Login from './pages/Login';
import RequireAuth from './components/RequireAuth';
import UserMenu from './components/UserMenu';
import ResetPassword from './pages/ResetPassword';
import { useAuth } from './contexts/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import Notification from './components/Notification';
import Admin from './pages/Admin';
import { getUser } from './services/auth';
import { useAppState } from './contexts/AppStateContext';
import { NotificationProvider } from './contexts/NotificationContext';
import NotificationContainer from './components/NotificationContainer';
import NotificationBell from './components/NotificationBell';

const navLinks = [
  { name: 'Dashboard', path: '/' },
  { name: 'Events', path: '/events' },
  { name: 'Streams', path: '/streams' },
  { name: 'Settings', path: '/settings' },
  { name: 'Notifications', path: '/notifications' },
];

function CameraIcon() {
  return (
    <svg className="w-8 h-8 text-simsy-blue" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><circle cx="12" cy="13.5" r="3.5"/></svg>
  );
}
function EventIcon() {
  return (
    <svg className="w-8 h-8 text-simsy-blue" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 9h18"/><circle cx="12" cy="14" r="3"/></svg>
  );
}
function LockIcon() {
  return (
    <svg className="w-8 h-8 text-simsy-blue" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="11" width="14" height="8" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  );
}

export default function App() {
  const { isAdmin } = useAuth();

  return (
    <ErrorBoundary>
      <NotificationProvider>
        <div className="min-h-screen bg-simsy-dark text-simsy-text font-sans">
          <Notification />
        {/* Top Navigation Bar */}
        <nav className="w-full bg-simsy-blue px-10 py-4 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-4">
            <span className="text-2xl font-extrabold tracking-widest text-white">S-IMSY</span>
          </div>
          <div className="flex gap-8 items-center">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className="text-white text-lg font-medium hover:text-simsy-dark hover:bg-white/10 px-3 py-1 rounded transition"
              >
                {link.name}
              </Link>
            ))}
            {isAdmin && (
              <Link
                to="/admin"
                className="text-white text-lg font-bold hover:text-simsy-dark hover:bg-white/10 px-3 py-1 rounded transition border border-white"
              >
                Admin
              </Link>
            )}
            <NotificationBell />
            <UserMenu />
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-5xl mx-auto py-16 px-4">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/admin" element={<RequireAuth><Admin /></RequireAuth>} />
            <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/events" element={<RequireAuth><Events /></RequireAuth>} />
            <Route path="/streams" element={<Streams />} />
            <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
            <Route path="/notifications" element={<RequireAuth><NotificationSettings /></RequireAuth>} />
          </Routes>
        </main>
      </div>
      </NotificationProvider>
    </ErrorBoundary>
  );
}
