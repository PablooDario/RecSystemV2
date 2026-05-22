import React, { useState, useEffect } from 'react';
import { getMovieDetails } from '../services/movie.service';
import { useParams } from 'react-router-dom';
import { Bookmark, BookmarkCheck } from 'lucide-react';
import MovieCard from '../components/Movie/MovieCard';
import RatingStars from '../components/Movie/RatingStars';
import LoginService from '../services/login.service';
import RatingService from '../services/rating.service';
import WatchlistService from '../services/watchlist.service';

const MovieDetail = () => {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userRating, setUserRating] = useState(0);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);
  const [inWatchlist, setInWatchlist] = useState(false);
  const imageBaseUrl = 'https://image.tmdb.org/t/p';

  useEffect(() => {
    const checkAuth = () => {
      const authenticated = LoginService.isAuthenticated();
      const currentUserId = LoginService.getUserId();
      setIsLoggedIn(authenticated);
      setUserId(currentUserId);
    };

    checkAuth();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const movie_details = await getMovieDetails(id);
        setMovie(movie_details);

        if (isLoggedIn && userId) {
          const rating = await RatingService.getUserRating(userId, id);
          if (rating) {
            setUserRating(rating.rating);
          } else {
            setUserRating(0);
          }
          const watchlistStatus = await WatchlistService.isInWatchlist(userId, id);
          setInWatchlist(watchlistStatus);
        } else {
          setUserRating(0);
        }

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, [id, isLoggedIn, userId]);

  const handleRate = async (rating) => {
    if (!isLoggedIn || !userId) {
      return;
    }

    try {
      await RatingService.createOrUpdateRating(userId, id, rating);
      setUserRating(rating);
    } catch (error) {
      console.error('Error saving rating:', error);
    }
  };

  const handleToggleWatchlist = async () => {
    if (!isLoggedIn || !userId) return;
    try {
      if (inWatchlist) {
        await WatchlistService.removeFromWatchlist(userId, parseInt(id));
        setInWatchlist(false);
      } else {
        await WatchlistService.addToWatchlist(userId, parseInt(id));
        setInWatchlist(true);
      }
    } catch (error) {
      console.error('Error toggling watchlist:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 flex items-center justify-center">
        <div className="text-white text-2xl">Cargando...</div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 flex items-center justify-center">
        <div className="text-white text-2xl">Película no encontrada</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900">
      <div className="relative">
        <div className="absolute inset-0 h-[800px] overflow-hidden">
          <div 
            className="w-full h-full bg-cover bg-center bg-no-repeat"
            style={{
              backgroundImage: movie.backdrop_path 
                ? `url(${imageBaseUrl}/original${movie.backdrop_path})`
                : 'linear-gradient(to bottom, #1a1a2e, #16213e)'
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-transparent to-gray-900/50" />
        </div>

        <div className="relative pt-24 px-4 pb-12">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row gap-8">
              <div className="flex-shrink-0 md:w-96">
                <MovieCard movie={movie} imageBaseUrl={imageBaseUrl} />
                
                {movie.genres && movie.genres.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-xl font-semibold mb-3 text-white">Géneros</h3>
                    <div className="flex flex-wrap gap-2">
                      {movie.genres.map((genre, index) => (
                        <span
                          key={index}
                          className="px-4 py-2 bg-purple-600/30 rounded-full text-sm font-medium border border-purple-500/50 hover:bg-purple-600/50 transition-colors text-white"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex-1 text-white pt-4">
                <h1 className="text-5xl font-bold mb-2">
                  {movie.title}
                  {movie.release_date && (
                    <span className="text-3xl text-gray-400 ml-3">
                      ({new Date(movie.release_date).getFullYear()})
                    </span>
                  )}
                </h1>

                {movie.tagline && (
                  <p className="text-xl text-purple-300 italic mb-6">
                    "{movie.tagline}"
                  </p>
                )}

                <div className="flex items-center gap-6 mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-16 h-16 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                      {movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Calificación</div>
                      <div className="text-lg font-semibold">
                        {movie.vote_count ? movie.vote_count.toLocaleString() : '0'} votos
                      </div>
                    </div>
                  </div>

                  {movie.runtime && (
                    <div>
                      <div className="text-sm text-gray-400">Duración</div>
                      <div className="text-lg font-semibold">
                        {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                      </div>
                    </div>
                  )}
                </div>

                {movie.director && (
                  <div className="mb-6">
                    <span className="text-gray-400">Dirigida por: </span>
                    <span className="text-white font-semibold text-lg">{movie.director}</span>
                  </div>
                )}

                <div className="mb-8">
                  <h2 className="text-2xl font-bold mb-3">Descripción</h2>
                  <p className="text-gray-300 text-lg leading-relaxed">
                    {movie.overview || 'No hay descripción disponible.'}
                  </p>
                </div>

                {isLoggedIn && (
                  <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-3">Tu calificacion</h2>
                    <div>
                      <RatingStars
                        rating={userRating}
                        onRate={handleRate}
                      />
                      <p className="text-gray-400 text-sm mt-3">
                        {userRating > 0
                          ? 'Haz clic para cambiar tu calificacion'
                          : 'Haz clic en las estrellas para calificar'}
                      </p>
                    </div>

                    <button
                      onClick={handleToggleWatchlist}
                      className={`mt-4 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg transition-colors ${
                        inWatchlist
                          ? 'bg-purple-600 text-white hover:bg-purple-700'
                          : 'bg-slate-700/50 text-gray-300 border border-slate-600 hover:bg-slate-700'
                      }`}
                    >
                      {inWatchlist ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}
                      {inWatchlist ? 'En tu lista' : 'Ver mas tarde'}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {movie.actors && movie.actors.length > 0 && (
              <div className="mt-12">
                <h2 className="text-3xl font-bold text-white mb-6">Reparto</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                  {movie.actors.map((actor, index) => (
                    <div
                      key={index}
                      className="bg-gray-800/50 rounded-lg overflow-hidden border border-gray-700/50 hover:border-purple-500/50 transition-all hover:transform hover:scale-105"
                    >
                      <div className="aspect-[2/3] bg-gray-700 flex items-center justify-center">
                        {actor.profile_path ? (
                          <img
                            src={`${imageBaseUrl}/original${actor.profile_path}`}
                            alt={actor.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="text-gray-500 text-4xl">👤</div>
                        )}
                      </div>
                      <div className="p-3">
                        <p className="text-white font-semibold text-sm truncate">
                          {actor.name}
                        </p>
                        {actor.character && (
                          <p className="text-gray-400 text-xs truncate mt-1">
                            {actor.character}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetail;