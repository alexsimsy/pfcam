import { getToken } from './auth';

export interface NotificationPayload {
  type: string;
  title: string;
  message: string;
  data: any;
  timestamp: string;
  priority: string;
  category: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: ((notification: NotificationPayload) => void)[] = [];
  private connectionListeners: ((connected: boolean) => void)[] = [];
  private isConnected = false;

  async connect(userId: number): Promise<void> {
    try {
      const token = getToken();
      if (!token) {
        console.warn('No auth token available for WebSocket connection');
        return;
      }

      // Use the same host as the current page, but ensure we're using the correct protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/notifications/ws/${userId}?token=${token}`;
      
      console.log('Attempting WebSocket connection:', { 
        userId, 
        protocol, 
        host, 
        wsUrl: wsUrl.replace(token, '[TOKEN]') 
      });
      
      this.ws = new WebSocket(wsUrl);
      
      // Add connection timeout
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          this.ws.close();
          this.isConnected = false;
          this.notifyConnectionListeners(false);
        }
      }, 5000); // 5 second timeout
      
      this.ws.onopen = () => {
        console.log('WebSocket connected successfully');
        clearTimeout(connectionTimeout);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyConnectionListeners(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connection_established') {
            console.log('WebSocket connection established');
            return;
          }

          // Handle notification payload
          if (data.type && data.title && data.message) {
            const notification: NotificationPayload = {
              type: data.type,
              title: data.title,
              message: data.message,
              data: data.data || {},
              timestamp: data.timestamp,
              priority: data.priority || 'normal',
              category: data.category || 'general'
            };
            
            this.notifyListeners(notification);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.notifyConnectionListeners(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          
          setTimeout(() => {
            this.connect(userId);
          }, this.reconnectDelay * this.reconnectAttempts);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket connection failed for user:', userId);
        this.isConnected = false;
        this.notifyConnectionListeners(false);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'User initiated disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.notifyConnectionListeners(false);
  }

  addNotificationListener(listener: (notification: NotificationPayload) => void): void {
    this.listeners.push(listener);
  }

  removeNotificationListener(listener: (notification: NotificationPayload) => void): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  addConnectionListener(listener: (connected: boolean) => void): void {
    this.connectionListeners.push(listener);
  }

  removeConnectionListener(listener: (connected: boolean) => void): void {
    const index = this.connectionListeners.indexOf(listener);
    if (index > -1) {
      this.connectionListeners.splice(index, 1);
    }
  }

  private notifyListeners(notification: NotificationPayload): void {
    this.listeners.forEach(listener => {
      try {
        listener(notification);
      } catch (error) {
        console.error('Error in notification listener:', error);
      }
    });
  }

  private notifyConnectionListeners(connected: boolean): void {
    this.connectionListeners.forEach(listener => {
      try {
        listener(connected);
      } catch (error) {
        console.error('Error in connection listener:', error);
      }
    });
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }
}

export const websocketService = new WebSocketService(); 