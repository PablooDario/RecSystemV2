const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const WatchlistService = {
  addToWatchlist: async (userId, movieId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/watchlist/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: parseInt(userId), movie_id: movieId }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al agregar a la lista');
      }
      return await response.json();
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      throw error;
    }
  },

  removeFromWatchlist: async (userId, movieId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/watchlist/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: parseInt(userId), movie_id: movieId }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al remover de la lista');
      }
      return await response.json();
    } catch (error) {
      console.error('Error removing from watchlist:', error);
      throw error;
    }
  },

  getWatchlist: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/watchlist/${userId}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al obtener la lista');
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting watchlist:', error);
      throw error;
    }
  },

  isInWatchlist: async (userId, movieId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/watchlist/${userId}/${movieId}`);
      if (!response.ok) return false;
      const data = await response.json();
      return data.in_watchlist;
    } catch (error) {
      console.error('Error checking watchlist:', error);
      return false;
    }
  },
};

export default WatchlistService;
