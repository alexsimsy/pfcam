import React, { useEffect, useState } from 'react';
import { fetchCameras, createCamera } from '../services/cameras';
import { fetchCameraStreams, getStreamSnapshot } from '../services/streams';
import type { Camera } from '../services/cameras';
import type { StreamList, SnapshotResponse } from '../services/streams';

export default function Cameras() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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

  useEffect(() => {
    fetchCameras()
      .then(setCameras)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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
      setLoading(true);
      fetchCameras()
        .then(setCameras)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    } catch (err: any) {
      setFormError(err.message || 'Failed to add camera');
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
      setError(`Failed to load streams: ${err.message}`);
    }
  };

  const handleTakeSnapshot = async (cameraId: number, streamName: string) => {
    setSnapshotLoading(cameraId);
    setSnapshotUrl(null);
    
    try {
      const snapshot: SnapshotResponse = await getStreamSnapshot(cameraId, streamName);
      setSnapshotUrl(snapshot.snapshot_url);
    } catch (err: any) {
      setError(`Failed to take snapshot: ${err.message}`);
    } finally {
      setSnapshotLoading(null);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">Cameras</h1>
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
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {!loading && !error && (
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
                            setError('Failed to load snapshot image');
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