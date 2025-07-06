import React, { useEffect, useState } from 'react';
import { fetchCameras } from '../services/cameras';
import { fetchCameraStreams, getStreamSnapshot, listSnapshots, deleteSnapshot, getStreamUrl } from '../services/streams';
import type { Camera } from '../services/cameras';
import type { StreamList, SnapshotResponse, SnapshotListItem } from '../services/streams';
import { fetchProtectedImage } from '../utils/proxyImage';
import { getToken } from '../services/auth';
import { FaSpinner, FaExclamationCircle, FaDownload, FaTrash, FaSyncAlt, FaCheck } from 'react-icons/fa';
import VideoStreamModal from '../components/VideoStreamModal';

const HD_STREAM_URL = 'http://192.168.86.199/stream-hd';

export default function Streams() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCamera, setSelectedCamera] = useState<number | null>(null);
  const [streams, setStreams] = useState<Map<number, StreamList>>(new Map());
  const [snapshotLoading, setSnapshotLoading] = useState<{cameraId: number, streamName: string} | null>(null);
  const [snapshotUrl, setSnapshotUrl] = useState<string | null>(null);
  const [snapshotList, setSnapshotList] = useState<Map<number, SnapshotListItem[]>>(new Map());
  const [snapshotImageUrls, setSnapshotImageUrls] = useState<Map<number, string>>(new Map());
  const [snapshotImageLoading, setSnapshotImageLoading] = useState<Map<number, boolean>>(new Map());
  const [snapshotImageError, setSnapshotImageError] = useState<Map<number, boolean>>(new Map());
  const [liveView, setLiveView] = useState<{
    cameraId: number;
    streamName: string;
    streamUrl: string;
  } | null>(null);
  const [liveViewLoading, setLiveViewLoading] = useState(false);
  const [liveViewError, setLiveViewError] = useState('');
  const [refreshingCameraId, setRefreshingCameraId] = useState<number | null>(null);
  const [refreshSuccessCameraId, setRefreshSuccessCameraId] = useState<number | null>(null);

  useEffect(() => {
    fetchCameras()
      .then(setCameras)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Clean up blob URLs when snapshotList changes
    return () => {
      snapshotImageUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [snapshotList]);

  useEffect(() => {
    // Fetch blob URLs for all snapshots
    const token = getToken();
    if (!token) return;
    cameras.forEach((cam) => {
      const snapshots = snapshotList.get(cam.id) || [];
      snapshots.forEach(async (item) => {
        if (!snapshotImageUrls.has(item.id) && !snapshotImageLoading.get(item.id)) {
          setSnapshotImageLoading((prev) => new Map(prev).set(item.id, true));
          setSnapshotImageError((prev) => new Map(prev).set(item.id, false));
          try {
            const blobUrl = await fetchProtectedImage(item.download_url, token);
            setSnapshotImageUrls((prev) => new Map(prev).set(item.id, blobUrl));
          } catch (e) {
            setSnapshotImageError((prev) => new Map(prev).set(item.id, true));
          } finally {
            setSnapshotImageLoading((prev) => new Map(prev).set(item.id, false));
          }
        }
      });
    });
    // eslint-disable-next-line
  }, [snapshotList, cameras]);

  // Stop stream on navigation away
  useEffect(() => {
    return () => {
      setLiveView(null);
    };
  }, []);

  const handleCameraClick = async (cameraId: number) => {
    if (selectedCamera === cameraId) {
      setSelectedCamera(null);
      return;
    }
    setSelectedCamera(cameraId);
    if (!streams.has(cameraId)) {
      try {
        const streamData = await fetchCameraStreams(cameraId);
        setStreams((prev: Map<number, StreamList>) => new Map(prev).set(cameraId, streamData));
      } catch (err: any) {
        setError(`Failed to load streams: ${err.message}`);
      }
    }
    // Always load snapshots for the camera
    try {
      const snapshots = await listSnapshots(cameraId);
      setSnapshotList((prev: Map<number, SnapshotListItem[]>) => new Map(prev).set(cameraId, snapshots));
    } catch (err: any) {
      setSnapshotList((prev: Map<number, SnapshotListItem[]>) => new Map(prev).set(cameraId, []));
    }
  };

  const handleTakeSnapshot = async (cameraId: number, streamName: string) => {
    setSnapshotLoading({ cameraId, streamName });
    setSnapshotUrl(null);
    try {
      const snapshot: SnapshotResponse = await getStreamSnapshot(cameraId, streamName);
      setSnapshotUrl(snapshot.snapshot_url);
      // Optionally reload the snapshot list
      const snapshots = await listSnapshots(cameraId);
      setSnapshotList((prev: Map<number, SnapshotListItem[]>) => new Map(prev).set(cameraId, snapshots));
    } catch (err: any) {
      setError(`Failed to take snapshot: ${err.message}`);
    } finally {
      setSnapshotLoading(null);
    }
  };

  const handleDownload = async (item: SnapshotListItem) => {
    const token = getToken();
    if (!token) return;
    try {
      const blobUrl = await fetchProtectedImage(item.download_url, token);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = item.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      alert('Failed to download image');
    }
  };

  const handleDelete = async (cameraId: number, item: SnapshotListItem) => {
    if (!confirm('Are you sure you want to delete this snapshot?')) {
      return;
    }
    try {
      await deleteSnapshot(item.id);
      // Remove the snapshot from the list
      setSnapshotList((prev: Map<number, SnapshotListItem[]>) => {
        const newList = new Map(prev);
        const currentSnapshots = prev.get(cameraId) || [];
        newList.set(cameraId, currentSnapshots.filter((i) => i.id !== item.id));
        return newList;
      });
      // Clean up the blob URL if it exists
      const blobUrl = snapshotImageUrls.get(item.id);
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setSnapshotImageUrls((prev) => {
          const newUrls = new Map(prev);
          newUrls.delete(item.id);
          return newUrls;
        });
      }
    } catch (err: any) {
      setError(`Failed to delete snapshot: ${err.message}`);
    }
  };

  const handleStartLiveView = async (cameraId: number, streamName: string) => {
    setLiveViewLoading(true);
    setLiveViewError('');
    try {
      if (streamName.toLowerCase() === 'hd') {
        setLiveView({ cameraId, streamName, streamUrl: HD_STREAM_URL });
      } else {
        // Existing logic for RTSP or other streams
        const { stream_url } = await getStreamUrl(cameraId, streamName);
        setLiveView({ cameraId, streamName, streamUrl: stream_url });
      }
    } catch (err: any) {
      setLiveViewError('Failed to start live view: ' + (err.message || 'Unknown error'));
    } finally {
      setLiveViewLoading(false);
    }
  };

  const handleStopLiveView = () => {
    setLiveView(null);
  };

  const handleRefreshCamera = async (cameraId: number) => {
    setRefreshingCameraId(cameraId);
    setRefreshSuccessCameraId(null);
    try {
      const token = getToken();
      await fetch(`/api/v1/cameras/${cameraId}/refresh-mediamtx`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });
      setRefreshSuccessCameraId(cameraId);
      setTimeout(() => setRefreshSuccessCameraId(null), 2000);
    } catch (e) {
      alert('Failed to refresh camera stream');
    } finally {
      setRefreshingCameraId(null);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">Streams</h1>
      {liveView && (
        <VideoStreamModal
          open={!!liveView}
          onClose={handleStopLiveView}
          streamUrl={liveView.streamUrl}
          streamName={liveView.streamName}
        />
      )}
      {loading && <div>Loading cameras...</div>}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {liveViewError && <div className="text-red-500 mb-4">{liveViewError}</div>}
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
                      <h3 className="text-xl font-bold text-simsy-blue flex items-center gap-2">
                        {cam.name}
                        <button
                          className="ml-2 text-simsy-blue hover:text-simsy-dark focus:outline-none"
                          onClick={e => { e.stopPropagation(); handleRefreshCamera(cam.id); }}
                          disabled={refreshingCameraId === cam.id}
                          title="Refresh stream settings"
                        >
                          {refreshingCameraId === cam.id ? (
                            <FaSpinner className="animate-spin" />
                          ) : refreshSuccessCameraId === cam.id ? (
                            <FaCheck className="text-green-400" />
                          ) : (
                            <FaSyncAlt />
                          )}
                        </button>
                      </h3>
                      <p className="text-simsy-text">{cam.ip_address}:{cam.port}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${cam.is_online ? 'text-green-400' : 'text-red-400'}`}>{cam.is_online ? 'Online' : 'Offline'}</span>
                      <span className="text-simsy-text">{cam.model || '-'}</span>
                    </div>
                    <p className="text-sm text-simsy-text">{cam.last_seen ? new Date(cam.last_seen).toLocaleString() : '-'}</p>
                  </div>
                </div>
              </div>
              {/* Streams Section */}
              {selectedCamera === cam.id && streams.get(cam.id) && (
                <div className="border-t border-simsy-dark p-4">
                  <h4 className="text-lg font-semibold text-simsy-blue mb-4">Streams</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {streams.get(cam.id)!.streams.map((stream) => (
                      <div key={stream.name} className="bg-simsy-dark p-4 rounded-lg">
                        <h5 className="font-semibold text-simsy-text mb-2">{stream.name.toUpperCase()}</h5>
                        <div className="text-sm text-simsy-text mb-3">
                          <p>Resolution: {stream.stream_info.resolution.width}x{stream.stream_info.resolution.height}</p>
                          <p>FPS: {stream.stream_info.fps}</p>
                          <p>Codec: {stream.stream_info.codec}</p>
                        </div>
                        <button
                          onClick={() => handleStartLiveView(cam.id, stream.name)}
                          disabled={liveViewLoading}
                          className="w-full bg-simsy-blue text-white font-bold py-2 px-4 rounded hover:bg-simsy-dark hover:text-simsy-blue transition disabled:opacity-50 mb-2"
                        >
                          {liveViewLoading ? 'Starting...' : 'Start Live View'}
                        </button>
                        {stream.stream_info.snapshot && (
                          <button
                            onClick={() => handleTakeSnapshot(cam.id, stream.name)}
                            disabled={snapshotLoading?.cameraId === cam.id && snapshotLoading?.streamName === stream.name}
                            className="w-full bg-simsy-blue text-white font-bold py-2 px-4 rounded hover:bg-simsy-dark hover:text-simsy-blue transition disabled:opacity-50"
                          >
                            {snapshotLoading?.cameraId === cam.id && snapshotLoading?.streamName === stream.name ? 'Taking Snapshot...' : 'Take Snapshot'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Snapshots Card - always displayed */}
              <div className="border-t border-simsy-dark p-4">
                <h4 className="text-lg font-semibold text-simsy-blue mb-4">Saved Snapshots</h4>
                {snapshotList.get(cam.id) && snapshotList.get(cam.id)!.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {snapshotList.get(cam.id)!.map((item: SnapshotListItem) => (
                      <div key={item.id} className="bg-simsy-dark p-2 rounded-lg flex flex-col items-center">
                        <div className="w-full h-48 flex items-center justify-center bg-black rounded">
                          {snapshotImageLoading.get(item.id) ? (
                            <FaSpinner className="animate-spin text-simsy-blue text-3xl" />
                          ) : snapshotImageError.get(item.id) ? (
                            <FaExclamationCircle className="text-red-500 text-3xl" title="Failed to load image" />
                          ) : snapshotImageUrls.get(item.id) ? (
                            <img src={snapshotImageUrls.get(item.id)} alt="Snapshot" className="max-w-full h-full object-contain rounded" />
                          ) : null}
                        </div>
                        <div className="mt-1 text-xs text-simsy-text">{new Date(item.taken_at).toLocaleString()}</div>
                                                 <div className="mt-1 flex items-center gap-2 text-xs">
                           <button onClick={() => handleDownload(item)} className="flex items-center gap-1 text-simsy-blue hover:underline">
                             <FaDownload /> Download
                           </button>
                           <button onClick={() => handleDelete(cam.id, item)} className="flex items-center gap-1 text-red-400 hover:text-red-300 hover:underline">
                             <FaTrash /> Delete
                           </button>
                         </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-simsy-text">No snapshots available.</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 