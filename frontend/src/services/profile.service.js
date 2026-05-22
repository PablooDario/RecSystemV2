const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const ProfileService = {
  getUserProfile: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/profile`);

      if (!response.ok) {
        throw new Error('Error al obtener el perfil del usuario');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in getUserProfile:', error);
      throw error;
    }
  },

  getUserWatchedMovies: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/watched-movies`);

      if (!response.ok) {
        throw new Error('Error al obtener películas vistas');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in getUserWatchedMovies:', error);
      throw error;
    }
  }
};

export default ProfileService;