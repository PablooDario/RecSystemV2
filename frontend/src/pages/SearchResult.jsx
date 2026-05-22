import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { searchMovies } from '../services/movie.service';
import MovieCard from '../components/Movie/MovieCard';

const SearchResult = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q');
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const imageBaseUrl = 'https://image.tmdb.org/t/p';

  useEffect(() => {
    const fetchSearchResults = async () => {
      if (!query) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const results = await searchMovies(query);
        setMovies(results);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching search results:', error);
        setLoading(false);
      }
    };

    fetchSearchResults();
  }, [query]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 flex items-center justify-center">
        <div className="text-white text-2xl">Buscando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 pb-12">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">
          Resultados de búsqueda
        </h1>
        <p className="text-gray-400 text-lg mb-8">
          {movies.length} resultados para "{query}"
        </p>

        {movies.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-gray-400 text-xl">
              No se encontraron películas para "{query}"
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {movies.map((movie) => (
              <Link
                key={movie.id}
                to={`/movie/${movie.id}`}
                className="block"
              >
                <div className="bg-gray-800/30 rounded-lg overflow-hidden border border-gray-700/50 hover:border-purple-500/50 transition-all hover:bg-gray-800/50 group">
                  <div className="flex flex-col sm:flex-row gap-4 p-4">
                    {/* Movie Poster */}
                    <div className="flex-shrink-0 w-32 sm:w-28">
                      <div className="aspect-[2/3] rounded-lg overflow-hidden bg-gray-700">
                        {movie.poster_path ? (
                          <img
                            src={`${imageBaseUrl}/w185${movie.poster_path}`}
                            alt={movie.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-gray-500 text-4xl">
                            🎬
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Movie Info */}
                    <div className="flex-1 min-w-0">
                      {/* Title and Year */}
                      <h2 className="text-2xl font-bold text-white mb-1 group-hover:text-purple-400 transition-colors">
                        {movie.title}
                      </h2>
                      
                      {movie.release_date && (
                        <p className="text-gray-400 text-sm mb-3">
                          {new Date(movie.release_date).toLocaleDateString('es-ES', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </p>
                      )}

                      {/* Overview */}
                      {movie.overview && (
                        <p className="text-gray-300 text-sm leading-relaxed line-clamp-3">
                          {movie.overview}
                        </p>
                      )}
                      
                      {/* Director */}
                      {movie.director && (
                        <p className="text-white-400 text-sm mt-2">
                          <span className="font-semibold">Dirigida por:</span> {movie.director}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchResult;