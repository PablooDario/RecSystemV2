import React from 'react';
import { Play } from 'lucide-react';

const HeroSection = ({ backdropPath, imageBaseUrl, onGetStarted }) => {
  const backdropUrl = backdropPath 
    ? `${imageBaseUrl}/original${backdropPath}` 
    : '/placeholder-backdrop.jpg';

  return (
    <div className="relative h-[85vh] overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0">
        <img
          src={backdropUrl}
          alt="Hero backdrop"
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = '/placeholder-backdrop.jpg';
          }}
        />
        {/* Dark gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0a0e1a] via-[#0a0e1a]/70 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0a0e1a]/90 via-transparent to-[#0a0e1a]/50" />
      </div>

      {/* Content */}
      <div className="relative h-full flex items-center">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="max-w-3xl">

            {/* Main Heading */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
              Descubre películas que{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                realmente amarás
              </span>
            </h1>

            {/* Description */}
            <p className="text-xl text-gray-300 mb-10 leading-relaxed">
              Recomendaciones personalizadas basadas en tu personalidad y gustos únicos. 
              Deja que la inteligencia artificial encuentre tu próxima película favorita.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={onGetStarted}
                className="group relative px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-purple-500/50"
              >
                <span className="flex items-center justify-center gap-2">
                  Comenzar ahora
                  <Play className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </button>
            </div>

            {/* Stats */}
            <div className="flex flex-wrap gap-8 mt-12 pt-12 border-t border-slate-800">
              <div>
                <div className="text-3xl font-bold text-white mb-1">3800+</div>
                <div className="text-sm text-gray-400">Películas disponibles</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-white mb-1">24/7</div>
                <div className="text-sm text-gray-400">Descubrimiento continuo</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeroSection;