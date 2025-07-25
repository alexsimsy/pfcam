import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { websocketService } from '../services/websocket';
import type { NotificationPayload } from '../services/websocket';
import { useAuth } from './AuthContext';

interface NotificationWithId extends NotificationPayload {
  id: string;
  isRead?: boolean;
}

interface NotificationContextType {
  notifications: NotificationWithId[];
  addNotification: (notification: NotificationPayload) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  isConnected: boolean;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationWithId[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;

    // Extract user ID from JWT payload
    // Since the JWT only contains email (sub), we need to determine the user ID
    // For now, we'll use user ID 1 for admin@s-imsy.com
    let userId: number | null = null;
    
    if (user.sub === 'admin@s-imsy.com') {
      userId = 1;
    } else {
      // For other users, we could make an API call to get the user ID
      // For now, we'll use a fallback
      console.warn('Unknown user email, using default user ID 1');
      userId = 1;
    }
    
    if (!userId) {
      console.warn('No user ID available for WebSocket connection');
      return;
    }

    console.log('Connecting to WebSocket with user ID:', userId, 'for user:', user.sub);

    // Connect to WebSocket
    websocketService.connect(userId);

    // Listen for connection status
    const handleConnectionChange = (connected: boolean) => {
      console.log('WebSocket connection status changed:', connected);
      setIsConnected(connected);
    };

    // Listen for notifications
    const handleNotification = (notification: NotificationPayload) => {
      console.log('Received notification:', notification);
      addNotification(notification);
    };

    websocketService.addConnectionListener(handleConnectionChange);
    websocketService.addNotificationListener(handleNotification);

    // Cleanup on unmount
    return () => {
      websocketService.removeConnectionListener(handleConnectionChange);
      websocketService.removeNotificationListener(handleNotification);
      websocketService.disconnect();
    };
  }, [user]);

  // Cleanup old notifications every hour
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      setNotifications(prev => {
        const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        return prev.filter(n => {
          const notificationDate = new Date(n.timestamp);
          return notificationDate > oneDayAgo;
        });
      });
    }, 60 * 60 * 1000); // Run every hour

    return () => clearInterval(cleanupInterval);
  }, []);

  const addNotification = (notification: NotificationPayload) => {
    const id = `${notification.timestamp}-${Math.random()}`;
    const notificationWithId: NotificationWithId = { ...notification, id };
    
    setNotifications(prev => {
      const newNotifications = [notificationWithId, ...prev.slice(0, 49)]; // Keep last 50 notifications
      
      // Auto-remove notifications older than 24 hours
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return newNotifications.filter(n => {
        const notificationDate = new Date(n.timestamp);
        return notificationDate > oneDayAgo;
      });
    });
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, isRead: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(n => ({ ...n, isRead: true }))
    );
  };

  const value: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    markAsRead,
    markAllAsRead,
    isConnected
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}; 