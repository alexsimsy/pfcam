import React, { useState } from 'react';
import { fetchCameras, createCamera } from '../services/cameras';
import { fetchCameraStreams, getStreamSnapshot } from '../services/streams';
import { fetchDashboardStats } from '../services/dashboard';
import type { Camera } from '../services/cameras';
import type { StreamList, SnapshotResponse } from '../services/streams';
import type { DashboardStats } from '../services/dashboard';
import { useApi } from '../hooks/useApi';
import { useAppState } from '../contexts/AppStateContext';

export default function Dashboard() {
  const { dispatch } = useAppState();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '',
    ip_address: '',
    port: 80,
    model: '',
    base_url: '',
  });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<number | null>(null);
  const [streams, setStreams] = useState<StreamList | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState<number | null>(null);
  const [snapshotUrl, setSnapshotUrl] = useState<string | null>(null);

  const { data: cameras, loading, error } = useApi(
    fetchCameras,
    [], // Empty dependencies - only fetch once
    {
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  const { data: stats, loading: statsLoading } = useApi(
    fetchDashboardStats,
    [], // Empty dependencies - only fetch once
    {
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleAddCamera = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    try {
      // base_url must start with http:// or https://
      const base_url = form.base_url.startsWith('http') ? form.base_url : `http://${form.base_url}`;
      await createCamera({ ...form, port: Number(form.port), base_url, use_ssl: base_url.startsWith('https') });
      setShowForm(false);
      setForm({ name: '', ip_address: '', port: 80, model: '', base_url: '' });
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Camera added successfully', type: 'success' } 
      });
      // Refetch cameras by reloading the page for now
      window.location.reload();
    } catch (err: any) {
      setFormError(err.message || 'Failed to add camera');
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: err.message || 'Failed to add camera', type: 'error' } 
      });
    } finally {
      setFormLoading(false);
    }
  };

  const handleCameraClick = async (cameraId: number) => {
    if (selectedCamera === cameraId) {
      setSelectedCamera(null);
      setStreams(null);
      setSnapshotUrl(null);
      return;
    }

    setSelectedCamera(cameraId);
    setSnapshotUrl(null);
    
    try {
      const streamData = await fetchCameraStreams(cameraId);
      setStreams(streamData);
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: `Failed to load streams: ${err.message}`, type: 'error' } 
      });
    }
  };

  const handleTakeSnapshot = async (cameraId: number, streamName: string) => {
    setSnapshotLoading(cameraId);
    setSnapshotUrl(null);
    
    try {
      const snapshot: SnapshotResponse = await getStreamSnapshot(cameraId, streamName);
      setSnapshotUrl(snapshot.snapshot_url);
    } catch (err: any) {
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: `Failed to take snapshot: ${err.message}`, type: 'error' } 
      });
    } finally {
      setSnapshotLoading(null);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">Dashboard</h1>
      
      {/* Status Overview */}
      {!statsLoading && stats && (
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Camera Status */}
          <div className="bg-simsy-card p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-simsy-text text-sm font-medium">Cameras</p>
                <p className="text-3xl font-bold text-simsy-blue">{stats.cameras.total}</p>
                <p className="text-sm text-green-400">
                  {stats.cameras.online} online
                </p>
                {stats.cameras.offline > 0 && (
                  <p className="text-sm text-red-400">
                    {stats.cameras.offline} offline
                  </p>
                )}
              </div>
              <div className="w-12 h-12 bg-simsy-blue/10 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-simsy-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect x="3" y="7" width="18" height="13" rx="2"/>
                  <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  <circle cx="12" cy="13.5" r="3.5"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Events Last 24h */}
          <div className="bg-simsy-card p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-simsy-text text-sm font-medium">Events (24h)</p>
                <p className="text-3xl font-bold text-simsy-blue">{stats.events.last_24h}</p>
                <p className="text-sm text-simsy-text">
                  of {stats.events.total} total
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-500/10 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect x="3" y="5" width="18" height="16" rx="2"/>
                  <path d="M16 3v4M8 3v4M3 9h18"/>
                  <circle cx="12" cy="14" r="3"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Unviewed Events */}
          <div className="bg-simsy-card p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-simsy-text text-sm font-medium">Unviewed</p>
                <p className="text-3xl font-bold text-red-400">{stats.events.unviewed}</p>
                <p className="text-sm text-simsy-text">
                  need attention
                </p>
              </div>
              <div className="w-12 h-12 bg-red-400/10 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
              </div>
            </div>
          </div>

          {/* Events by Tag */}
          <div className="bg-simsy-card p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-simsy-text text-sm font-medium">Tagged Events</p>
                <p className="text-3xl font-bold text-purple-400">
                  {stats.events_by_tag.reduce((sum, tag) => sum + tag.count, 0)}
                </p>
                <p className="text-sm text-simsy-text">
                  {stats.events_by_tag.length} tags
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-400/10 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events by Tag Breakdown */}
      {!statsLoading && stats && stats.events_by_tag.length > 0 && (
        <div className="mb-8 bg-simsy-card p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-bold text-simsy-blue mb-4">Events by Tag</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stats.events_by_tag.map((tag, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-simsy-dark rounded-lg">
                <div className="flex items-center gap-3">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: tag.tag_color }}
                  ></div>
                  <span className="text-simsy-text font-medium">{tag.tag_name}</span>
                </div>
                <span className="text-simsy-blue font-bold">{tag.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        className="mb-4 bg-simsy-blue text-white font-bold py-2 px-4 rounded hover:bg-simsy-dark hover:text-simsy-blue transition"
        onClick={() => setShowForm((v) => !v)}
      >
        {showForm ? 'Cancel' : 'Add Camera'}
      </button>
      {showForm && (
        <form onSubmit={handleAddCamera} className="mb-6 flex flex-col gap-2 bg-simsy-card p-4 rounded-xl shadow">
          <div className="flex gap-4">
            <input name="name" value={form.name} onChange={handleFormChange} placeholder="Name" className="p-2 rounded bg-simsy-dark text-simsy-text flex-1" required />
            <input name="ip_address" value={form.ip_address} onChange={handleFormChange} placeholder="IP Address" className="p-2 rounded bg-simsy-dark text-simsy-text flex-1" required />
            <input name="port" type="number" value={form.port} onChange={handleFormChange} placeholder="Port" className="p-2 rounded bg-simsy-dark text-simsy-text w-24" required />
            <input name="model" value={form.model} onChange={handleFormChange} placeholder="Model" className="p-2 rounded bg-simsy-dark text-simsy-text flex-1" />
            <input name="base_url" value={form.base_url} onChange={handleFormChange} placeholder="Base URL (http://...)" className="p-2 rounded bg-simsy-dark text-simsy-text flex-1" required />
          </div>
          {formError && <div className="text-red-500">{formError}</div>}
          <button type="submit" className="bg-simsy-blue text-white font-bold py-2 px-4 rounded w-32 mt-2" disabled={formLoading}>
            {formLoading ? 'Adding...' : 'Add Camera'}
          </button>
        </form>
      )}
      {loading && <div>Loading cameras...</div>}
      {error && <div className="text-red-500 mb-4">{error.message}</div>}
      {!loading && !error && cameras && (
        <div className="space-y-4">
          {cameras.map((cam) => (
            <div key={cam.id} className="bg-simsy-card rounded-xl shadow-lg overflow-hidden">
              <div 
                className="p-4 cursor-pointer hover:bg-simsy-dark/50 transition"
                onClick={() => handleCameraClick(cam.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-3 h-3 rounded-full bg-green-400"></div>
                    <div>
                      <h3 className="text-xl font-bold text-simsy-blue">{cam.name}</h3>
                      <p className="text-simsy-text">{cam.ip_address}:{cam.port}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${cam.is_online ? 'text-green-400' : 'text-red-400'}`}>
                        {cam.is_online ? 'Online' : 'Offline'}
                      </span>
                      <span className="text-simsy-text">{cam.model || '-'}</span>
                    </div>
                    <p className="text-sm text-simsy-text">
                      {cam.last_seen ? new Date(cam.last_seen).toLocaleString() : '-'}
                    </p>
                  </div>
                </div>
              </div>
              
              {selectedCamera === cam.id && streams && (
                <div className="border-t border-simsy-dark p-4">
                  <h4 className="text-lg font-semibold text-simsy-blue mb-4">Streams & Snapshots</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {streams.streams.map((stream) => (
                      <div key={stream.name} className="bg-simsy-dark p-4 rounded-lg">
                        <h5 className="font-semibold text-simsy-text mb-2">{stream.name.toUpperCase()}</h5>
                        <div className="text-sm text-simsy-text mb-3">
                          <p>Resolution: {stream.stream_info.resolution.width}x{stream.stream_info.resolution.height}</p>
                          <p>FPS: {stream.stream_info.fps}</p>
                          <p>Codec: {stream.stream_info.codec}</p>
                        </div>
                        {stream.stream_info.snapshot && (
                          <button
                            onClick={() => handleTakeSnapshot(cam.id, stream.name)}
                            disabled={snapshotLoading === cam.id}
                            className="w-full bg-simsy-blue text-white font-bold py-2 px-4 rounded hover:bg-simsy-dark hover:text-simsy-blue transition disabled:opacity-50"
                          >
                            {snapshotLoading === cam.id ? 'Taking Snapshot...' : 'Take Snapshot'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  {snapshotUrl && (
                    <div className="mt-6">
                      <h5 className="font-semibold text-simsy-blue mb-2">Latest Snapshot</h5>
                      <div className="bg-simsy-dark p-4 rounded-lg">
                        <img 
                          src={snapshotUrl} 
                          alt="Camera Snapshot" 
                          className="max-w-full h-auto rounded-lg"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            dispatch({ 
                              type: 'ADD_NOTIFICATION', 
                              payload: { message: 'Failed to load snapshot image', type: 'error' } 
                            });
                          }}
                        />
                        <div className="mt-2">
                          <a 
                            href={snapshotUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-simsy-blue hover:underline"
                          >
                            Open in new tab
                          </a>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 