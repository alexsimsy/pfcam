import React, { useState, useEffect } from 'react';
import { fetchEvents, fetchOrphanedEvents, downloadEvent, playEvent, deleteEventLocal, deleteEventFromCamera, getEventSyncStatus, syncEvents } from '../services/events';
import { fetchTags, assignTagsToEvent, getTagUsageStats, createTag, deleteTag } from '../services/tags';
import { fetchCameras } from '../services/cameras';
import { useApi } from '../hooks/useApi';
import { useAppState } from '../contexts/AppStateContext';
import type { Event } from '../services/events';
import type { Tag, TagUsage } from '../services/tags';
import type { Camera } from '../services/cameras';

import { getToken } from '../services/auth';

// Status Icon Components
const StatusIcon = ({ status, type }: { status: boolean; type: 'success' | 'error' }) => {
  if (status) {
    return (
      <div className="flex items-center justify-center w-6 h-6 bg-green-100 rounded-full">
        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </div>
    );
  }
  return (
    <div className="flex items-center justify-center w-6 h-6 bg-red-100 rounded-full">
      <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    </div>
  );
};

// Tag Component
const TagBadge = ({ tag, onClick, selected = false }: { tag: Tag; onClick?: () => void; selected?: boolean }) => {
  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium cursor-pointer transition-colors ${
        selected 
          ? 'ring-2 ring-offset-2 ring-blue-500' 
          : 'hover:opacity-80'
      }`}
      style={{ backgroundColor: tag.color, color: '#ffffff' }}
    >
      {tag.name}
    </span>
  );
};

// Action Button Components
const ActionButton = ({ 
  onClick, 
  disabled, 
  loading, 
  icon, 
  label, 
  variant = 'primary' 
}: {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon: React.ReactNode;
  label: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger';
}) => {
  const baseClasses = "flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed";
  const variantClasses = {
    primary: "bg-blue-500 hover:bg-blue-600 text-white",
    success: "bg-green-500 hover:bg-green-600 text-white",
    warning: "bg-orange-500 hover:bg-orange-600 text-white",
    danger: "bg-red-500 hover:bg-red-600 text-white"
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${variantClasses[variant]}`}
      title={label}
    >
      {loading ? (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : (
        icon
      )}
    </button>
  );
};

