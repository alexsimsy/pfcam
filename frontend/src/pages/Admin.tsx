import React, { useState } from 'react';
import { createCamera } from '../services/cameras';
import type { CameraCreate } from '../services/cameras';

const tabs = [
  { name: 'Users', key: 'users' },
  { name: 'Cameras', key: 'cameras' },
];

const initialCamera: CameraCreate = {
  name: '',
  ip_address: '',
  port: 80,
  base_url: '',
  username: '',
  password: '',
  use_ssl: false,
};

export default function Admin() {
  const [tab, setTab] = useState('users');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<CameraCreate>(initialCamera);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({
      ...f,
      [name]: type === 'checkbox' ? checked : value,
    }));
    
    // Auto-extract IP and port from base_url
    if (name === 'base_url') {
      try {
        const url = new URL(value);
        // Strip /api from the base URL since CameraClient adds it automatically
        let cleanBaseUrl = `${url.protocol}//${url.hostname}`;
        if (url.port) {
          cleanBaseUrl += `:${url.port}`;
        }
        // Remove /api suffix if present
        if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
          // Keep the base URL without /api
        } else {
          cleanBaseUrl += url.pathname;
        }
        
        setForm((f) => ({
          ...f,
          ip_address: url.hostname,
          port: parseInt(url.port) || (url.protocol === 'https:' ? 443 : 80),
          use_ssl: url.protocol === 'https:',
          base_url: cleanBaseUrl,
        }));
      } catch (e) {
        // Invalid URL, don't update IP/port
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    // Basic validation
    if (!form.name || !form.base_url) {
      setError('Name and Base URL are required.');
      setLoading(false);
      return;
    }
    if (!form.base_url.startsWith('http://') && !form.base_url.startsWith('https://')) {
      setError('Base URL must start with http:// or https://');
      setLoading(false);
      return;
    }
    try {
      await createCamera(form);
      setSuccess('Camera added successfully!');
      setForm(initialCamera);
      // Optionally refresh camera list here
    } catch (err: any) {
      setError(err.message || 'Failed to add camera');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-4xl font-bold mb-6">Admin Panel</h1>
      <div className="flex gap-4 mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`px-4 py-2 rounded font-bold ${tab === t.key ? 'bg-simsy-blue text-white' : 'bg-simsy-card text-simsy-blue'}`}
            onClick={() => setTab(t.key)}
          >
            {t.name}
          </button>
        ))}
      </div>
      <div>
        {tab === 'users' && <div>User management coming soon...</div>}
        {tab === 'cameras' && (
          <div>
            <button
              className="mb-4 bg-simsy-blue text-white px-4 py-2 rounded font-bold hover:bg-simsy-dark hover:text-simsy-blue transition"
              onClick={() => setShowModal(true)}
            >
              + Add Camera
            </button>
            {/* Camera onboarding modal */}
            {showModal && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-simsy-card p-8 rounded-xl shadow-lg w-full max-w-lg relative">
                  <button
                    className="absolute top-2 right-2 text-simsy-blue text-2xl font-bold"
                    onClick={() => { setShowModal(false); setError(''); setSuccess(''); }}
                  >
                    ×
                  </button>
                  <h2 className="text-2xl font-bold mb-4 text-simsy-blue">Add New Camera</h2>
                  <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <input
                      type="text"
                      name="name"
                      placeholder="Camera Name"
                      value={form.name}
                      onChange={handleChange}
                      className="p-3 rounded bg-simsy-dark text-simsy-text border border-simsy-blue focus:outline-none"
                      required
                    />
                    <input
                      type="text"
                      name="base_url"
                      placeholder="Camera URL (e.g., http://192.168.86.33 or http://192.168.86.33/api)"
                      value={form.base_url}
                      onChange={handleChange}
                      className="p-3 rounded bg-simsy-dark text-simsy-text border border-simsy-blue focus:outline-none"
                      required
                    />
                    <div className="text-sm text-simsy-text/70">
                      IP: {form.ip_address} | Port: {form.port} | SSL: {form.use_ssl ? 'Yes' : 'No'}
                    </div>
                    <input
                      type="text"
                      name="username"
                      placeholder="Username (optional)"
                      value={form.username}
                      onChange={handleChange}
                      className="p-3 rounded bg-simsy-dark text-simsy-text border border-simsy-blue focus:outline-none"
                    />
                    <input
                      type="password"
                      name="password"
                      placeholder="Password (optional)"
                      value={form.password}
                      onChange={handleChange}
                      className="p-3 rounded bg-simsy-dark text-simsy-text border border-simsy-blue focus:outline-none"
                    />
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        name="use_ssl"
                        checked={form.use_ssl}
                        onChange={handleChange}
                        className="accent-simsy-blue"
                      />
                      Use SSL
                    </label>
                    {error && <div className="text-red-500 text-center">{error}</div>}
                    {success && <div className="text-green-400 text-center">{success}</div>}
                    <button
                      type="submit"
                      className="bg-simsy-blue text-white font-bold py-2 rounded hover:bg-simsy-dark hover:text-simsy-blue transition"
                      disabled={loading}
                    >
                      {loading ? 'Adding...' : 'Add Camera'}
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 