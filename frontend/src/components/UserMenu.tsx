import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handlePasswordReset = () => {
    // For now, just navigate to a placeholder page
    navigate('/reset-password');
  };

  return (
    <div className="relative">
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