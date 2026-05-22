const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const RatingService = {
  createOrUpdateRating: async (userId, movieId, rating) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ratings/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          movie_id: movieId,
          rating: rating
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al guardar la calificación');
      }

      return data;
    } catch (error) {
      console.error('Error in createOrUpdateRating:', error);
      throw error;
    }
  },

  getUserRating: async (userId, movieId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ratings/${userId}/${movieId}`);

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error('Error al obtener la calificación');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in getUserRating:', error);
      return null;
    }
  }
};

export default RatingService;