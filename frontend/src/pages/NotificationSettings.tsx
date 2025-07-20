import React, { useState, useEffect } from 'react';
import { useAppState } from '../contexts/AppStateContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  getNotificationPreferences, 
  updateNotificationPreferences, 
  getNotificationStatus, 
  sendTestEmail,
  type NotificationPreferences,
  type NotificationStatus
} from '../services/notifications';
import { getUser } from '../services/auth';
import { 
  FaBell, 
  FaEnvelope, 
  FaGlobe, 
  FaWifi, 
  FaCheck, 
  FaTimes, 
  FaSpinner,
  FaMobile,
  FaDesktop,
  FaShieldAlt
} from 'react-icons/fa';

export default function NotificationSettings() {
  const { dispatch } = useAppState();
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [status, setStatus] = useState<NotificationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [formData, setFormData] = useState<Partial<NotificationPreferences>>({});

  // Get current user for WebSocket connection
  const user = getUser();
  const userId = user?.sub ? parseInt(user.sub) : 0;

  // WebSocket connection for real-time status
  const { isConnected, requestNotificationPermission } = useWebSocket({
    userId,
    onMessage: (message) => {
      // Update status when we receive messages
      loadNotificationStatus();
    }
  });

  // Load notification preferences and status
  const loadData = async () => {
    try {
      setLoading(true);
      const [prefs, stat] = await Promise.all([
        getNotificationPreferences(),
        getNotificationStatus()
      ]);
      setPreferences(prefs);
      setStatus(stat);
      setFormData(prefs);
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to load notification settings' 
      });
    } finally {
      setLoading(false);
    }
  };

  const loadNotificationStatus = async () => {
    try {
      const stat = await getNotificationStatus();
      setStatus(stat);
    } catch (error) {
      console.error('Failed to load notification status:', error);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Handle form changes
  const handleInputChange = (field: keyof NotificationPreferences, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Save preferences
  const handleSave = async () => {
    try {
      setSaving(true);
      const updatedPrefs = await updateNotificationPreferences(formData);
      setPreferences(updatedPrefs);
      setFormData(updatedPrefs);
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Notification settings saved successfully', type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to save notification settings' 
      });
    } finally {
      setSaving(false);
    }
  };

  // Test email notification
  const handleTestEmail = async () => {
    try {
      setTestingEmail(true);
      await sendTestEmail();
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Test email sent successfully', type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to send test email' 
      });
    } finally {
      setTestingEmail(false);
    }
  };

  // Request browser notification permission
  const handleRequestPermission = async () => {
    const granted = await requestNotificationPermission();
    if (granted) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Browser notifications enabled', type: 'success' } 
      });
    } else {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Browser notifications denied' 
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="animate-spin text-4xl text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading notification settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <FaBell className="mr-3 text-blue-600" />
            Notification Settings
          </h1>
          <p className="mt-2 text-gray-600">
            Configure how you receive alerts and notifications from PFCAM
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Settings */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Notification Preferences</h2>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Email Notifications */}
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <FaEnvelope className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">Email Notifications</h3>
                        <p className="text-sm text-gray-500">
                          Receive email alerts for events and system updates
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.email_notifications || false}
                          onChange={(e) => handleInputChange('email_notifications', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                    
                    {formData.email_notifications && (
                      <div className="mt-3">
                        <button
                          onClick={handleTestEmail}
                          disabled={testingEmail}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                          {testingEmail ? (
                            <>
                              <FaSpinner className="animate-spin mr-1" />
                              Sending...
                            </>
                          ) : (
                            'Send Test Email'
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Event Notifications */}
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <FaBell className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">Event Notifications</h3>
                        <p className="text-sm text-gray-500">
                          Get notified when cameras capture new events
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.event_notifications || false}
                          onChange={(e) => handleInputChange('event_notifications', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Camera Status Notifications */}
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <FaWifi className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">Camera Status</h3>
                        <p className="text-sm text-gray-500">
                          Alerts when cameras go offline or come back online
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.camera_status_notifications || false}
                          onChange={(e) => handleInputChange('camera_status_notifications', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* System Alerts */}
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <FaShieldAlt className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">System Alerts</h3>
                        <p className="text-sm text-gray-500">
                          Important system notifications and security alerts
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.system_alerts || false}
                          onChange={(e) => handleInputChange('system_alerts', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Webhook URL */}
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <FaGlobe className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Webhook URL (Optional)</h3>
                      <p className="text-sm text-gray-500 mb-2">
                        Send notifications to external systems via webhook
                      </p>
                      <input
                        type="url"
                        placeholder="https://your-webhook-url.com/notifications"
                        value={formData.webhook_url || ''}
                        onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Save Button */}
                <div className="pt-4">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {saving ? (
                      <>
                        <FaSpinner className="animate-spin mr-2" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <FaCheck className="mr-2" />
                        Save Settings
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Status Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Connection Status</h2>
              </div>
              
              <div className="p-6 space-y-4">
                {/* WebSocket Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FaWifi className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900">Real-time Connection</span>
                  </div>
                  <div className="flex items-center">
                    {isConnected ? (
                      <FaCheck className="w-4 h-4 text-green-500" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                </div>

                {/* Email Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FaEnvelope className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900">Email Service</span>
                  </div>
                  <div className="flex items-center">
                    {status?.email_enabled ? (
                      <FaCheck className="w-4 h-4 text-green-500" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                </div>

                {/* Browser Notifications */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FaBell className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900">Browser Notifications</span>
                  </div>
                  <div className="flex items-center">
                    {Notification.permission === 'granted' ? (
                      <FaCheck className="w-4 h-4 text-green-500" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                </div>

                {/* Mobile Optimization */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FaMobile className="w-5 h-5 text-gray-400 mr-2" />
                    <span className="text-sm font-medium text-gray-900">Mobile Optimized</span>
                  </div>
                  <div className="flex items-center">
                    <FaCheck className="w-4 h-4 text-green-500" />
                  </div>
                </div>

                {/* Browser Notifications Permission */}
                {Notification.permission !== 'granted' && (
                  <div className="pt-4">
                    <button
                      onClick={handleRequestPermission}
                      className="w-full inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <FaBell className="mr-2" />
                      Enable Browser Notifications
                    </button>
                  </div>
                )}

                {/* Active Connections */}
                {status && (
                  <div className="pt-4 border-t border-gray-200">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{status.active_connections}</div>
                      <div className="text-sm text-gray-500">Active Connections</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 