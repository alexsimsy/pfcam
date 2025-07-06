import React, { useEffect } from 'react';
import { useAppState } from '../contexts/AppStateContext';
import { FaCheckCircle, FaExclamationCircle, FaTimes } from 'react-icons/fa';

export default function Notification() {
  const { state, dispatch } = useAppState();

  useEffect(() => {
    // Auto-remove notifications after 5 seconds
    const timeouts: ReturnType<typeof setTimeout>[] = [];
    
    state.notifications.forEach((notification) => {
      const timeout = setTimeout(() => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id });
      }, 5000);
      timeouts.push(timeout);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [state.notifications, dispatch]);

  if (state.notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {state.notifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-center p-4 rounded-lg shadow-lg max-w-sm ${
            notification.type === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}
        >
          <div className="flex-shrink-0 mr-3">
            {notification.type === 'success' ? (
              <FaCheckCircle className="w-5 h-5" />
            ) : (
              <FaExclamationCircle className="w-5 h-5" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">{notification.message}</p>
          </div>
          <button
            onClick={() => dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id })}
            className="flex-shrink-0 ml-3 text-white hover:text-gray-200 transition"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
} 