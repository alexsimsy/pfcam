import React, { useState } from 'react';
import { fetchApplicationSettings, updateApplicationSettings, resetApplicationSettings } from '../services/settings';
import type { ApplicationSettings } from '../services/settings';
import { useApi } from '../hooks/useApi';
import { useAppState } from '../contexts/AppStateContext';

export default function Settings() {
  const { dispatch } = useAppState();
  const [saving, setSaving] = useState(false);

  const { data: settings, loading, error } = useApi(
    fetchApplicationSettings,
    [], // Empty dependencies - only fetch once
    {
      onError: (err) => {
        dispatch({ type: 'ADD_ERROR', payload: err.message });
        // Set default settings if API fails
        return {
          id: 1,
          auto_start_streams: false,
          stream_quality: 'medium',
          store_data_on_camera: true,
          auto_download_events: false,
          auto_download_snapshots: false,
          event_retention_days: 30,
          snapshot_retention_days: 7,
          mobile_data_saving: true,
          low_bandwidth_mode: false,
          created_at: new Date().toISOString(),
        };
      }
    }
  );

  const updateSetting = async (field: keyof ApplicationSettings, value: any) => {
    if (!settings) return;
    
    setSaving(true);
    
    try {
      await updateApplicationSettings({ [field]: value });
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Settings updated successfully', type: 'success' } 
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
        {/* Streaming Settings */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Streaming Settings</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Auto-start Streams</h3>
                <p className="text-sm text-simsy-text">Automatically start camera streams when viewing cameras</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.auto_start_streams}
                  onChange={(e) => updateSetting('auto_start_streams', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Stream Quality</h3>
                <p className="text-sm text-simsy-text">Default quality for camera streams</p>
              </div>
              <select
                value={settings.stream_quality}
                onChange={(e) => updateSetting('stream_quality', e.target.value)}
                disabled={saving}
                className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
        </div>

        {/* Storage Settings */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Storage Settings</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Store Data on Camera</h3>
                <p className="text-sm text-simsy-text">Keep events and snapshots stored on the camera</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.store_data_on_camera}
                  onChange={(e) => updateSetting('store_data_on_camera', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Auto-download Events</h3>
                <p className="text-sm text-simsy-text">Automatically download events to application storage</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.auto_download_events}
                  onChange={(e) => updateSetting('auto_download_events', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Auto-download Snapshots</h3>
                <p className="text-sm text-simsy-text">Automatically download snapshots to application storage</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.auto_download_snapshots}
                  onChange={(e) => updateSetting('auto_download_snapshots', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Data Retention Settings */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Data Retention</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Event Retention (days)</h3>
                <p className="text-sm text-simsy-text">How long to keep events in storage</p>
              </div>
              <input
                type="number"
                min="1"
                max="365"
                value={settings.event_retention_days}
                onChange={(e) => updateSetting('event_retention_days', parseInt(e.target.value))}
                disabled={saving}
                className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none w-20"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Snapshot Retention (days)</h3>
                <p className="text-sm text-simsy-text">How long to keep snapshots in storage</p>
              </div>
              <input
                type="number"
                min="1"
                max="365"
                value={settings.snapshot_retention_days}
                onChange={(e) => updateSetting('snapshot_retention_days', parseInt(e.target.value))}
                disabled={saving}
                className="bg-simsy-dark text-simsy-text px-3 py-2 rounded border border-simsy-dark focus:border-simsy-blue focus:outline-none w-20"
              />
            </div>
          </div>
        </div>

        {/* Mobile Optimization Settings */}
        <div className="bg-simsy-card rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-simsy-blue mb-4">Mobile Optimization</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Mobile Data Saving</h3>
                <p className="text-sm text-simsy-text">Optimize for mobile data usage</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.mobile_data_saving}
                  onChange={(e) => updateSetting('mobile_data_saving', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-simsy-text">Low Bandwidth Mode</h3>
                <p className="text-sm text-simsy-text">Reduce bandwidth usage for slow connections</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.low_bandwidth_mode}
                  onChange={(e) => updateSetting('low_bandwidth_mode', e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-simsy-dark peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-simsy-blue"></div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 