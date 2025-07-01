import React, { useEffect, useState } from 'react';
import { fetchEvents, syncEvents, downloadEvent } from '../services/events';
import type { Event, EventFilters } from '../services/events';
import { fetchCameras } from '../services/cameras';
import type { Camera } from '../services/cameras';

export default function Events() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [filters, setFilters] = useState<EventFilters>({});
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchCameras().then(setCameras).catch(() => {});
  }, []);

  const toISODate = (date: string, endOfDay = false) => {
    if (!date) return undefined;
    return endOfDay ? `${date}T23:59:59Z` : `${date}T00:00:00Z`;
  };

  const loadEvents = () => {
    setLoading(true);
    const filtersWithISO = {
      ...filters,
      startDate: toISODate(filters.startDate || '', false),
      endDate: toISODate(filters.endDate || '', true),
    };
    fetchEvents(filtersWithISO)
      .then((data) => {
        setEvents(data.events);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch events');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEvents();
    // eslint-disable-next-line
  }, [filters]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value || undefined }));
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncEvents(filters.cameraId ? Number(filters.cameraId) : undefined);
      loadEvents();
    } catch (err: any) {
      setError(err.message || 'Failed to sync events');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">Events</h1>
      <div className="flex flex-wrap gap-4 mb-4 items-end">
        <div>
          <label className="block text-sm mb-1">Camera</label>
          <select
            name="cameraId"
            value={filters.cameraId || ''}
            onChange={handleFilterChange}
            className="bg-gray-900 text-white px-2 py-1 rounded"
          >
            <option value="">All Cameras</option>
            {cameras.map((cam) => (
              <option key={cam.id} value={cam.id}>{cam.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1">Start Date</label>
          <input
            type="date"
            name="startDate"
            value={filters.startDate || ''}
            onChange={handleFilterChange}
            className="bg-gray-900 text-white px-2 py-1 rounded"
          />
        </div>
        <div>
          <label className="block text-sm mb-1">End Date</label>
          <input
            type="date"
            name="endDate"
            value={filters.endDate || ''}
            onChange={handleFilterChange}
            className="bg-gray-900 text-white px-2 py-1 rounded"
          />
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow"
        >
          {syncing ? 'Syncing...' : 'Sync Events'}
        </button>
      </div>
      {loading && <p>Loading events...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && events.length === 0 && <p>No events found.</p>}
      {!loading && !error && events.length > 0 && (
        <table className="min-w-full bg-gray-800 text-white rounded-lg overflow-hidden">
          <thead>
            <tr>
              <th className="px-4 py-2">Filename</th>
              <th className="px-4 py-2">Event Name</th>
              <th className="px-4 py-2">Camera</th>
              <th className="px-4 py-2">Triggered At</th>
              <th className="px-4 py-2">Downloaded</th>
              <th className="px-4 py-2">Processed</th>
              <th className="px-4 py-2">Download</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id} className="border-t border-gray-700">
                <td className="px-4 py-2">{event.filename}</td>
                <td className="px-4 py-2">{event.event_name || '-'}</td>
                <td className="px-4 py-2">{event.camera_name || event.camera_id}</td>
                <td className="px-4 py-2">{new Date(event.triggered_at).toLocaleString()}</td>
                <td className="px-4 py-2">{event.is_downloaded ? 'Yes' : 'No'}</td>
                <td className="px-4 py-2">{event.is_processed ? 'Yes' : 'No'}</td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => downloadEvent(event.id)}
                    className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded"
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
} 