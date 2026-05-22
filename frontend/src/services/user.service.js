const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

export const getUserProfile = async () => {
  try {
    const userId = localStorage.getItem('user_id');
    if (!userId) throw new Error('No hay sesión activa');

    const response = await fetch(`${API_BASE_URL}/users/${userId}/profile`);
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al obtener perfil');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting user profile:', error);
    throw error;
  }
};

export const updateUserProfile = async (profileData) => {
  try {
    const userId = localStorage.getItem('user_id');
    if (!userId) throw new Error('No hay sesión activa');

    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al actualizar perfil');
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

export const rateMovie = async (movieId, rating) => {
  try {
    const userId = localStorage.getItem('user_id');
    if (!userId) throw new Error('No hay sesión activa');

    const response = await fetch(`${API_BASE_URL}/ratings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: parseInt(userId),
        movie_id: movieId,
        rating: rating,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al calificar película');
    }

    return await response.json();
  } catch (error) {
    console.error('Error rating movie:', error);
    throw error;
  }
};

export const getWatchedMovies = async () => {
  try {
    const userId = localStorage.getItem('user_id');
    if (!userId) throw new Error('No hay sesión activa');

    const response = await fetch(`${API_BASE_URL}/users/${userId}/watched-movies`);
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al obtener películas vistas');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting watched movies:', error);
    return [];
  }
};

export const getRecommendations = async () => {
  try {
    const userId = localStorage.getItem('user_id');
    if (!userId) throw new Error('No hay sesión activa');

    const response = await fetch(`${API_BASE_URL}/recommendations/${userId}`);
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Error al obtener recomendaciones');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting recommendations:', error);
    return [];
  }
};
