const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const RecommendationService = {
  getRecommendations: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/recommendations/${userId}`);

      if (response.status === 404) {
        const data = await response.json();
        throw new Error(data.detail || 'No se encontraron recomendaciones');
      }

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al obtener recomendaciones');
      }

      return await response.json();
      // Returns: { sections: [{title, model, movies}], rating_count, next_threshold, next_model }
    } catch (error) {
      console.error('Error in getRecommendations:', error);
      throw error;
    }
  },

  getContentBasedRecommendations: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/recommendations/content/${userId}`);

      if (response.status === 404) {
        const data = await response.json();
        throw new Error(data.detail || 'No se encontraron recomendaciones');
      }

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al obtener recomendaciones');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in getContentBasedRecommendations:', error);
      throw error;
    }
  }
};

export default RecommendationService;
