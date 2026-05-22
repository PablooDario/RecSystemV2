import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import RegistrationService from '../services/registration.service';
import LoginService from '../services/login.service';

const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const QUESTIONS = [
  { id: 1, text: "Compasivo/a, con un gran corazón" },
  { id: 2, text: "Relajado/a, que gestiona bien el estrés" },
  { id: 3, text: "Respetuoso/a, que trata a los demás con respeto" },
  { id: 4, text: "Formal, constante" },
  { id: 5, text: "Que tiende a estar callado/a" },
  { id: 6, text: "Fascinado/a por el arte, la música o la literatura" },
  { id: 7, text: "Dominante, que actúa como líder" },
  { id: 8, text: "Emocionalmente estable, que no se altera con facilidad" },
  { id: 9, text: "Que mantiene todo limpio y ordenado" },
  { id: 10, text: "Lleno/a de energía" },
  { id: 11, text: "Tenaz, que trabaja hasta terminar la tarea" },
  { id: 12, text: "Que tiende a sentirse deprimido/a, melancólico/a" },
  { id: 13, text: "Con poco interés por ideas abstractas" },
  { id: 14, text: "Que piensa bien de la gente" },
  { id: 15, text: "Original, que aporta ideas nuevas" },
  { id: 16, text: "Abierto/a, sociable" },
  { id: 17, text: "Que tiende a ser desorganizado/a" },
  { id: 18, text: "Con pocos intereses artísticos" },
  { id: 19, text: "Que se mantiene optimista después de sufrir un contratiempo" },
  { id: 20, text: "Que siente curiosidad por gran variedad de cosas" },
  { id: 21, text: "Variable, con notables cambios de humor" },
  { id: 22, text: "Que siente poca compasión hacia los demás" },
  { id: 23, text: "A quien le cuesta empezar las tareas" },
  { id: 24, text: "Menos activo/a que otras personas" },
  { id: 25, text: "Que puede ser algo descuidado/a" },
  { id: 26, text: "Con poca creatividad" },
  { id: 27, text: "Que se preocupa mucho" },
  { id: 28, text: "A quien le es difícil influir en los demás" },
  { id: 29, text: "Que a veces es grosero/a con los demás" },
  { id: 30, text: "Que desconfía de las intenciones de los demás" }
];

const LIKERT_OPTIONS = [
  { value: 1, label: "Totalmente en desacuerdo", short: "Muy en desacuerdo" },
  { value: 2, label: "En desacuerdo", short: "En desacuerdo" },
  { value: 3, label: "Neutral", short: "Neutral" },
  { value: 4, label: "De acuerdo", short: "De acuerdo" },
  { value: 5, label: "Totalmente de acuerdo", short: "Muy de acuerdo" }
];

const QUESTIONS_PER_PAGE = 5;
const TOTAL_PAGES = 6;

