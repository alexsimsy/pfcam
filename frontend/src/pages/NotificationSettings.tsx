import React, { useState, useEffect } from 'react';
import { useAppState } from '../contexts/AppStateContext';
import { useNotifications } from '../contexts/NotificationContext';
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
  const { isConnected } = useNotifications();

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

  // Handle form changes and save immediately
  const handleInputChange = async (field: keyof NotificationPreferences, value: any) => {
    const updatedFormData = {
      ...formData,
      [field]: value
    };
    
    setFormData(updatedFormData);
    
    // Save immediately
    try {
      setSaving(true);
      const updatedPrefs = await updateNotificationPreferences(updatedFormData);
      setPreferences(updatedPrefs);
      setFormData(updatedPrefs);
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Setting updated', type: 'success' } 
      });
    } catch (error) {
      // Revert on error
      setFormData(preferences || {});
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to save setting' 
      });
    } finally {
      setSaving(false);
    }
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
    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
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
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to request notification permission' 
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-simsy-bg flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="animate-spin text-4xl text-simsy-blue mx-auto mb-4" />
          <p className="text-simsy-text">Loading notification settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-simsy-bg min-h-screen">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-simsy-text flex items-center">
            <FaBell className="mr-3 text-simsy-blue" />
            Notification Settings
          </h1>
          <p className="mt-2 text-simsy-text">
            Configure how you receive alerts and notifications from Event Cam
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Settings */}
          <div className="lg:col-span-2">
            <div className="bg-simsy-card rounded-xl shadow-lg">
              <div className="px-6 py-4 border-b border-simsy-dark">
                <h2 className="text-lg font-semibold text-simsy-blue">Notification Preferences</h2>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Email Notifications */}
                <div className="flex items-start space-x-4 p-4 bg-simsy-dark/20 rounded-lg">
                  <div className="flex-shrink-0">
                    <FaEnvelope className="w-6 h-6 text-simsy-blue" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-simsy-text">Email Notifications</h3>
                        <p className="text-sm text-simsy-text">
                          Receive email alerts for events and system updates
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.email_notifications || false}
                          onChange={(e) => handleInputChange('email_notifications', e.target.checked)}
                          disabled={saving}
                        />
                        <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-simsy-blue rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-simsy-dark after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
                      </label>
                    </div>
                    
                    {formData.email_notifications && (
                      <div className="mt-3">
                        <button
                          onClick={handleTestEmail}
                          disabled={testingEmail}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-simsy-blue bg-simsy-blue/10 hover:bg-simsy-blue/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-simsy-blue disabled:opacity-50"
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
                <div className="flex items-start space-x-4 p-4 bg-simsy-dark/20 rounded-lg">
                  <div className="flex-shrink-0">
                    <FaBell className="w-6 h-6 text-simsy-blue" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-simsy-text">Event Notifications</h3>
                        <p className="text-sm text-simsy-text">
                          Get notified when cameras capture new events
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.event_notifications || false}
                          onChange={(e) => handleInputChange('event_notifications', e.target.checked)}
                          disabled={saving}
                        />
                        <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-simsy-blue rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-simsy-dark after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Camera Status Notifications */}
                <div className="flex items-start space-x-4 p-4 bg-simsy-dark/20 rounded-lg">
                  <div className="flex-shrink-0">
                    <FaWifi className="w-6 h-6 text-simsy-blue" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-simsy-text">Camera Status</h3>
                        <p className="text-sm text-simsy-text">
                          Alerts when cameras go offline or come back online
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.camera_status_notifications || false}
                          onChange={(e) => handleInputChange('camera_status_notifications', e.target.checked)}
                          disabled={saving}
                        />
                        <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-simsy-blue rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-simsy-dark after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* System Alerts */}
                <div className="flex items-start space-x-4 p-4 bg-simsy-dark/20 rounded-lg">
                  <div className="flex-shrink-0">
                    <FaShieldAlt className="w-6 h-6 text-simsy-blue" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-simsy-text">System Alerts</h3>
                        <p className="text-sm text-simsy-text">
                          Important system notifications and security alerts
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={formData.system_alerts || false}
                          onChange={(e) => handleInputChange('system_alerts', e.target.checked)}
                          disabled={saving}
                        />
                        <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-simsy-blue rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-simsy-dark after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Webhook URL */}
                <div className="flex items-start space-x-4 p-4 bg-simsy-dark/20 rounded-lg">
                  <div className="flex-shrink-0">
                    <FaGlobe className="w-6 h-6 text-simsy-blue" />
                  </div>
                  <div className="flex-1">
                    <div>
                      <h3 className="text-sm font-medium text-simsy-text">Webhook URL (Optional)</h3>
                      <p className="text-sm text-simsy-text mb-2">
                        Send notifications to external systems via webhook
                      </p>
                      <input
                        type="url"
                        placeholder="https://your-webhook-url.com/notifications"
                        value={formData.webhook_url || ''}
                        onChange={(e) => handleInputChange('webhook_url', e.target.value)}
                        className="w-full px-3 py-2 border border-simsy-dark rounded-md shadow-sm focus:outline-none focus:ring-simsy-blue focus:border-simsy-blue bg-simsy-dark text-simsy-text"
                      />
                    </div>
                  </div>
                </div>

                {/* Auto-save indicator */}
                {saving && (
                  <div className="pt-4">
                    <div className="flex items-center justify-center text-simsy-blue">
                      <FaSpinner className="animate-spin mr-2" />
                      <span className="text-sm">Saving...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Status Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-simsy-card rounded-xl shadow-lg">
              <div className="px-6 py-4 border-b border-simsy-dark">
                <h2 className="text-lg font-semibold text-simsy-blue">Connection Status</h2>
              </div>
              
              <div className="p-6 space-y-4">
                {/* WebSocket Status */}
                <div className="flex items-center justify-between p-3 bg-simsy-dark/20 rounded-lg">
                  <div className="flex items-center">
                    <FaWifi className="w-5 h-5 text-simsy-blue mr-2" />
                    <span className="text-sm font-medium text-simsy-text">Real-time Connection</span>
                  </div>
                  <div className="flex items-center">
                    {isConnected ? (
                      <FaCheck className="w-4 h-4 text-green-400" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </div>

                {/* Email Status */}
                <div className="flex items-center justify-between p-3 bg-simsy-dark/20 rounded-lg">
                  <div className="flex items-center">
                    <FaEnvelope className="w-5 h-5 text-simsy-blue mr-2" />
                    <span className="text-sm font-medium text-simsy-text">Email Service</span>
                  </div>
                  <div className="flex items-center">
                    {status?.email_enabled ? (
                      <FaCheck className="w-4 h-4 text-green-400" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </div>

                {/* Browser Notifications */}
                <div className="flex items-center justify-between p-3 bg-simsy-dark/20 rounded-lg">
                  <div className="flex items-center">
                    <FaBell className="w-5 h-5 text-simsy-blue mr-2" />
                    <span className="text-sm font-medium text-simsy-text">Browser Notifications</span>
                  </div>
                  <div className="flex items-center">
                    {Notification.permission === 'granted' ? (
                      <FaCheck className="w-4 h-4 text-green-400" />
                    ) : (
                      <FaTimes className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </div>

                {/* Mobile Optimization */}
                <div className="flex items-center justify-between p-3 bg-simsy-dark/20 rounded-lg">
                  <div className="flex items-center">
                    <FaMobile className="w-5 h-5 text-simsy-blue mr-2" />
                    <span className="text-sm font-medium text-simsy-text">Mobile Optimized</span>
                  </div>
                  <div className="flex items-center">
                    <FaCheck className="w-4 h-4 text-green-400" />
                  </div>
                </div>

                {/* Browser Notifications Permission */}
                {Notification.permission !== 'granted' && (
                  <div className="pt-4">
                    <button
                      onClick={handleRequestPermission}
                      className="w-full inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-simsy-blue bg-simsy-blue/10 hover:bg-simsy-blue/20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-simsy-blue"
                    >
                      <FaBell className="mr-2" />
                      Enable Browser Notifications
                    </button>
                  </div>
                )}

                {/* Active Connections */}
                {status && (
                  <div className="pt-4 border-t border-simsy-dark">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-simsy-blue">{status.active_connections}</div>
                      <div className="text-sm text-simsy-text">Active Connections</div>
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