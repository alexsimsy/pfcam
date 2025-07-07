import React, { useState, useEffect } from 'react';
import { fetchEvents, downloadEvent, playEvent, deleteEventLocal, deleteEventFromCamera, getEventSyncStatus } from '../services/events';
import { useApi } from '../hooks/useApi';
import { useAppState } from '../contexts/AppStateContext';
import type { Event } from '../services/events';
import { triggerEvent } from '../services/cameras';

export default function Events() {
  const { dispatch } = useAppState();
  const [playingEventUrl, setPlayingEventUrl] = useState<string | null>(null);
  const [playingEventName, setPlayingEventName] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [syncStatus, setSyncStatus] = useState<{[key: number]: {on_server: boolean, on_camera: boolean}}>({});

  const { data: events, loading, error } = useApi(
    fetchEvents,
    [],
    {
      onError: (err) => dispatch({ type: 'ADD_ERROR', payload: err.message })
    }
  );

  // Load sync status for all events
  useEffect(() => {
    if (events?.events) {
      events.events.forEach((event: Event) => {
        loadSyncStatus(event.id);
      });
    }
  }, [events]);

  const loadSyncStatus = async (eventId: number) => {
    try {
      const status = await getEventSyncStatus(eventId);
      setSyncStatus(prev => ({ ...prev, [eventId]: status }));
    } catch (error) {
      // Ignore sync errors for now
    }
  };

  const handlePlay = async (eventId: number, eventName: string) => {
    try {
      const playUrl = await playEvent(eventId);
      setPlayingEventUrl(playUrl);
      setPlayingEventName(eventName);
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to play event' 
      });
    }
  };

  const handleDeleteLocal = async (eventId: number) => {
    setDeleting(eventId);
    try {
      await deleteEventLocal(eventId);
      await loadSyncStatus(eventId);
      window.location.reload();
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Event deleted from local storage', type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to delete event from local storage' 
      });
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteFromCamera = async (eventId: number) => {
    setDeleting(eventId);
    try {
      await deleteEventFromCamera(eventId);
      await loadSyncStatus(eventId);
      window.location.reload();
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Event deleted from camera', type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to delete event from camera' 
      });
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = async (eventId: number, filename: string) => {
    try {
      const response = await fetch(`/api/v1/events/${eventId}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Event downloaded successfully', type: 'success' } 
      });
      window.location.reload();
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to download event' 
      });
    }
  };

  const handleTriggerEvent = async () => {
    setTriggering(true);
    try {
      await triggerEvent(1, 10, 10, 'string', 'overlay');
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: { message: 'Event triggered successfully', type: 'success' }
      });
      window.location.reload();
    } catch (error) {
      dispatch({
        type: 'ADD_ERROR',
        payload: 'Failed to trigger event'
      });
    } finally {
      setTriggering(false);
    }
  };

  if (loading) return <div className="p-4">Loading events...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error.message}</div>;

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-simsy-text">Events</h1>
        <div className="flex gap-2">
          <button
            onClick={() => window.location.reload()}
            className="bg-simsy-primary text-white px-4 py-2 rounded hover:bg-simsy-primary-dark"
          >
            Refresh
          </button>
          <button
            onClick={handleTriggerEvent}
            disabled={triggering}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {triggering ? 'Triggering...' : 'Trigger Event'}
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-300">
          <thead>
            <tr className="bg-gray-50">
              <th className="px-4 py-2 border-b">Filename</th>
              <th className="px-4 py-2 border-b">Event Name</th>
              <th className="px-4 py-2 border-b">Camera</th>
              <th className="px-4 py-2 border-b">Triggered At</th>
              <th className="px-4 py-2 border-b">Sync</th>
              <th className="px-4 py-2 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            {events?.events.map((event: Event) => {
              const status = syncStatus[event.id];
              const isOnServer = status?.on_server || event.is_downloaded;
              const isOnCamera = status?.on_camera !== false;
              return (
                <tr key={event.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 border-b">{event.filename}</td>
                  <td className="px-4 py-2 border-b">{event.event_name || 'N/A'}</td>
                  <td className="px-4 py-2 border-b">{event.camera_name}</td>
                  <td className="px-4 py-2 border-b">{new Date(event.triggered_at).toLocaleString()}</td>
                  <td className="px-4 py-2 border-b">
                    <span className={isOnServer ? 'text-green-600' : 'text-red-600'}>
                      {isOnServer ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-2 border-b">
                    <div className="flex gap-2">
                      {isOnServer && (
                        <>
                          <button
                            onClick={() => handleDownload(event.id, event.filename)}
                            className="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => handlePlay(event.id, event.filename)}
                            className="bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600"
                          >
                            Play
                          </button>
                          <button
                            onClick={() => handleDeleteLocal(event.id)}
                            disabled={deleting === event.id}
                            className="bg-orange-500 text-white px-2 py-1 rounded text-sm hover:bg-orange-600 disabled:opacity-50"
                          >
                            {deleting === event.id ? '...' : 'Delete Locally'}
                          </button>
                        </>
                      )}
                      {isOnCamera && (
                        <button
                          onClick={() => handleDeleteFromCamera(event.id)}
                          disabled={deleting === event.id}
                          className="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600 disabled:opacity-50"
                        >
                          {deleting === event.id ? '...' : 'Delete from Camera'}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {/* Video Playback Modal */}
      {playingEventUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-4xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{playingEventName}</h3>
              <button
                onClick={() => {
                  setPlayingEventUrl(null);
                  setPlayingEventName(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <video
              controls
              autoPlay
              className="w-full max-h-96"
              src={playingEventUrl}
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      )}
    </div>
  );
} 