const Questionnaire = ({ userData, onComplete }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isRetake = location.state?.retake === true;

  const [currentPage, setCurrentPage] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isNavigating, setIsNavigating] = useState(false);

  useEffect(() => {
    if (isRetake) return;
    if (!userData && !isNavigating) {
      try {
        const savedData = sessionStorage.getItem('registrationData');
        if (!savedData) {
          console.warn('No registration data found, redirecting to register');
          navigate('/register');
        }
      } catch (error) {
        console.error('Error reading sessionStorage:', error);
        navigate('/register');
      }
    }
  }, [userData, navigate, isNavigating, isRetake]);

  const getCurrentPageQuestions = () => {
    const startIndex = currentPage * QUESTIONS_PER_PAGE;
    const endIndex = startIndex + QUESTIONS_PER_PAGE;
    return QUESTIONS.slice(startIndex, endIndex);
  };

  const isCurrentPageComplete = () => {
    const currentQuestions = getCurrentPageQuestions();
    return currentQuestions.every(q => answers[q.id] !== undefined);
  };

  const isAllQuestionsAnswered = () => {
    return QUESTIONS.every(q => answers[q.id] !== undefined);
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleNext = () => {
    if (currentPage < TOTAL_PAGES - 1) {
      setCurrentPage(prev => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSubmit = async () => {
    if (!isAllQuestionsAnswered()) {
      setError('Por favor responde todas las preguntas antes de finalizar');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (isRetake) {
        const userId = LoginService.getUserId();
        if (!userId) throw new Error('No hay sesion activa');

        const response = await fetch(`${API_BASE_URL}/personality/${userId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Error al actualizar personalidad');
        }

        const result = await response.json();
        setIsNavigating(true);
        navigate('/personality-results', {
          state: { personalityTraits: result }
        });
      } else {
        let userInfo = userData;
        if (!userInfo) {
          const savedData = sessionStorage.getItem('registrationData');
          if (savedData) {
            userInfo = JSON.parse(savedData);
          }
        }

        if (!userInfo) {
          throw new Error('No se encontraron datos de registro');
        }

        const registrationData = {
          username: userInfo.username,
          password: userInfo.password,
          gender: userInfo.gender,
          age: userInfo.age,
          questionnaire_answers: { answers }
        };

        const result = await RegistrationService.registerUser(registrationData);

        localStorage.setItem('user_id', result.user_id);
        localStorage.setItem('username', result.username);
        localStorage.setItem('isAuthenticated', 'true');

        try {
          sessionStorage.removeItem('registrationData');
        } catch (error) {
          console.error('Error clearing sessionStorage:', error);
        }

        if (onComplete) {
          onComplete(result);
        }

        setIsNavigating(true);
        navigate('/personality-results', {
          state: { personalityTraits: result.personality_traits }
        });
      }
    } catch (err) {
      console.error('Error en el registro:', err);
      setError(err.message || 'Error al procesar. Por favor intenta de nuevo.');
      setIsSubmitting(false);
    }
  };

  const answeredCount = Object.keys(answers).length;
  const progress = (answeredCount / QUESTIONS.length) * 100;
  const currentQuestions = getCurrentPageQuestions();

  return (
    <div className="min-h-screen bg-[#0a0e1a] relative overflow-hidden py-12 px-4">
      <div className="absolute inset-0">
        <div 
          className="absolute w-[650px] h-[650px] rounded-full blur-[130px] opacity-25"
          style={{
            background: 'radial-gradient(circle, rgba(147, 51, 234, 0.7) 0%, transparent 70%)',
            animation: 'float1 20s ease-in-out infinite',
            top: '5%',
            right: '-10%'
          }}
        />
        <div 
          className="absolute w-[550px] h-[550px] rounded-full blur-[120px] opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.6) 0%, transparent 70%)',
            animation: 'float2 18s ease-in-out infinite',
            bottom: '15%',
            left: '-8%'
          }}
        />
      </div>

      <div className="relative max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            Cuestionario de Personalidad
          </h1>
          <p className="text-gray-400 text-lg">
            Responde con sinceridad. No hay respuestas correctas o incorrectas.
          </p>
        </div>

        <div className="relative group mb-8">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl opacity-20 blur" />
          <div className="relative bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
            <div className="flex justify-between items-center mb-3 text-sm">
              <span className="text-gray-400">Página {currentPage + 1} de {TOTAL_PAGES}</span>
              <span className="text-purple-300 font-medium">{answeredCount} / {QUESTIONS.length} respondidas</span>
            </div>
            <div className="w-full h-3 bg-slate-900/50 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        <div className="space-y-6 mb-8">
          <p className="text-gray-300 text-center mb-8 bg-purple-500/10 border border-purple-500/20 rounded-xl p-4">
            Me describo como alguien...
          </p>

          {currentQuestions.map((question, index) => (
            <div key={question.id} className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-2xl opacity-0 group-hover:opacity-100 blur transition duration-300" />
              
              <div className="relative bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 hover:border-purple-500/30 transition-all">
                <div className="mb-4">
                  <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
                    Pregunta {currentPage * QUESTIONS_PER_PAGE + index + 1}
                  </span>
                  <p className="text-lg text-white mt-2">
                    {question.text}
                  </p>
                </div>

                <div className="grid grid-cols-5 gap-2">
                  {LIKERT_OPTIONS.map(option => (
                    <button
                      key={option.value}
                      onClick={() => handleAnswerChange(question.id, option.value)}
                      className={`relative p-3 rounded-xl border-2 transition-all ${
                        answers[question.id] === option.value
                          ? 'bg-purple-500/20 border-purple-500 shadow-lg shadow-purple-500/30'
                          : 'bg-slate-900/50 border-slate-700 hover:border-slate-600 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="text-center">
                        <div className={`text-2xl font-bold mb-1 ${
                          answers[question.id] === option.value ? 'text-purple-300' : 'text-white'
                        }`}>
                          {option.value}
                        </div>
                        <div className={`text-xs leading-tight ${
                          answers[question.id] === option.value ? 'text-gray-300' : 'text-gray-500'
                        }`}>
                          {option.short}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
            <span className="text-2xl">⚠</span>
            <p className="text-red-300">{error}</p>
          </div>
        )}

        <div className="flex items-center justify-between gap-4">
          <button
            onClick={handlePrevious}
            disabled={currentPage === 0}
            className={`px-6 py-3 rounded-xl font-medium transition-all ${
              currentPage === 0
                ? 'bg-slate-800/50 text-gray-600 cursor-not-allowed'
                : 'bg-slate-800 text-white hover:bg-slate-700 border border-slate-600 hover:border-slate-500'
            }`}
          >
            ← Anterior
          </button>

          <div className="flex gap-2">
            {Array.from({ length: TOTAL_PAGES }).map((_, index) => (
              <div
                key={index}
                className={`h-2 rounded-full transition-all ${
                  index === currentPage 
                    ? 'w-8 bg-purple-500' 
                    : index < currentPage 
                      ? 'w-2 bg-purple-600/50' 
                      : 'w-2 bg-slate-700'
                }`}
              />
            ))}
          </div>

          {currentPage < TOTAL_PAGES - 1 ? (
            <button
              onClick={handleNext}
              disabled={!isCurrentPageComplete()}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                !isCurrentPageComplete()
                  ? 'bg-slate-800/50 text-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 shadow-lg shadow-purple-500/30'
              }`}
            >
              Siguiente →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!isAllQuestionsAnswered() || isSubmitting}
              className={`px-8 py-3 rounded-xl font-semibold transition-all ${
                !isAllQuestionsAnswered() || isSubmitting
                  ? 'bg-slate-800/50 text-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-pink-600 to-purple-600 text-white hover:from-pink-500 hover:to-purple-500 shadow-lg shadow-pink-500/30 transform hover:scale-105'
              }`}
            >
              {isSubmitting ? 'Procesando...' : 'Finalizar'}
            </button>
          )}
        </div>

        {!isCurrentPageComplete() && (
          <p className="text-center text-amber-400 text-sm mt-4">
            Completa todas las preguntas de esta página para continuar
          </p>
        )}
      </div>

      <style jsx>{`
        @keyframes float1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-60px, 40px) scale(1.1); }
        }
        @keyframes float2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(50px, -30px) scale(0.95); }
        }
      `}</style>
    </div>
  );
};

export default Questionnaire;