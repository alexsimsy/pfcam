import { useEffect, useRef, useCallback, useState } from 'react';
import { getToken } from '../services/auth';

interface NotificationMessage {
  type: string;
  title: string;
  message: string;
  data: any;
  timestamp: string;
  priority: string;
  category: string;
}

interface UseWebSocketOptions {
  userId: number;
  onMessage?: (message: NotificationMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  userId,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  autoReconnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<NotificationMessage | null>(null);

  // Request notification permission for browser push notifications
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }, []);

  // Show browser push notification
  const showPushNotification = useCallback((message: NotificationMessage) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(message.title, {
        body: message.message,
        icon: '/favicon.ico', // You can customize this
        badge: '/favicon.ico',
        tag: message.type, // Group similar notifications
        requireInteraction: message.priority === 'high' || message.priority === 'urgent',
        silent: false
      });

      // Handle notification click
      notification.onclick = () => {
        window.focus();
        notification.close();
        
        // Navigate to relevant page based on notification type
        if (message.type === 'event_captured') {
          window.location.href = '/events';
        } else if (message.type === 'camera_offline' || message.type === 'camera_online') {
          window.location.href = '/cameras';
        }
      };

      // Auto-close after 10 seconds (except for urgent notifications)
      if (message.priority !== 'urgent') {
        setTimeout(() => {
          notification.close();
        }, 10000);
      }
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const token = getToken();
      if (!token) {
        console.warn('No authentication token available for WebSocket connection');
        return;
      }

      // Build WebSocket URL with authentication
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/notifications/ws/${userId}?token=${token}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: NotificationMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Call the message handler
          onMessage?.(message);
          
          // Show browser push notification if not focused
          if (document.hidden && message.type !== 'connection_established') {
            showPushNotification(message);
          }
          
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();
        
        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [userId, onMessage, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval, maxReconnectAttempts, showPushNotification]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Initialize connection and request notification permission
  useEffect(() => {
    // Request notification permission on mount
    requestNotificationPermission();
    
    // Connect to WebSocket
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect, requestNotificationPermission]);

  // Reconnect when userId changes
  useEffect(() => {
    disconnect();
    connect();
  }, [userId, disconnect, connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    requestNotificationPermission
  };
} 