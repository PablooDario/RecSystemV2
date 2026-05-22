import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Brain, Heart, Users, Target, Zap } from 'lucide-react';

const TRAIT_INFO = {
  openness: {
    name: 'Apertura a la Experiencia',
    icon: Brain,
    color: 'purple',
    description: 'Refleja tu curiosidad intelectual, creatividad y preferencia por la novedad. Las personas con alta apertura disfrutan del arte, las emociones y las nuevas ideas.'
  },
  conscientiousness: {
    name: 'Responsabilidad',
    icon: Target,
    color: 'blue',
    description: 'Mide tu organización, autodisciplina y orientación a objetivos. Las personas responsables son confiables, trabajadoras y orientadas al logro.'
  },
  extraversion: {
    name: 'Extraversión',
    icon: Zap,
    color: 'yellow',
    description: 'Indica tu nivel de energía social, asertividad y búsqueda de estimulación. Los extrovertidos disfrutan estar rodeados de personas y son sociables.'
  },
  agreeableness: {
    name: 'Amabilidad',
    icon: Heart,
    color: 'pink',
    description: 'Refleja tu compasión, cooperación y confianza en otros. Las personas amables son empáticas, consideradas y valoran la armonía social.'
  },
  neuroticism: {
    name: 'Neuroticismo',
    icon: Users,
    color: 'red',
    description: 'Mide tu estabilidad emocional y tendencia a experimentar emociones negativas. Puntuaciones bajas indican calma y resistencia al estrés.'
  }
};

const PersonalityResults = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const personalityTraits = location.state?.personalityTraits || {};

  const handleStart = () => {
    navigate('/');
  };

  const getColorClasses = (color) => {
    const colors = {
      purple: 'from-purple-500 to-purple-600',
      blue: 'from-blue-500 to-blue-600',
      yellow: 'from-yellow-500 to-yellow-600',
      pink: 'from-pink-500 to-pink-600',
      red: 'from-red-500 to-red-600'
    };
    return colors[color] || colors.purple;
  };

  const getBarColor = (color) => {
    const colors = {
      purple: 'bg-purple-500',
      blue: 'bg-blue-500',
      yellow: 'bg-yellow-500',
      pink: 'bg-pink-500',
      red: 'bg-red-500'
    };
    return colors[color] || colors.purple;
  };

  const getScoreLevel = (score) => {
    if (score < 2.5) return 'Bajo';
    if (score <= 3.5) return 'Intermedio';
    return 'Alto';
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] relative overflow-hidden py-12 px-4">
      {/* Animated background */}
      <div className="absolute inset-0">
        <div 
          className="absolute w-[700px] h-[700px] rounded-full blur-[140px] opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.6) 0%, transparent 70%)',
            animation: 'float1 20s ease-in-out infinite',
            top: '10%',
            left: '-10%'
          }}
        />
        <div 
          className="absolute w-[600px] h-[600px] rounded-full blur-[130px] opacity-25"
          style={{
            background: 'radial-gradient(circle, rgba(236, 72, 153, 0.5) 0%, transparent 70%)',
            animation: 'float2 22s ease-in-out infinite',
            bottom: '5%',
            right: '-8%'
          }}
        />
      </div>

      <div className="relative max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 tracking-tight">
            ¡Registro Completado!
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            Aquí están los resultados de tu perfil de personalidad
          </p>
          <p className="text-gray-400">
            Basado en el modelo de los Cinco Grandes (Big Five)
          </p>
        </div>

        {/* Personality Traits */}
        <div className="space-y-6 mb-12">
          {Object.entries(TRAIT_INFO).map(([key, info]) => {
            const score = personalityTraits[key] || 0;
            const percentage = (score / 5) * 100;
            const Icon = info.icon;

            return (
              <div key={key} className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-2xl opacity-0 group-hover:opacity-100 blur transition duration-300" />
                
                <div className="relative bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 hover:border-purple-500/30 transition-all">
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${getColorClasses(info.color)}`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-bold text-white">
                          {info.name}
                        </h3>
                        <span className="text-2xl font-bold text-white">
                          {score.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm leading-relaxed mb-4">
                        {info.description}
                      </p>
                      
                      {/* Progress Bar */}
                      <div className="w-full h-3 bg-slate-900/50 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${getBarColor(info.color)} transition-all duration-1000 rounded-full`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <div className="flex justify-between items-center text-xs mt-2">
                        <span className="text-gray-400 font-medium">
                          Nivel: <span className="text-white">{getScoreLevel(score)}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Info Box */}
        <div className="relative group mb-8">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl opacity-20 blur" />
          <div className="relative bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
            <p className="text-gray-300 text-center leading-relaxed">
              <span className="text-purple-300 font-semibold">Tu perfil de personalidad</span> se utilizará para 
              brindarte recomendaciones de películas personalizadas. El sistema aprenderá de tus gustos y 
              preferencias para ofrecerte sugerencias cada vez más precisas.
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="text-center">
          <button
            onClick={handleStart}
            className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold text-lg rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-purple-500/50"
          >
            <span className="flex items-center justify-center gap-2">
              Comenzar con las recomendaciones
              <svg 
                className="w-5 h-5 group-hover:translate-x-1 transition-transform" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </span>
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes float1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-50px, 30px) scale(1.1); }
        }
        @keyframes float2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(40px, -25px) scale(0.95); }
        }
      `}</style>
    </div>
  );
};

export default PersonalityResults;