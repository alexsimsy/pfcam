import React, { useState, useEffect } from 'react';
import { fetchApplicationSettings, updateApplicationSettings, resetApplicationSettings } from '../services/settings';
import type { ApplicationSettings } from '../services/settings';
import { fetchUsers, createUser, updateUser, deleteUser, activateUser, deactivateUser } from '../services/users';
import type { User, UserCreate, UserUpdate } from '../services/users';
import { useApi } from '../hooks/useApi';
import { useAppState } from '../contexts/AppStateContext';
import { fetchCameras } from '../services/cameras';
import type { Camera } from '../services/cameras';
import { fetchCameraSettings, updateCameraSettings, type CameraSettings } from '../services/cameraSettings';

export default function Settings() {
  const { dispatch } = useAppState();
  const [saving, setSaving] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userFormData, setUserFormData] = useState<UserCreate>({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'viewer'
  });
  const [localSettings, setLocalSettings] = useState<ApplicationSettings | null>(null);

  
  // Camera-specific settings state
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(null);
  const [cameraSettings, setCameraSettings] = useState<Record<string, CameraSettings>>({});
  const [localCameraSettings, setLocalCameraSettings] = useState<CameraSettings | null>(null);

  const { data: settings, loading, error } = useApi(
    fetchApplicationSettings,
    [],
    {
      onSuccess: (data) => setLocalSettings(data),
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  const { data: users, loading: usersLoading, error: usersError } = useApi(
    fetchUsers,
    [], // Empty dependencies - only fetch once
    {
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  const { data: cameras } = useApi(
    fetchCameras,
    [],
    {
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  // Load camera settings for selected camera
  const { data: cameraSettingsData, loading: cameraSettingsLoading } = useApi(
    () => selectedCameraId ? fetchCameraSettings(selectedCameraId) : Promise.resolve(null),
    [selectedCameraId],
    {
      onSuccess: (data) => {
        console.log('Camera settings loaded for camera', selectedCameraId, ':', data);
        if (data) {
          console.log('Setting local camera settings to:', data.settings);
          setLocalCameraSettings(data.settings);
        }
      },
      onError: (err) => {
        console.error('Failed to load camera settings:', err);
        dispatch({ type: 'ADD_ERROR', payload: err.message })
      }
    }
  );

  // Update local settings when settings data changes
  React.useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
    }
  }, [settings]);



  const getDefaultCameraSettings = (): CameraSettings => ({
    live_quality_level: 50,
    recording_quality_level: 50,
    heater_level: 0,
    picture_rotation: 90,
    recording_seconds_pre_event: 10,
    recording_seconds_post_event: 10,
    rtsp_quality_level: 50
  });

  const updateSetting = async (field: keyof ApplicationSettings, value: any) => {
    if (!settings) return;
    
    setSaving(true);
    
    try {
      const updatedSettings = await updateApplicationSettings({ [field]: value });
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Settings updated successfully', type: 'success' } 
      });
      // Update local state with the response from the API
      if (updatedSettings) {
        setLocalSettings(updatedSettings);
      }
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  const updateCameraSetting = async (field: keyof CameraSettings, value: any) => {
    if (!selectedCameraId || !localCameraSettings) return;
    
    setSaving(true);
    
    try {
      const updatedSettings = await updateCameraSettings(selectedCameraId, { [field]: value });
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Camera settings updated successfully', type: 'success' } 
      });
      
      // Update local state with the response from the API (actual camera values)
      if (updatedSettings) {
        setLocalCameraSettings(updatedSettings.settings);
      }
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  const resetSettings = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
      return;
    }
    
    setSaving(true);
    
    try {
      await resetApplicationSettings();
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Settings reset to defaults', type: 'success' } 
      });
      // Reload page to get updated settings
      window.location.reload();
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUserFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      if (editingUser) {
        await updateUser(editingUser.id, userFormData as UserUpdate);
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { message: 'User updated successfully', type: 'success' } 
        });
      } else {
        await createUser(userFormData);
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { message: 'User created successfully', type: 'success' } 
        });
      }
      
      setShowUserForm(false);
      setEditingUser(null);
      setUserFormData({
        email: '',
        username: '',
        password: '',
        full_name: '',
        role: 'viewer'
      });
      // Reload page to refresh users
      window.location.reload();
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }
    
    setSaving(true);
    try {
      await deleteUser(userId);
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'User deleted successfully', type: 'success' } 
      });
      // Reload page to refresh users
      window.location.reload();
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    setSaving(true);
    try {
      if (user.is_active) {
        await deactivateUser(user.id);
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { message: 'User deactivated successfully', type: 'success' } 
        });
      } else {
        await activateUser(user.id);
        dispatch({ 
          type: 'ADD_NOTIFICATION', 
          payload: { message: 'User activated successfully', type: 'success' } 
        });
      }
      // Reload page to refresh users
      window.location.reload();
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message, type: 'error' } 
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <h1 className="text-4xl font-bold mb-4">Settings</h1>
        <div>Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h1 className="text-4xl font-bold mb-4">Settings</h1>
        <div className="text-red-500">Error: {error.message}</div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div>
        <h1 className="text-4xl font-bold mb-4">Settings</h1>
        <div className="text-red-500">Failed to load settings</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-4xl font-bold">Settings</h1>
        <button
          onClick={resetSettings}
          disabled={saving}
          className="bg-red-600 text-white font-bold py-2 px-4 rounded hover:bg-red-700 transition disabled:opacity-50"
        >
          {saving ? 'Resetting...' : 'Reset to Defaults'}
        </button>
      </div>

      <div className="space-y-6">
        {/* Application Settings Section */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Application Settings</h2>
          <p className="text-sm text-simsy-text mb-6">These settings apply to the entire application and affect all cameras.</p>
          
          <div className="space-y-6">
            {/* Data Retention Settings */}
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-simsy-text">Data Retention (Server Only)</h3>
              
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-simsy-text">Enable Data Retention Policy</h4>
                  <p className="text-sm text-simsy-text">Automatically delete old events and snapshots based on retention settings</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={localSettings ? localSettings.data_retention_enabled : true}
                    onChange={(e) => {
                      setLocalSettings(prev => prev ? { ...prev, data_retention_enabled: e.target.checked } : null);
                      updateSetting('data_retention_enabled', e.target.checked);
                    }}
                    disabled={saving}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
                </label>
              </div>
            </div>

            {/* Retention Period Settings */}
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-simsy-text">Retention Periods</h3>
              
              {!localSettings?.data_retention_enabled && (
                <div className="bg-simsy-dark p-3 rounded border border-simsy-dark">
                  <p className="text-sm text-simsy-text">
                    <span className="font-semibold">Data retention is disabled.</span> Events and snapshots will be kept indefinitely.
                  </p>
                </div>
              )}
              
              <div className="flex items-center justify-between">
                <div>
                  <h4 className={`font-semibold ${!localSettings?.data_retention_enabled ? 'text-gray-500' : 'text-simsy-text'}`}>
                    Event Retention (days)
                  </h4>
                  <p className={`text-sm ${!localSettings?.data_retention_enabled ? 'text-gray-500' : 'text-simsy-text'}`}>
                    How long to keep events in storage
                  </p>
                </div>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={localSettings?.event_retention_days || 30}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || 30;
                    setLocalSettings(prev => prev ? { ...prev, event_retention_days: value } : null);
                  }}
                  onBlur={(e) => {
                    const value = parseInt(e.target.value) || 30;
                    updateSetting('event_retention_days', value);
                  }}
                  disabled={saving || !localSettings?.data_retention_enabled}
                  className={`px-3 py-2 rounded border focus:outline-none w-20 ${
                    !localSettings?.data_retention_enabled 
                      ? 'bg-gray-700 text-gray-500 border-gray-600 cursor-not-allowed' 
                      : 'bg-simsy-dark text-simsy-text border-simsy-dark focus:border-simsy-blue'
                  }`}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className={`font-semibold ${!localSettings?.data_retention_enabled ? 'text-gray-500' : 'text-simsy-text'}`}>
                    Snapshot Retention (days)
                  </h4>
                  <p className={`text-sm ${!localSettings?.data_retention_enabled ? 'text-gray-500' : 'text-simsy-text'}`}>
                    How long to keep snapshots in storage
                  </p>
                </div>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={localSettings?.snapshot_retention_days || 7}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || 7;
                    setLocalSettings(prev => prev ? { ...prev, snapshot_retention_days: value } : null);
                  }}
                  onBlur={(e) => {
                    const value = parseInt(e.target.value) || 7;
                    updateSetting('snapshot_retention_days', value);
                  }}
                  disabled={saving || !localSettings?.data_retention_enabled}
                  className={`px-3 py-2 rounded border focus:outline-none w-20 ${
                    !localSettings?.data_retention_enabled 
                      ? 'bg-gray-700 text-gray-500 border-gray-600 cursor-not-allowed' 
                      : 'bg-simsy-dark text-simsy-text border-simsy-dark focus:border-simsy-blue'
                  }`}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Camera Settings Section */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Camera Settings</h2>
          <p className="text-sm text-simsy-text mb-6">These settings apply to individual cameras. Select a camera to configure its settings.</p>
          
          {/* Camera Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-simsy-text mb-2">
              Select Camera
            </label>
            <select
              value={selectedCameraId || ''}
              onChange={(e) => setSelectedCameraId(e.target.value ? parseInt(e.target.value) : null)}
              className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none w-full"
            >
              <option value="">Select a camera...</option>
              {cameras?.map((camera) => (
                <option key={camera.id} value={camera.id}>
                  {camera.name} ({camera.ip_address})
                </option>
              ))}
            </select>
          </div>

          {selectedCameraId && (
            <div className="space-y-6">
              {!localCameraSettings && (
                <div className="text-center py-4">
                  <div className="text-simsy-text">Loading camera settings...</div>
                </div>
              )}
              {localCameraSettings && (
                <>
                  {/* Streaming Settings */}
                  <div className="space-y-4">
                <h3 className="text-xl font-semibold text-simsy-text">Streaming Settings</h3>
                
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-simsy-text">Live Stream Quality</h4>
                    <span className="text-sm text-simsy-text">{localCameraSettings.live_quality_level || 50}</span>
                  </div>
                  <p className="text-sm text-simsy-text mb-3">Quality level for live camera streams (1-100)</p>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={localCameraSettings.live_quality_level || 50}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 50;
                      setLocalCameraSettings(prev => prev ? { ...prev, live_quality_level: value } : null);
                    }}
                    onMouseUp={async (e) => {
                      const value = parseInt(e.currentTarget.value) || 50;
                      await updateCameraSetting('live_quality_level', value);
                      await updateCameraSetting('rtsp_quality_level', value);
                    }}
                    disabled={saving}
                    className="w-full h-2 bg-simsy-dark rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-simsy-text">Recording Quality</h4>
                    <span className="text-sm text-simsy-text">{localCameraSettings.recording_quality_level || 50}</span>
                  </div>
                  <p className="text-sm text-simsy-text mb-3">Quality level for recorded events (1-100)</p>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={localCameraSettings.recording_quality_level || 50}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 50;
                      setLocalCameraSettings(prev => prev ? { ...prev, recording_quality_level: value } : null);
                    }}
                    onMouseUp={async (e) => {
                      const value = parseInt(e.currentTarget.value) || 50;
                      await updateCameraSetting('recording_quality_level', value);
                    }}
                    disabled={saving}
                    className="w-full h-2 bg-simsy-dark rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              </div>

              {/* Camera Hardware Settings */}
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-simsy-text">Camera Hardware Settings</h3>
                
                <div>
                  <h4 className="font-semibold text-simsy-text mb-3">Heater Level</h4>
                  <p className="text-sm text-simsy-text mb-3">Camera heater setting for cold weather operation</p>
                  <div className="flex gap-4">
                    {[
                      { value: 0, label: 'Off' },
                      { value: 1, label: 'Low' },
                      { value: 2, label: 'Med' },
                      { value: 3, label: 'High' }
                    ].map((option) => (
                      <label key={option.value} className="flex items-center cursor-pointer">
                        <input
                          type="radio"
                          name="heater_level"
                          value={option.value}
                          checked={localCameraSettings.heater_level === option.value}
                          onChange={async (e) => {
                            const value = parseInt(e.target.value);
                            setLocalCameraSettings(prev => prev ? { ...prev, heater_level: value } : null);
                            await updateCameraSetting('heater_level', value);
                          }}
                          disabled={saving}
                          className="mr-2"
                        />
                        <span className="text-simsy-text">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-simsy-text mb-3">Picture Rotation</h4>
                  <p className="text-sm text-simsy-text mb-3">Rotate camera image orientation</p>
                  <div className="flex gap-4">
                    {[
                      { value: 0, label: '0°' },
                      { value: 90, label: '90°' },
                      { value: 180, label: '180°' },
                      { value: 270, label: '270°' }
                    ].map((option) => (
                      <label key={option.value} className="flex items-center cursor-pointer">
                        <input
                          type="radio"
                          name="picture_rotation"
                          value={option.value}
                          checked={localCameraSettings.picture_rotation === option.value}
                          onChange={async (e) => {
                            const value = parseInt(e.target.value);
                            setLocalCameraSettings(prev => prev ? { ...prev, picture_rotation: value } : null);
                            await updateCameraSetting('picture_rotation', value);
                          }}
                          disabled={saving}
                          className="mr-2"
                        />
                        <span className="text-simsy-text">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Event Recording Settings */}
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-simsy-text">Event Recording Settings</h3>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-simsy-text">Pre-event Recording (seconds)</h4>
                    <p className="text-sm text-simsy-text">How many seconds to record before an event is triggered</p>
                  </div>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={localCameraSettings.recording_seconds_pre_event || 10}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 10;
                      setLocalCameraSettings(prev => prev ? { ...prev, recording_seconds_pre_event: value } : null);
                    }}
                    onBlur={async (e) => {
                      const value = parseInt(e.target.value) || 10;
                      await updateCameraSetting('recording_seconds_pre_event', value);
                    }}
                    disabled={saving}
                    className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none w-20"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-simsy-text">Post-event Recording (seconds)</h4>
                    <p className="text-sm text-simsy-text">How many seconds to record after an event is triggered</p>
                  </div>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={localCameraSettings.recording_seconds_post_event || 10}
                    onChange={(e) => {
                      const value = parseInt(e.target.value) || 10;
                      setLocalCameraSettings(prev => prev ? { ...prev, recording_seconds_post_event: value } : null);
                    }}
                    onBlur={async (e) => {
                      const value = parseInt(e.target.value) || 10;
                      await updateCameraSetting('recording_seconds_post_event', value);
                    }}
                    disabled={saving}
                    className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none w-20"
                  />
                </div>
              </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* User Management */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-simsy-blue">User Management</h2>
            <button
              onClick={() => setShowUserForm(true)}
              disabled={saving}
              className="bg-simsy-blue text-white font-bold py-2 px-4 rounded hover:bg-simsy-dark hover:text-simsy-blue transition disabled:opacity-50"
            >
              Add User
            </button>
          </div>
          
          {usersLoading && <div>Loading users...</div>}
          {usersError && <div className="text-red-500">Error: {usersError.message}</div>}
          
          {!usersLoading && !usersError && users && (
            <div className="space-y-4">
              <table className="min-w-full bg-simsy-dark text-simsy-text rounded-lg overflow-hidden">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left">Username</th>
                    <th className="px-4 py-2 text-left">Email</th>
                    <th className="px-4 py-2 text-left">Full Name</th>
                    <th className="px-4 py-2 text-left">Role</th>
                    <th className="px-4 py-2 text-left">Status</th>
                    <th className="px-4 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-t border-simsy-dark">
                      <td className="px-4 py-2">{user.username}</td>
                      <td className="px-4 py-2">{user.email}</td>
                      <td className="px-4 py-2">{user.full_name}</td>
                      <td className="px-4 py-2 capitalize">{user.role}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleToggleUserStatus(user)}
                            disabled={saving}
                            className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-red-600 text-white' : 'bg-green-600 text-white'} hover:opacity-80 disabled:opacity-50`}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={saving}
                            className="bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700 disabled:opacity-50"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* User Form Modal */}
      {showUserForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-simsy-card rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">{editingUser ? 'Edit User' : 'Add User'}</h3>
            <form onSubmit={handleUserFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-simsy-text mb-1">Email</label>
                <input
                  type="email"
                  value={userFormData.email}
                  onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
                  required
                  className="w-full bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-simsy-text mb-1">Username</label>
                <input
                  type="text"
                  value={userFormData.username}
                  onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
                  required
                  className="w-full bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-simsy-text mb-1">Full Name</label>
                <input
                  type="text"
                  value={userFormData.full_name}
                  onChange={(e) => setUserFormData({ ...userFormData, full_name: e.target.value })}
                  required
                  className="w-full bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
                />
              </div>
              {!editingUser && (
                <div>
                  <label className="block text-sm font-medium text-simsy-text mb-1">Password</label>
                  <input
                    type="password"
                    value={userFormData.password}
                    onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
                    required
                    className="w-full bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-simsy-text mb-1">Role</label>
                <select
                  value={userFormData.role}
                  onChange={(e) => setUserFormData({ ...userFormData, role: e.target.value as any })}
                  className="w-full bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
                >
                  <option value="viewer">Viewer</option>
                  <option value="operator">Operator</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-simsy-blue text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : (editingUser ? 'Update' : 'Create')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowUserForm(false);
                    setEditingUser(null);
                    setUserFormData({
                      email: '',
                      username: '',
                      password: '',
                      full_name: '',
                      role: 'viewer'
                    });
                  }}
                  className="bg-simsy-dark text-simsy-text px-4 py-2 rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
} 