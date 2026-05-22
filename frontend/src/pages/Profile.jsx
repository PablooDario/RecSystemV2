import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Brain, Heart, Users, Target, Zap, Film, User as UserIcon, Calendar, Sparkles, Bookmark, RefreshCw } from 'lucide-react';
import LoginService from '../services/login.service';
import ProfileService from '../services/profile.service';
import WatchlistService from '../services/watchlist.service';

const TRAIT_INFO = {
  openness: {
    name: 'Apertura',
    icon: Brain,
    color: 'purple',
    bgColor: 'bg-purple-500/10',
    textColor: 'text-purple-400',
    borderColor: 'border-purple-500/30'
  },
  conscientiousness: {
    name: 'Responsabilidad',
    icon: Target,
    color: 'blue',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-400',
    borderColor: 'border-blue-500/30'
  },
  extraversion: {
    name: 'Extraversión',
    icon: Zap,
    color: 'yellow',
    bgColor: 'bg-yellow-500/10',
    textColor: 'text-yellow-400',
    borderColor: 'border-yellow-500/30'
  },
  agreeableness: {
    name: 'Amabilidad',
    icon: Heart,
    color: 'pink',
    bgColor: 'bg-pink-500/10',
    textColor: 'text-pink-400',
    borderColor: 'border-pink-500/30'
  },
  neuroticism: {
    name: 'Neuroticismo',
    icon: Users,
    color: 'red',
    bgColor: 'bg-red-500/10',
    textColor: 'text-red-400',
    borderColor: 'border-red-500/30'
  }
};

