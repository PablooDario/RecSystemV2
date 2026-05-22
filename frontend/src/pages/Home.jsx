import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import HeroSection from '../components/HeroSection';
import MovieCarousel from '../components/Movie/MovieCarousel';
import { getPopularMovies, getRandomBackdrop } from '../services/movie.service';
import LoginService from '../services/login.service';

const Home = () => {
  const navigate = useNavigate();
  const [heroBackdrop, setHeroBackdrop] = useState(null);
  const [popularMovies, setPopularMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const authenticated = LoginService.isAuthenticated();
      setIsLoggedIn(authenticated);
    };

    checkAuth();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const movies = await getPopularMovies();
        setPopularMovies(movies);
        
        const backdrop = await getRandomBackdrop();
        setHeroBackdrop(backdrop);
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const imageBaseUrl = 'https://image.tmdb.org/t/p';

  const handleGetStarted = () => {
    if (isLoggedIn) {
      navigate('/recommendations');
    } else {
      navigate('/login');
    }
  };

  return (
    <>
      <HeroSection 
        backdropPath={heroBackdrop} 
        imageBaseUrl={imageBaseUrl}
        onGetStarted={handleGetStarted}
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-white text-xl">Cargando películas...</div>
        </div>
      ) : (
        <MovieCarousel 
          movies={popularMovies} 
          title="Películas populares ahora"
          imageBaseUrl={imageBaseUrl}
        />
      )}

      {/* System Explanation Section */}
      <div className="relative py-32 bg-[#0a0e1a] overflow-hidden">
        <div className="absolute inset-0">
          <div 
            className="absolute w-[700px] h-[700px] rounded-full blur-[140px] opacity-35"
            style={{
              background: 'radial-gradient(circle, rgba(59, 130, 246, 0.8) 0%, rgba(59, 130, 246, 0) 70%)',
              animation: 'float1 18s ease-in-out infinite',
              top: '5%',
              left: '-15%'
            }}
          ></div>
          
          <div 
            className="absolute w-[550px] h-[550px] rounded-full blur-[120px] opacity-30"
            style={{
              background: 'radial-gradient(circle, rgba(147, 51, 234, 0.7) 0%, rgba(147, 51, 234, 0) 70%)',
              animation: 'float2 22s ease-in-out infinite',
              top: '45%',
              right: '-8%'
            }}
          ></div>
          
          <div 
            className="absolute w-[650px] h-[650px] rounded-full blur-[130px] opacity-35"
            style={{
              background: 'radial-gradient(circle, rgba(251, 146, 60, 0.8) 0%, rgba(251, 146, 60, 0) 70%)',
              animation: 'float3 20s ease-in-out infinite',
              bottom: '10%',
              left: '25%'
            }}
          ></div>
          
          <div 
            className="absolute w-[500px] h-[500px] rounded-full blur-[110px] opacity-25"
            style={{
              background: 'radial-gradient(circle, rgba(96, 165, 250, 0.6) 0%, rgba(96, 165, 250, 0) 70%)',
              animation: 'float4 24s ease-in-out infinite',
              top: '55%',
              left: '5%'
            }}
          ></div>
          
          <div className="absolute inset-0 opacity-[0.02]" style={{
            backgroundImage: `
              linear-gradient(rgba(139, 92, 246, 0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(139, 92, 246, 0.3) 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px'
          }}></div>
          
          <div className="absolute inset-0 opacity-[0.015]" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' /%3E%3C/svg%3E")`
          }}></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-24">
            <h3>
              <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto leading-relaxed mt-8">
                Diseñada para que lleves un <span className="text-purple-300 font-medium">registro inteligente</span> de las películas que ves y calificas
              </p>
            </h3>
          </div>

          <div className="max-w-4xl mx-auto mb-20">
            <p className="text-xl text-gray-300 leading-relaxed text-center">
              <h2 className="text-6xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                ¿Cómo funciona<span className="text-purple-400">?</span>
              </h2>
              Con un pequeño formulario obtendremos tu personalidad. Así, combinando tus gustos cinematográficos con tu perfil único, el sistema <span className="text-purple-300 font-semibold bg-purple-500/10 px-2 py-1 rounded">aprende y evoluciona</span> para ofrecerte recomendaciones cada vez más precisas y personalizadas.
            </p>
          </div>

          <div className="max-w-5xl mx-auto mb-24">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-blue-600 rounded-3xl blur-xl opacity-0 group-hover:opacity-30 transition duration-500"></div>
              
              <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 backdrop-blur-sm rounded-3xl p-12 border border-purple-500/20">
                <h3 className="text-3xl md:text-4xl font-bold text-white mb-8 text-center leading-tight">
                  ¿Por qué es diferente?
                </h3>
                <p className="text-lg md:text-xl text-gray-300 leading-relaxed text-center">
                  El sistema de recomendación no solo toma en cuenta tus gustos, sino también <span className="text-purple-300 font-semibold">tus rasgos de personalidad</span>. Basándose en usuarios con perfiles y preferencias similares, <span className="text-white font-semibold">el sistema comprende profundamente tus necesidades</span> para ofrecerte recomendaciones que realmente resuenen contigo.
                </p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl opacity-0 group-hover:opacity-20 blur transition duration-500"></div>
              <div className="relative bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 h-full">
                <div className="mb-6">
                  <div className="w-14 h-14 bg-purple-500/10 rounded-xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                </div>
                
                <h3 className="text-xl font-bold text-white mb-4">
                  Análisis de Personalidad
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  Entendemos tu perfil único a través de cuestionarios y comportamiento, creando un mapa detallado de tus preferencias
                </p>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl opacity-0 group-hover:opacity-20 blur transition duration-500"></div>
              <div className="relative bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 h-full">
                <div className="mb-6">
                  <div className="w-14 h-14 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                </div>
                
                <h3 className="text-xl font-bold text-white mb-4">
                  Contenido Inteligente
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  Analizamos géneros, temas y características que te gustan para construir tu perfil cinematográfico ideal
                </p>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-600 to-purple-600 rounded-2xl opacity-0 group-hover:opacity-20 blur transition duration-500"></div>
              <div className="relative bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 hover:border-pink-500/50 transition-all duration-300 h-full">
                <div className="mb-6">
                  <div className="w-14 h-14 bg-pink-500/10 rounded-xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                </div>
                
                <h3 className="text-xl font-bold text-white mb-4">
                  Filtrado Colaborativo
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  Aprendemos de usuarios con gustos similares a los tuyos para descubrir joyas ocultas que amarás
                </p>
              </div>
            </div>
          </div>

          <div className="mt-24 text-center">
            <p className="text-gray-500 text-sm tracking-wide">
              Cuanto más uses la plataforma, más precisas serán tus recomendaciones
            </p>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-500/20 to-transparent"></div>
      </div>

      <style jsx>{`
        @keyframes float1 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(80%, 30%) scale(1.15);
          }
          66% {
            transform: translate(-50%, -20%) scale(0.9);
          }
        }

        @keyframes float2 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(-60%, -35%) scale(1.1);
          }
          66% {
            transform: translate(40%, 25%) scale(0.85);
          }
        }

        @keyframes float3 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(-55%, 40%) scale(1.12);
          }
          66% {
            transform: translate(60%, -30%) scale(0.88);
          }
        }

        @keyframes float4 {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(70%, -25%) scale(0.9);
          }
          66% {
            transform: translate(-40%, 35%) scale(1.15);
          }
        }
      `}</style>
    </>
  );
};

export default Home;