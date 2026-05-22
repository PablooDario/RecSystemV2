const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

// Get 20 popular movies from the backend to show in the home carrusel
export const getPopularMovies = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/movies`);

    if (!response.ok) {
      throw new Error("Error fetching movies");
    }

    return await response.json();
  } catch (error) {
    console.error("Error in getPopularMovies:", error);
    return [];
  }
};


// Get a Movie by its title
export const searchMovies = async (query) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/movies/search/?query=${encodeURIComponent(query)}`
    );
    
    if (!response.ok) {
      throw new Error('Error searching movies');
    }

    const data = await response.json();
    return data; 
  } catch (error) {
    console.error('Error in searchMovies:', error);
    return [];
  }
};


// Get the details for a specific movie
export const getMovieDetails = async (movie_id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/movies/${movie_id}`);
    
    if (!response.ok) {
      throw new Error('Error fetching movie details');
    }

    return await response.json();
  } catch (error) {
    console.error('Error in getMovieDetails:', error);
    return null;
  }
};

// Get a Backdrop path for the home page
export const getRandomBackdrop = async () => {
  try {
    const movie_id = Math.floor(Math.random() * 3830) + 1;
    const movie_details = await getMovieDetails(movie_id);
    return movie_details.backdrop_path || null;

  } catch (error) {
    console.error('Error in getRandomBackdrop:', error);
    return null;
  }
};