const Profile = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [watchedMovies, setWatchedMovies] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const imageBaseUrl = 'https://image.tmdb.org/t/p';

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userId = LoginService.getUserId();
        
        if (!userId) {
          setError('Debes iniciar sesión para ver tu perfil');
          setLoading(false);
          return;
        }

        const [profileData, moviesData, watchlistData] = await Promise.all([
          ProfileService.getUserProfile(userId),
          ProfileService.getUserWatchedMovies(userId),
          WatchlistService.getWatchlist(userId),
        ]);

        setProfile(profileData);
        setWatchedMovies(moviesData);
        setWatchlist(watchlistData.movies || []);
        setLoading(false);
      } catch (err) {
        console.error('Error loading profile:', err);
        setError('Error al cargar el perfil');
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const getScoreLevel = (score) => {
    if (score < 2.5) return 'Bajo';
    if (score <= 3.5) return 'Medio';
    return 'Alto';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 flex items-center justify-center">
        <div className="text-white text-2xl">Cargando perfil...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 flex items-center justify-center">
        <div className="text-red-400 text-2xl">{error}</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 flex items-center justify-center">
        <div className="text-white text-2xl">Perfil no encontrado</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 pb-12">
      <div className="max-w-7xl mx-auto">
        {/* Profile Overview Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* User Info Card - Left Side */}
          <div className="lg:col-span-1">
            <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-xl p-6 border border-purple-500/20 h-full">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <UserIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">{profile.username}</h1>
                  <p className="text-gray-400 text-sm">Usuario</p>
                </div>
              </div>

              <div className="space-y-3">
                {profile.age && (
                  <div className="flex items-center gap-3 text-gray-300">
                    <Calendar className="w-4 h-4 text-purple-400" />
                    <span className="text-sm">{profile.age} años</span>
                  </div>
                )}
                {profile.gender && (
                  <div className="flex items-center gap-3 text-gray-300">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-sm capitalize">{profile.gender}</span>
                  </div>
                )}
                <div className="flex items-center gap-3 text-gray-300">
                  <Film className="w-4 h-4 text-purple-400" />
                  <span className="text-sm">{watchedMovies.length} películas vistas</span>
                </div>
              </div>
            </div>
          </div>

          {/* Personality Traits - Right Side */}
          <div className="lg:col-span-2">
            <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-xl p-6 border border-purple-500/20">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" />
                Perfil de Personalidad
              </h2>
              
              <div className="space-y-3">
                {profile.personality && Object.entries(TRAIT_INFO).map(([key, info]) => {
                  const score = profile.personality[key];
                  const percentage = (score / 5) * 100;
                  const Icon = info.icon;
                  
                  return (
                    <div 
                      key={key} 
                      className={`flex items-center gap-4 p-3 rounded-lg border ${info.borderColor} ${info.bgColor} hover:bg-opacity-20 transition-all group`}
                    >
                      <div className={`p-2 rounded-lg ${info.bgColor}`}>
                        <Icon className={`w-5 h-5 ${info.textColor}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white font-medium text-sm">{info.name}</span>
                          <span className={`text-xs ${info.textColor} font-semibold`}>
                            {getScoreLevel(score)}
                          </span>
                        </div>
                        
                        <div className="relative h-2 bg-slate-900/50 rounded-full overflow-hidden">
                          <div 
                            className={`absolute top-0 left-0 h-full transition-all duration-1000`}
                            style={{ 
                              width: `${percentage}%`,
                              background: `linear-gradient(to right, ${
                                info.color === 'purple' ? '#9333ea' : 
                                info.color === 'blue' ? '#3b82f6' : 
                                info.color === 'yellow' ? '#eab308' : 
                                info.color === 'pink' ? '#ec4899' : '#ef4444'
                              }, ${
                                info.color === 'purple' ? '#7c3aed' : 
                                info.color === 'blue' ? '#2563eb' : 
                                info.color === 'yellow' ? '#ca8a04' : 
                                info.color === 'pink' ? '#db2777' : '#dc2626'
                              })`
                            }}
                          />
                        </div>
                      </div>
                      
                      <span className="text-white font-bold text-lg w-12 text-right">
                        {score?.toFixed(1)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Re-take Questionnaire Button */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/questionnaire', { state: { retake: true } })}
            className="inline-flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Volver a contestar cuestionario de personalidad
          </button>
        </div>

        {/* Watchlist Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Bookmark className="w-7 h-7 text-purple-400" />
            <h2 className="text-3xl font-bold text-white">
              Ver mas tarde
            </h2>
            <span className="text-gray-500 text-lg">({watchlist.length})</span>
          </div>

          {watchlist.length === 0 ? (
            <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-xl p-12 border border-purple-500/20 text-center">
              <Bookmark className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg mb-2">
                No tienes peliculas en tu lista
              </p>
              <p className="text-gray-500 text-sm">
                Agrega peliculas desde su pagina de detalle para verlas despues
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {watchlist.map((movie) => (
                <Link key={movie.id} to={`/movie/${movie.id}`} className="block">
                  <div className="bg-gray-800/30 rounded-lg overflow-hidden border border-gray-700/50 hover:border-purple-500/50 transition-all hover:bg-gray-800/50 group">
                    <div className="flex flex-col sm:flex-row gap-4 p-4">
                      <div className="flex-shrink-0 w-24 sm:w-20">
                        <div className="aspect-[2/3] rounded-lg overflow-hidden bg-gray-700 shadow-lg">
                          {movie.poster_path ? (
                            <img
                              src={`${imageBaseUrl}/w185${movie.poster_path}`}
                              alt={movie.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-500">
                              <Film className="w-8 h-8" />
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-white mb-1 group-hover:text-purple-400 transition-colors line-clamp-1">
                          {movie.title}
                        </h3>
                        {movie.overview && (
                          <p className="text-gray-300 text-sm leading-relaxed line-clamp-2">
                            {movie.overview}
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

        {/* Watched Movies Section */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <Film className="w-7 h-7 text-purple-400" />
            <h2 className="text-3xl font-bold text-white">
              Peliculas Vistas
            </h2>
            <span className="text-gray-500 text-lg">({watchedMovies.length})</span>
          </div>

          {watchedMovies.length === 0 ? (
            <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-xl p-12 border border-purple-500/20 text-center">
              <Film className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg mb-2">
                Aún no has calificado ninguna película
              </p>
              <p className="text-gray-500 text-sm">
                Explora el catálogo y califica películas para mejorar tus recomendaciones
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {watchedMovies.map((movie) => (
                <Link
                  key={movie.id}
                  to={`/movie/${movie.id}`}
                  className="block"
                >
                  <div className="bg-gray-800/30 rounded-lg overflow-hidden border border-gray-700/50 hover:border-purple-500/50 transition-all hover:bg-gray-800/50 group">
                    <div className="flex flex-col sm:flex-row gap-4 p-4">
                      <div className="flex-shrink-0 w-24 sm:w-20">
                        <div className="aspect-[2/3] rounded-lg overflow-hidden bg-gray-700 shadow-lg">
                          {movie.poster_path ? (
                            <img
                              src={`${imageBaseUrl}/w185${movie.poster_path}`}
                              alt={movie.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-500 text-3xl">
                              🎬
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-bold text-white mb-1 group-hover:text-purple-400 transition-colors line-clamp-1">
                          {movie.title}
                        </h3>
                        
                        {movie.release_date && (
                          <p className="text-gray-400 text-xs mb-2">
                            {new Date(movie.release_date).toLocaleDateString('es-ES', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            })}
                          </p>
                        )}

                        {movie.overview && (
                          <p className="text-gray-300 text-sm leading-relaxed line-clamp-2 mb-2">
                            {movie.overview}
                          </p>
                        )}
                        
                        {movie.director && (
                          <p className="text-gray-400 text-xs">
                            <span className="text-purple-400 font-medium">Director:</span> {movie.director}
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
    </div>
  );
};

export default Profile;