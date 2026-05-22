import React, { useState, useEffect } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import LoginService from '../services/login.service';
import RecommendationService from '../services/recommendations.service';
import SurveyService from '../services/survey.service';
import MovieCarousel from '../components/Movie/MovieCarousel';
import SurveyModal from '../components/SurveyModal';

const Recommendations = () => {
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSurvey, setShowSurvey] = useState(false);
  const [ratingCount, setRatingCount] = useState(0);
  const imageBaseUrl = 'https://image.tmdb.org/t/p';

  const checkSurveyEligibility = async (userId, ratingsCount) => {
    if (ratingsCount < 16) return;

    const dismissedKey = `survey_dismissed_${userId}`;
    if (sessionStorage.getItem(dismissedKey)) return;

    try {
      const status = await SurveyService.checkStatus(userId);
      if (!status.completed) {
        setShowSurvey(true);
      }
    } catch (err) {
      console.error('Error checking survey status:', err);
    }
  };

  const handleSurveyClose = () => {
    const userId = LoginService.getUserId();
    sessionStorage.setItem(`survey_dismissed_${userId}`, 'true');
    setShowSurvey(false);
  };

  const handleSurveyComplete = () => {
    // Survey was submitted successfully; modal will show thank you then close
  };

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const userId = LoginService.getUserId();

      if (!userId) {
        setError('Debes iniciar sesion para ver recomendaciones');
        setLoading(false);
        return;
      }

      const result = await RecommendationService.getRecommendations(userId);
      setSections(result.sections);
      setRatingCount(result.rating_count || 0);
      setLoading(false);

      // Check survey eligibility after recommendations load
      checkSurveyEligibility(userId, result.rating_count || 0);
    } catch (err) {
      console.error('Error loading recommendations:', err);
      setError(err.message || 'Error al cargar recomendaciones');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mb-4"></div>
          <p className="text-white text-xl">Generando recomendaciones personalizadas...</p>
          <p className="text-gray-400 text-sm mt-2">Analizando tus preferencias</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4">
        <div className="max-w-3xl mx-auto mt-20">
          <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-2xl p-8 border border-red-500/20 text-center">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">No hay recomendaciones disponibles</h2>
            <p className="text-gray-400 mb-6">{error}</p>

            <button
              onClick={fetchRecommendations}
              className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Intentar de nuevo
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 pt-20 px-4 pb-12">
      {/* Survey Modal */}
      {showSurvey && (
        <SurveyModal
          userId={LoginService.getUserId()}
          onClose={handleSurveyClose}
          onComplete={handleSurveyComplete}
        />
      )}

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Peliculas que te van a
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400"> encantar</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Recomendaciones generadas con inteligencia artificial
          </p>
        </div>

        {/* Recommendation Sections */}
        <div className="space-y-12">
          {sections.map((section, index) => (
            <div key={index}>
              {section.movies && section.movies.length > 0 && (
                <MovieCarousel
                  movies={section.movies}
                  title={section.title}
                  imageBaseUrl={imageBaseUrl}
                />
              )}
            </div>
          ))}
        </div>

        {sections.length === 0 && (
          <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-2xl p-12 border border-purple-500/20 text-center">
            <p className="text-gray-400 text-lg mb-2">
              No hay suficientes datos para generar recomendaciones
            </p>
            <p className="text-gray-500 text-sm">
              Califica mas peliculas para obtener mejores recomendaciones
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Recommendations;
