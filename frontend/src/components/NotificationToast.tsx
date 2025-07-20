import React, { useEffect, useState } from 'react';
import { FaBell, FaTimes, FaExclamationTriangle, FaInfoCircle, FaCheckCircle } from 'react-icons/fa';
import type { NotificationPayload } from '../services/websocket';

interface NotificationToastProps {
  notification: NotificationPayload & { id: string };
  onRemove: (id: string) => void;
}

const NotificationToast: React.FC<NotificationToastProps> = ({ notification, onRemove }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Animate in
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const getIcon = () => {
    switch (notification.type) {
      case 'event_captured':
        return <FaBell className="text-simsy-blue" />;
      case 'camera_offline':
        return <FaExclamationTriangle className="text-red-500" />;
      case 'camera_online':
        return <FaCheckCircle className="text-green-500" />;
      case 'system_alert':
        return <FaInfoCircle className="text-simsy-blue" />;
      default:
        return <FaBell className="text-simsy-blue" />;
    }
  };

  const getPriorityStyles = () => {
    switch (notification.priority) {
      case 'high':
        return 'border-l-4 border-red-500 bg-red-50';
      case 'urgent':
        return 'border-l-4 border-red-600 bg-red-100';
      default:
        return 'border-l-4 border-simsy-blue bg-simsy-blue/5';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleRemove = () => {
    setIsVisible(false);
    setTimeout(() => onRemove(notification.id), 300);
  };

  return (
    <div
      className={`
        fixed top-4 right-4 z-50 max-w-sm w-full bg-white rounded-lg shadow-lg border
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        ${getPriorityStyles()}
      `}
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0 mt-0.5">
              {getIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-simsy-text">
                {notification.title}
              </h4>
              <p className="text-sm text-simsy-text mt-1">
                {notification.message}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-simsy-text/60">
                  {formatTime(notification.timestamp)}
                </span>
                {notification.category && (
                  <span className="text-xs bg-simsy-blue/10 text-simsy-blue px-2 py-1 rounded">
                    {notification.category}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={handleRemove}
            className="flex-shrink-0 ml-3 text-simsy-text/40 hover:text-simsy-text/60 transition-colors"
          >
            <FaTimes size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationToast; 