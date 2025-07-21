import React, { useState, useRef, useEffect } from 'react';
import { FaBell, FaTimes, FaExclamationTriangle, FaInfoCircle, FaCheckCircle, FaVideo } from 'react-icons/fa';
import { useNotifications } from '../contexts/NotificationContext';
import { websocketService } from '../services/websocket';
import type { NotificationPayload } from '../services/websocket';

interface NotificationWithId extends NotificationPayload {
  id: string;
  isRead?: boolean;
}

const NotificationBell: React.FC = () => {
  const { notifications, removeNotification, clearNotifications, markAsRead, markAllAsRead, isConnected } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const getIcon = (type: string) => {
    switch (type) {
      case 'event_captured':
        return <FaVideo className="text-simsy-blue" />;
      case 'camera_offline':
        return <FaExclamationTriangle className="text-red-500" />;
      case 'camera_online':
        return <FaCheckCircle className="text-green-500" />;
      case 'system_alert':
        return <FaInfoCircle className="text-simsy-blue" />;
      case 'manual_trigger':
        return <FaVideo className="text-simsy-blue" />;
      default:
        return <FaBell className="text-simsy-blue" />;
    }
  };

  const parseLocalDate = (timestamp: string) => {
    // Defensive: handle missing or malformed timestamps
    if (!timestamp || typeof timestamp !== 'string') return new Date();
    const parts = timestamp.split(' ');
    if (parts.length !== 2) return new Date();
    const [datePart, timePart] = parts;
    const dateArr = datePart.split('-').map(Number);
    const timeArr = timePart.split(':').map(Number);
    if (dateArr.length !== 3 || timeArr.length < 2) return new Date();
    const [year, month, day] = dateArr;
    const [hour, minute] = timeArr;
    if (
      isNaN(year) || isNaN(month) || isNaN(day) ||
      isNaN(hour) || isNaN(minute)
    ) return new Date();
    return new Date(year, month - 1, day, hour, minute);
  };

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '';
    const date = parseLocalDate(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleClearAll = () => {
    clearNotifications();
    setIsOpen(false);
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  const handleNotificationClick = (notification: NotificationWithId) => {
    if (!notification.isRead) {
      markAsRead(notification.id);
    }
  };

  const handleTestConnection = () => {
    console.log('Manual WebSocket connection test');
    websocketService.connect(1); // Connect with user ID 1 (admin)
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-white hover:text-simsy-dark hover:bg-white/10 rounded transition-colors"
        title="Notifications"
      >
        <FaBell size={20} />
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status Indicator */}
        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`} title={isConnected ? 'Connected' : 'Disconnected'} />
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-simsy-dark rounded-lg shadow-xl border border-gray-700 z-50 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <FaBell className="mr-2 text-simsy-blue" />
              Event Cam Alerts
            </h3>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-gray-400 hover:text-white transition-colors"
                >
                  Clear all
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <FaTimes size={14} />
              </button>
            </div>
          </div>

          {/* Connection Status */}
          <div className={`px-4 py-2 text-xs ${
            isConnected ? 'bg-green-900/30 text-green-400 border-b border-green-800' : 'bg-red-900/30 text-red-400 border-b border-red-800'
          }`}>
            <div className="flex items-center justify-between">
              <span>{isConnected ? '🟢 Event Cam real-time alerts connected' : '🔴 Event Cam alerts disconnected'}</span>
              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="text-xs bg-simsy-blue text-white px-2 py-1 rounded hover:bg-simsy-blue/80 transition-colors"
                  >
                    Mark Read
                  </button>
                )}
                {!isConnected && (
                  <button
                    onClick={handleTestConnection}
                    className="text-xs bg-simsy-blue text-white px-2 py-1 rounded hover:bg-simsy-blue/80 transition-colors"
                  >
                    Test Connection
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-400">
                <FaBell size={24} className="mx-auto mb-2 opacity-50" />
                <p>No Event Cam alerts</p>
                <p className="text-xs mt-1">Camera events and system alerts will appear here</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`px-4 py-3 border-b border-gray-700 hover:bg-gray-800 transition-colors cursor-pointer ${
                    !notification.isRead ? 'bg-blue-900/20' : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                                      <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1 relative">
                        {getIcon(notification.type)}
                        {!notification.isRead && (
                          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
                        )}
                      </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <h4 className={`text-sm font-medium truncate ${
                          !notification.isRead ? 'text-white font-semibold' : 'text-gray-300'
                        }`}>
                          {notification.title === 'Manual Event Triggered' ? 'Event Captured' : notification.title}
                        </h4>
                        <button
                          onClick={() => removeNotification(notification.id)}
                          className="flex-shrink-0 ml-2 text-gray-500 hover:text-gray-300 transition-colors"
                        >
                          <FaTimes size={12} />
                        </button>
                      </div>
                                              <p className={`text-sm mt-1 line-clamp-2 ${
                          !notification.isRead ? 'text-gray-200' : 'text-gray-400'
                        }`}>
                          {notification.message.replace('User admin manually triggered an event on camera', 'Event triggered on camera')}
                        </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {formatTime(notification.timestamp)}
                        </span>
                        {notification.category && (
                          <span className="text-xs bg-simsy-blue/20 text-simsy-blue px-2 py-1 rounded">
                            {notification.category}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-700 bg-gray-800">
              <p className="text-xs text-gray-400 text-center">
                {notifications.length} Event Cam alert{notifications.length !== 1 ? 's' : ''}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell; 