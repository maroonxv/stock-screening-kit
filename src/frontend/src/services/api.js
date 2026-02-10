import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const screeningApi = {
  // Strategies
  getStrategies: (params) => apiClient.get('/screening/strategies', { params }),
  getStrategy: (id) => apiClient.get(`/screening/strategies/${id}`),
  createStrategy: (data) => apiClient.post('/screening/strategies', data),
  updateStrategy: (id, data) => apiClient.put(`/screening/strategies/${id}`, data),
  deleteStrategy: (id) => apiClient.delete(`/screening/strategies/${id}`),
  executeStrategy: (id) => apiClient.post(`/screening/strategies/${id}/execute`),

  // Sessions
  getSessions: (params) => apiClient.get('/screening/sessions', { params }),
  getSession: (id) => apiClient.get(`/screening/sessions/${id}`),

  // Watchlists
  getWatchlists: (params) => apiClient.get('/screening/watchlists', { params }),
  getWatchlist: (id) => apiClient.get(`/screening/watchlists/${id}`),
  createWatchlist: (data) => apiClient.post('/screening/watchlists', data),
  updateWatchlist: (id, data) => apiClient.put(`/screening/watchlists/${id}`, data),
  deleteWatchlist: (id) => apiClient.delete(`/screening/watchlists/${id}`),
  addStock: (watchlistId, data) => apiClient.post(`/screening/watchlists/${watchlistId}/stocks`, data),
  removeStock: (watchlistId, stockCode) => apiClient.delete(`/screening/watchlists/${watchlistId}/stocks/${stockCode}`),
};
