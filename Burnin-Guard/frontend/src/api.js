const API_BASE = import.meta.env.VITE_API_URL || '';

async function fetchJson(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  getDuts() {
    return fetchJson('/api/duts');
  },

  getDut(dutId) {
    return fetchJson(`/api/duts/${dutId}`);
  },

  getDashboardStats() {
    return fetchJson('/api/dashboard/stats');
  },

  getAuditLog() {
    return fetchJson('/api/audit-log');
  },

  async predictCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.status}`);
    }
    return response.json();
  },

  async predictBatch(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}/predict/batch`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Batch prediction failed: ${response.status}`);
    }
    return response.json();
  },
};
