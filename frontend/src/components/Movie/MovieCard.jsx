import React from 'react';
import { useNavigate } from 'react-router-dom';

const MovieCard = ({ movie, imageBaseUrl }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/movie/${movie.id}`);
  };

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-48 cursor-pointer group"
    >
      <div className="relative overflow-hidden rounded-lg shadow-lg transition-transform transform group-hover:scale-105">
        <img
          src={movie.poster_path 
            ? `${imageBaseUrl}/w500${movie.poster_path}`
            : 'https://via.placeholder.com/500x750?text=No+Image'
          }
          alt={movie.title}
          className="w-full h-72 object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="absolute bottom-0 p-4 w-full">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold text-sm">
                {movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>
      <h3 className="mt-2 text-white font-medium truncate">{movie.title}</h3>
      <p className="text-gray-400 text-sm">{movie.release_date?.split('-')[0] || 'N/A'}</p>
    </div>
  );
};

export default MovieCard;