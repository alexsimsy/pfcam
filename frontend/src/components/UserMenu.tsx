import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open]);

  const handleLogout = () => {
    setOpen(false);
    logout();
    navigate('/login');
  };

  const handlePasswordReset = () => {
    setOpen(false);
    navigate('/reset-password');
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        className="text-white font-bold px-4 py-2 rounded bg-simsy-blue hover:bg-simsy-dark hover:text-simsy-blue transition"
        onClick={() => setOpen((v) => !v)}
      >
        {user?.username || 'User'} ▼
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-simsy-card rounded shadow-lg z-50">
          <button
            className="block w-full text-left px-4 py-2 hover:bg-simsy-dark hover:text-simsy-blue"
            onClick={handlePasswordReset}
          >
            Reset Password
          </button>
          <button
            className="block w-full text-left px-4 py-2 hover:bg-simsy-dark hover:text-simsy-blue"
            onClick={handleLogout}
          >
            Log Out
          </button>
        </div>
      )}
    </div>
  );
} 