export default function Events() {
  const { dispatch } = useAppState();
  const [playingEventUrl, setPlayingEventUrl] = useState<string | null>(null);
  const [playingEventName, setPlayingEventName] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [syncStatus, setSyncStatus] = useState<{[key: number]: {on_server: boolean, on_camera: boolean, in_ftp?: boolean}}>({});
  const [refreshing, setRefreshing] = useState(false);
  const [showOrphaned, setShowOrphaned] = useState(false);
  const [selectedEvents, setSelectedEvents] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [tags, setTags] = useState<Tag[]>([]);
  const [tagUsageStats, setTagUsageStats] = useState<TagUsage[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [showTagManager, setShowTagManager] = useState(false);
  const [editingEventTags, setEditingEventTags] = useState<number | null>(null);
  const [showCreateTag, setShowCreateTag] = useState(false);

  // Filter state
  const [filters, setFilters] = useState({
    cameraId: undefined as number | undefined,
    tagIds: [] as number[],
    isPlayed: undefined as boolean | undefined,
    showFilters: false
  });

  const [refreshKey, setRefreshKey] = useState(0);
  
  // Create a wrapper function that includes filters
  const fetchEventsWithFilters = async () => {
    if (showOrphaned) {
      return fetchOrphanedEvents();
    } else {
      return fetchEvents({
        cameraId: filters.cameraId,
        tagIds: filters.tagIds.length > 0 ? filters.tagIds : undefined,
        isPlayed: filters.isPlayed
      });
    }
  };

  const { data: events, loading, error } = useApi(
    fetchEventsWithFilters,
    [showOrphaned, refreshKey, filters], // Re-fetch when showOrphaned, refreshKey, or filters change
    {
      onError: (err) => {
        console.error('Events fetch error:', err);
        dispatch({ type: 'ADD_ERROR', payload: err.message });
      }
    }
  );

  const refreshEvents = () => {
    setRefreshKey(prev => prev + 1);
  };

  // Load tags, usage stats, and cameras
  useEffect(() => {
    const loadData = async () => {
      try {
        const [tagsData, usageData, camerasData] = await Promise.all([
          fetchTags(),
          getTagUsageStats(),
          fetchCameras()
        ]);
        setTags(tagsData.tags);
        setTagUsageStats(usageData);
        setCameras(camerasData);
      } catch (error) {
        console.error('Failed to load data:', error);
      }
    };
    loadData();
  }, []);

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
      console.log('Playing event:', { eventId, eventName });
      
      // Fetch the video file with authentication
      const token = getToken();
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/events/${eventId}/play`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Create blob URL for the video
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      console.log('Created blob URL:', blobUrl);
      setPlayingEventUrl(blobUrl);
      setPlayingEventName(eventName);
    } catch (error) {
      console.error('Play error:', error);
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: `Failed to play event: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    }
  };

  const handleDeleteLocal = async (eventId: number) => {
    setDeleting(eventId);
    try {
      await deleteEventLocal(eventId);
      await loadSyncStatus(eventId);
      // Remove from selected events
      setSelectedEvents(prev => {
        const newSet = new Set(prev);
        newSet.delete(eventId);
        return newSet;
      });
      refreshEvents();
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

  const handleBulkDeleteLocal = async () => {
    if (selectedEvents.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedEvents.size} event(s) from local storage? This action cannot be undone.`)) {
      return;
    }
    
    setBulkDeleting(true);
    try {
      const promises = Array.from(selectedEvents).map(eventId => deleteEventLocal(eventId));
      await Promise.all(promises);
      
      // Clear selected events
      setSelectedEvents(new Set());
      refreshEvents();
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: `${selectedEvents.size} events deleted from local storage`, type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to delete some events from local storage' 
      });
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleSelectEvent = (eventId: number, checked: boolean) => {
    setSelectedEvents(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(eventId);
      } else {
        newSet.delete(eventId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked: boolean) => {
    if (!events?.events) return;
    
    if (checked) {
      // Select all events that can be deleted locally
      const deletableEvents = events.events.filter((event: Event) => {
        const status = syncStatus[event.id];
        const isOnServer = status?.on_server || event.is_downloaded;
        return isOnServer;
      });
      setSelectedEvents(new Set(deletableEvents.map((e: Event) => e.id)));
    } else {
      setSelectedEvents(new Set());
    }
  };

  const handleDeleteFromCamera = async (eventId: number) => {
    if (!confirm('Are you sure you want to delete this event from the camera? This action cannot be undone.')) {
      return;
    }
    
    setDeleting(eventId);
    try {
      await deleteEventFromCamera(eventId);
      await loadSyncStatus(eventId);
      refreshEvents();
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
      await downloadEvent(eventId);
      
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Event downloaded successfully', type: 'success' } 
      });
    } catch (error) {
      console.error('Download error:', error);
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: `Failed to download event: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    }
  };



  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await syncEvents();
      // Re-fetch events after sync
      refreshEvents();
    } catch (err: any) {
      console.error('Refresh error:', err);
      dispatch({ type: 'ADD_ERROR', payload: err.message || 'Failed to sync events' });
    } finally {
      setRefreshing(false);
    }
  };

  const handleAssignTags = async (eventId: number, selectedTagIds: number[]) => {
    try {
      console.log('Assigning tags:', { eventId, selectedTagIds });
      const result = await assignTagsToEvent(eventId, selectedTagIds);
      console.log('Tag assignment result:', result);
      
      // Close the modal
      setEditingEventTags(null);
      
      // Show success message
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Tags assigned successfully', type: 'success' } 
      });
      
      // Refresh events to show updated tags
      refreshEvents();
    } catch (error) {
      console.error('Error assigning tags:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace'
      });
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: `Failed to assign tags: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    }
  };

  const handleCreateTag = async (tagData: { name: string; color: string; description?: string }) => {
    try {
      await createTag(tagData);
      setShowCreateTag(false);
      // Reload tags
      const [tagsData, usageData] = await Promise.all([
        fetchTags(),
        getTagUsageStats()
      ]);
      setTags(tagsData.tags);
      setTagUsageStats(usageData);
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: 'Tag created successfully', type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to create tag' 
      });
    }
  };

  const handleDeleteTag = async (tagId: number, tagName: string) => {
    if (!confirm(`Are you sure you want to delete the tag "${tagName}"? This will remove it from all events.`)) {
      return;
    }
    
    try {
      await deleteTag(tagId);
      // Reload tags
      const [tagsData, usageData] = await Promise.all([
        fetchTags(),
        getTagUsageStats()
      ]);
      setTags(tagsData.tags);
      setTagUsageStats(usageData);
      dispatch({ 
        type: 'ADD_NOTIFICATION', 
        payload: { message: `Tag "${tagName}" deleted successfully`, type: 'success' } 
      });
    } catch (error) {
      dispatch({ 
        type: 'ADD_ERROR', 
        payload: 'Failed to delete tag' 
      });
    }
  };

  // Filter handlers
  const handleFilterChange = (filterType: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleClearFilters = () => {
    setFilters({
      cameraId: undefined,
      tagIds: [],
      isPlayed: undefined,
      showFilters: false
    });
  };

  // Helper function to get event display name
  const getEventDisplayName = (event: Event) => {
    if (event.display_name) return event.display_name;
    if (event.event_name && event.event_name.trim()) return event.event_name.trim();
    return `Event E${event.id.toString().padStart(4, '0')}`;
  };

  // Helper function to get event ID
  const getEventId = (event: Event) => {
    if (event.event_id) return event.event_id;
    return `E${event.id.toString().padStart(4, '0')}`;
  };

  if (loading) return <div className="p-4">Loading events...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error.message}</div>;

  return (
    <div className="p-4 bg-simsy-bg min-h-screen">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold text-simsy-text">
          {showOrphaned ? 'Deleted Events' : 'Events'}
        </h1>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setShowOrphaned(!showOrphaned)}
            className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              showOrphaned 
                ? 'bg-orange-600 text-white hover:bg-orange-700 shadow-lg' 
                : 'bg-gray-600 text-white hover:bg-gray-700 shadow-lg'
            }`}
          >
            {showOrphaned ? 'Show Active Events' : 'Show Deleted Events'}
          </button>
          <button
            onClick={() => setShowTagManager(!showTagManager)}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 shadow-lg"
          >
            {showTagManager ? 'Hide Tags' : 'Manage Tags'}
          </button>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-simsy-blue text-white px-6 py-3 rounded-lg font-medium hover:bg-simsy-dark hover:text-simsy-blue transition-all duration-200 disabled:opacity-50 shadow-lg"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 p-4 bg-simsy-card rounded-lg shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-simsy-text">Filters</h2>
          <div className="flex gap-2">
            <button
              onClick={() => handleFilterChange('showFilters', !filters.showFilters)}
              className="text-simsy-blue hover:text-simsy-dark transition-colors duration-200"
            >
              {filters.showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
            <button
              onClick={handleClearFilters}
              className="text-gray-500 hover:text-gray-700 transition-colors duration-200"
            >
              Clear All
            </button>
          </div>
        </div>
        
        {filters.showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Camera Filter */}
            <div>
              <label className="block text-sm font-medium text-simsy-text mb-2">
                Camera
              </label>
              <select
                value={filters.cameraId || ''}
                onChange={(e) => handleFilterChange('cameraId', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-simsy-dark rounded-md shadow-sm focus:outline-none focus:ring-simsy-blue focus:border-simsy-blue bg-simsy-dark text-simsy-text"
              >
                <option value="">All Cameras</option>
                {cameras.map((camera) => (
                  <option key={camera.id} value={camera.id}>
                    {camera.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Tags Filter */}
            <div>
              <label className="block text-sm font-medium text-simsy-text mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 min-h-[40px] p-2 border border-simsy-dark rounded-md bg-simsy-dark">
                {tags.map((tag) => (
                  <TagBadge
                    key={tag.id}
                    tag={tag}
                    selected={filters.tagIds.includes(tag.id)}
                    onClick={() => {
                      const newTagIds = filters.tagIds.includes(tag.id)
                        ? filters.tagIds.filter(id => id !== tag.id)
                        : [...filters.tagIds, tag.id];
                      handleFilterChange('tagIds', newTagIds);
                    }}
                  />
                ))}
                {tags.length === 0 && (
                  <span className="text-gray-500 text-sm">No tags available</span>
                )}
              </div>
            </div>

            {/* Played Status Filter */}
            <div>
              <label className="block text-sm font-medium text-simsy-text mb-2">
                Played Status
              </label>
              <select
                value={filters.isPlayed === undefined ? '' : filters.isPlayed.toString()}
                onChange={(e) => handleFilterChange('isPlayed', e.target.value === '' ? undefined : e.target.value === 'true')}
                className="w-full px-3 py-2 border border-simsy-dark rounded-md shadow-sm focus:outline-none focus:ring-simsy-blue focus:border-simsy-blue bg-simsy-dark text-simsy-text"
              >
                <option value="">All Events</option>
                <option value="true">Played</option>
                <option value="false">Not Played</option>
              </select>
            </div>

            {/* Active Filters Summary */}
            <div>
              <label className="block text-sm font-medium text-simsy-text mb-2">
                Active Filters
              </label>
              <div className="text-sm text-simsy-text">
                {[
                  filters.cameraId && `Camera: ${cameras.find(c => c.id === filters.cameraId)?.name}`,
                  filters.tagIds.length > 0 && `Tags: ${filters.tagIds.length} selected`,
                  filters.isPlayed !== undefined && `Status: ${filters.isPlayed ? 'Played' : 'Not Played'}`
                ].filter(Boolean).join(', ') || 'No filters applied'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tag Manager */}
      {showTagManager && (
        <div className="mb-6 p-6 bg-simsy-card rounded-lg shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-simsy-text">Tag Management</h2>
            <button
              onClick={() => setShowCreateTag(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors duration-200"
            >
              Create New Tag
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tagUsageStats.map((usage) => (
              <div key={usage.tag.id} className="p-4 border border-simsy-dark rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <TagBadge tag={usage.tag} />
                    <span className="text-sm text-simsy-text">{usage.usage_count} events</span>
                  </div>
                  <button
                    onClick={() => handleDeleteTag(usage.tag.id, usage.tag.name)}
                    className="text-red-500 hover:text-red-700 transition-colors duration-200"
                    title={`Delete tag "${usage.tag.name}"`}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
                {usage.tag.description && (
                  <p className="text-sm text-gray-500">{usage.tag.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bulk Delete Controls */}
      {!showOrphaned && selectedEvents.size > 0 && (
        <div className="mb-4 p-4 bg-orange-100 border border-orange-300 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-orange-800 font-medium">
                {selectedEvents.size} event(s) selected for deletion
              </span>
              <button
                onClick={() => setSelectedEvents(new Set())}
                className="text-orange-600 hover:text-orange-800 text-sm underline"
              >
                Clear Selection
              </button>
            </div>
            <button
              onClick={handleBulkDeleteLocal}
              disabled={bulkDeleting}
              className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 transition-colors duration-200"
            >
              {bulkDeleting ? 'Deleting...' : `Delete ${selectedEvents.size} Event(s)`}
            </button>
          </div>
        </div>
      )}

      {/* Events Table */}
      <div className="bg-simsy-card rounded-lg shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-simsy-dark text-simsy-blue">
                {!showOrphaned && (
                  <th className="px-4 py-3 text-center font-semibold">
                    <div className="flex justify-center">
                      <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </th>
                )}
                <th className="px-4 py-3 text-left font-semibold">Event ID</th>
                <th className="px-4 py-3 text-left font-semibold">Camera</th>
                <th className="px-4 py-3 text-left font-semibold">Date & Time</th>
                <th className="px-4 py-3 text-center font-semibold">Status</th>
                <th className="px-4 py-3 text-center font-semibold">Tags</th>
                <th className="px-4 py-3 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-simsy-dark">
              {events?.events.length === 0 ? (
                <tr>
                  <td colSpan={showOrphaned ? 6 : 7} className="px-6 py-12 text-center text-simsy-text">
                    <div className="flex flex-col items-center">
                      <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-lg font-medium">
                        {showOrphaned 
                          ? 'No deleted events found'
                          : 'No events found'
                        }
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {showOrphaned 
                          ? 'All events are either on camera or downloaded locally.'
                          : 'Try refreshing or triggering a new event.'
                        }
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                events?.events.map((event: Event) => {
                  const status = syncStatus[event.id];
                  const isOnServer = status?.on_server || event.is_downloaded;
                  const isOnCamera = status?.on_camera !== false;
                  
                  return (
                    <tr key={event.id} className="hover:bg-simsy-dark/20 transition-colors duration-200">
                      {!showOrphaned && (
                        <td className="px-4 py-3 text-center">
                          {isOnServer && (
                            <input
                              type="checkbox"
                              checked={selectedEvents.has(event.id)}
                              onChange={(e) => handleSelectEvent(event.id, e.target.checked)}
                              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                            />
                          )}
                        </td>
                      )}
                      <td className="px-4 py-3">
                        <span className="font-mono text-sm bg-simsy-dark text-simsy-blue px-2 py-1 rounded">
                          {getEventId(event)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-simsy-text">
                        {event.camera_name || 'Unknown Camera'}
                      </td>
                      <td className="px-4 py-3 text-simsy-text">
                        {event.triggered_at ? event.triggered_at.slice(0, 16).replace('T', ' ') : ''}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-2">
                          <div className="flex flex-col items-center">
                            <StatusIcon status={isOnCamera} type="success" />
                            <span className="text-xs text-simsy-text mt-1">Camera</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <StatusIcon status={isOnServer} type="success" />
                            <span className="text-xs text-simsy-text mt-1">Local</span>
                          </div>
                          <div className="flex flex-col items-center">
                            <StatusIcon status={event.is_played || false} type="success" />
                            <span className="text-xs text-simsy-text mt-1">Played</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1 justify-center">
                          {event.tags && event.tags.length > 0 ? (
                            event.tags.map((tag) => (
                              <TagBadge key={tag.id} tag={tag} />
                            ))
                          ) : (
                            <span className="text-xs text-gray-500">No tags</span>
                          )}
                          <button
                            onClick={() => setEditingEventTags(event.id)}
                            className="text-xs text-blue-500 hover:text-blue-700 underline"
                          >
                            Edit
                          </button>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-2">
                          {isOnServer && (
                            <>
                              <ActionButton
                                onClick={() => handleDownload(event.id, event.filename)}
                                icon={
                                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                  </svg>
                                }
                                label="Download"
                                variant="primary"
                              />
                              <ActionButton
                                onClick={() => handlePlay(event.id, getEventDisplayName(event))}
                                icon={
                                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                                  </svg>
                                }
                                label="Play"
                                variant="success"
                              />
                            </>
                          )}
                          {isOnCamera && (
                            <ActionButton
                              onClick={() => handleDeleteFromCamera(event.id)}
                              disabled={deleting === event.id}
                              loading={deleting === event.id}
                              icon={
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                              }
                              label="Delete from Camera"
                              variant="danger"
                            />
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

            {/* Tag Assignment Modal */}
      {editingEventTags !== null && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-simsy-card p-6 rounded-lg max-w-md w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-simsy-text">Assign Tags</h3>
              <button
                onClick={() => setEditingEventTags(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <TagAssignmentModal
              eventId={editingEventTags}
              availableTags={tags}
              currentTags={events?.events.find((e: Event) => e.id === editingEventTags)?.tags || []}
              onAssign={handleAssignTags}
              onCancel={() => setEditingEventTags(null)}
            />
          </div>
        </div>
      )}

      {/* Create Tag Modal */}
      {showCreateTag && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-simsy-card p-6 rounded-lg max-w-md w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-simsy-text">Create New Tag</h3>
              <button
                onClick={() => setShowCreateTag(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <CreateTagModal
              onCreate={handleCreateTag}
              onCancel={() => setShowCreateTag(false)}
            />
          </div>
        </div>
      )}

      {/* Video Playback Modal */}
      {playingEventUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-simsy-card p-6 rounded-lg max-w-4xl w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-simsy-text">{playingEventName}</h3>
              <button
                onClick={() => {
                  // Clean up blob URL
                  if (playingEventUrl && playingEventUrl.startsWith('blob:')) {
                    URL.revokeObjectURL(playingEventUrl);
                  }
                  setPlayingEventUrl(null);
                  setPlayingEventName(null);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <video
              controls
              autoPlay
              className="w-full max-h-96 rounded-lg"
              src={playingEventUrl}
              onError={(e) => {
                console.error('Video error:', e);
                dispatch({ 
                  type: 'ADD_ERROR', 
                  payload: 'Failed to load video. The file may not exist locally or may be corrupted.' 
                });
              }}
              onLoadStart={() => console.log('Video loading started')}
              onLoadedData={() => console.log('Video data loaded')}
              onCanPlay={() => console.log('Video can play')}
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      )}
    </div>
  );
}

// Tag Assignment Modal Component
const TagAssignmentModal = ({ 
  eventId, 
  availableTags, 
  currentTags, 
  onAssign, 
  onCancel 
}: {
  eventId: number;
  availableTags: Tag[];
  currentTags: Tag[];
  onAssign: (eventId: number, tagIds: number[]) => void;
  onCancel: () => void;
}) => {
  const [selectedTags, setSelectedTags] = useState<Set<number>>(
    new Set(currentTags.map(tag => tag.id))
  );

  const handleTagToggle = (tagId: number) => {
    console.log('Tag toggle clicked:', tagId);
    setSelectedTags(prev => {
      const newSet = new Set(prev);
      if (newSet.has(tagId)) {
        newSet.delete(tagId);
      } else {
        newSet.add(tagId);
      }
      console.log('Updated selected tags:', Array.from(newSet));
      return newSet;
    });
  };

  const handleSave = () => {
    console.log('Save button clicked!', { eventId, selectedTags: Array.from(selectedTags) });
    onAssign(eventId, Array.from(selectedTags));
  };

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-simsy-text mb-3">Select tags to assign to this event:</p>
        <div className="max-h-60 overflow-y-auto space-y-2">
          {availableTags.map((tag) => (
            <label key={tag.id} className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedTags.has(tag.id)}
                onChange={() => handleTagToggle(tag.id)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <TagBadge tag={tag} />
              {tag.description && (
                <span className="text-sm text-gray-500">{tag.description}</span>
              )}
            </label>
          ))}
        </div>
      </div>
      <div className="flex justify-end space-x-3 relative z-10">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors duration-200 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={(e) => {
            console.log('Save button clicked with event:', e);
            handleSave();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer relative z-10"
        >
          Save Tags
        </button>
      </div>
    </div>
  );
};

// Create Tag Modal Component
const CreateTagModal = ({ 
  onCreate, 
  onCancel 
}: {
  onCreate: (tagData: { name: string; color: string; description?: string }) => void;
  onCancel: () => void;
}) => {
  const [name, setName] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    onCreate({
      name: name.trim(),
      color,
      description: description.trim() || undefined
    });
  };

  const colorOptions = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', 
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
  ];

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-simsy-text mb-2">
            Tag Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            placeholder="Enter tag name"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-simsy-text mb-2">
            Color
          </label>
          <div className="flex flex-wrap gap-2">
            {colorOptions.map((colorOption) => (
              <button
                key={colorOption}
                type="button"
                onClick={() => setColor(colorOption)}
                className={`w-8 h-8 rounded-full border-2 transition-all ${
                  color === colorOption ? 'border-gray-800 scale-110' : 'border-gray-300'
                }`}
                style={{ backgroundColor: colorOption }}
              />
            ))}
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-simsy-text mb-2">
            Description (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            placeholder="Enter description"
            rows={3}
          />
        </div>
      </div>
      
      <div className="flex justify-end space-x-3 mt-6">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors duration-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
        >
          Create Tag
        </button>
      </div>
    </form>
  );
}; 