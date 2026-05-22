import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react';
import SurveyService from '../services/survey.service';

const questions = [
  {
    id: 'P1',
    text: '¿Qué tan satisfecho estás con las recomendaciones que recibiste en general?',
    type: 'likert',
    labels: ['Muy insatisfecho', 'Insatisfecho', 'Neutral', 'Satisfecho', 'Muy satisfecho']
  },
  {
    id: 'P2',
    text: '¿Las recomendaciones te ayudaron a descubrir películas que no conocías?',
    type: 'likert',
    labels: ['Nunca', 'Casi nunca', 'A veces', 'Casi siempre', 'Siempre']
  },
  {
    id: 'P3',
    text: '¿Cuál sección de recomendaciones te resultó más útil para encontrar películas que te interesan?',
    type: 'choice',
    options: [
      'Basadas en tu personalidad',
      'Películas similares a las que te gustaron',
      'Basadas en personas con gustos similares',
      'Recomendaciones pensadas en ti',
      'Todas por igual',
      'Ninguna'
    ]
  },
  {
    id: 'P4',
    text: '¿Cuál sección te sorprendió más positivamente (te recomendó algo que no esperabas pero te gustó)?',
    type: 'choice',
    options: [
      'Basadas en tu personalidad',
      'Películas similares a las que te gustaron',
      'Basadas en personas con gustos similares',
      'Recomendaciones pensadas en ti',
      'Todas por igual',
      'Ninguna'
    ]
  },
  {
    id: 'P5',
    text: 'De las primeras recomendaciones que recibiste (cuando aún no habías calificado muchas películas), ¿qué tan relevantes te parecieron?',
    type: 'likert',
    labels: ['Nada relevantes', 'Poco relevantes', 'Neutral', 'Relevantes', 'Muy relevantes']
  },
  {
    id: 'P6',
    text: 'Imagina que acabas de registrarte y no has calificado ninguna película. ¿Qué preferirías recibir como primeras recomendaciones?',
    type: 'choice',
    options: [
      'Las películas más populares del momento',
      'Películas seleccionadas según tu personalidad'
    ]
  },
  {
    id: 'P7',
    text: '¿Sentiste que las recomendaciones mejoraron conforme calificaste más películas?',
    type: 'likert',
    labels: ['No mejoró nada', 'Mejoró poco', 'Neutral', 'Mejoró bastante', 'Mejoró mucho']
  },
  {
    id: 'P8',
    text: '¿Sientes que las recomendaciones reflejan tus gustos personales?',
    type: 'likert',
    labels: ['No reflejan mis gustos', 'Reflejan poco', 'Neutral', 'Reflejan bastante', 'Reflejan perfectamente mis gustos']
  }
];

const SurveyModal = ({ userId, onClose, onComplete }) => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const question = questions[currentQuestion];
  const totalQuestions = questions.length;
  const isLastQuestion = currentQuestion === totalQuestions - 1;
  const hasAnswer = answers[question.id] !== undefined;

  const handleLikertSelect = (value) => {
    setAnswers({ ...answers, [question.id]: String(value) });
  };

  const handleChoiceSelect = (option) => {
    setAnswers({ ...answers, [question.id]: option });
  };

  const handleNext = async () => {
    if (isLastQuestion) {
      setSubmitting(true);
      try {
        await SurveyService.submit(userId, answers);
        setSubmitted(true);
        if (onComplete) onComplete();
      } catch (error) {
        console.error('Error submitting survey:', error);
      } finally {
        setSubmitting(false);
      }
    } else {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  if (submitted) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
        <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 max-w-md w-full border border-purple-500/30 shadow-2xl">
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">
              ¡Gracias por tu respuesta!
            </h2>
            <p className="text-gray-400 mb-6">
              Tu opinión nos ayuda a mejorar las recomendaciones para todos los usuarios.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 sm:p-8 max-w-lg w-full border border-purple-500/30 shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-white mb-1">
            Encuesta de satisfacción
          </h2>
          <p className="text-gray-400 text-sm">
            Ayúdanos a mejorar tus recomendaciones
          </p>
        </div>

        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">
              Pregunta {currentQuestion + 1} de {totalQuestions}
            </span>
            <span className="text-sm text-purple-400">
              {Math.round(((currentQuestion + 1) / totalQuestions) * 100)}%
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / totalQuestions) * 100}%` }}
            />
          </div>
        </div>

        {/* Question */}
        <div className="mb-8">
          <p className="text-white text-lg font-medium mb-6">
            {question.text}
          </p>

          {question.type === 'likert' && (
            <div className="space-y-3">
              {question.labels.map((label, index) => {
                const value = index + 1;
                const isSelected = answers[question.id] === String(value);
                return (
                  <button
                    key={value}
                    onClick={() => handleLikertSelect(value)}
                    className={`w-full text-left px-4 py-3 rounded-lg border transition-all duration-200 ${
                      isSelected
                        ? 'border-purple-500 bg-purple-500/20 text-white'
                        : 'border-slate-600 bg-slate-700/50 text-gray-300 hover:border-purple-400 hover:bg-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'border-purple-500' : 'border-slate-500'
                      }`}>
                        {isSelected && (
                          <div className="w-2.5 h-2.5 rounded-full bg-purple-500" />
                        )}
                      </div>
                      <span className="text-sm">{value} - {label}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {question.type === 'choice' && (
            <div className="space-y-3">
              {question.options.map((option) => {
                const isSelected = answers[question.id] === option;
                return (
                  <button
                    key={option}
                    onClick={() => handleChoiceSelect(option)}
                    className={`w-full text-left px-4 py-3 rounded-lg border transition-all duration-200 ${
                      isSelected
                        ? 'border-purple-500 bg-purple-500/20 text-white'
                        : 'border-slate-600 bg-slate-700/50 text-gray-300 hover:border-purple-400 hover:bg-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'border-purple-500' : 'border-slate-500'
                      }`}>
                        {isSelected && (
                          <div className="w-2.5 h-2.5 rounded-full bg-purple-500" />
                        )}
                      </div>
                      <span className="text-sm">{option}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between items-center">
          <button
            onClick={handleBack}
            disabled={currentQuestion === 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentQuestion === 0
                ? 'text-gray-600 cursor-not-allowed'
                : 'text-gray-300 hover:text-white hover:bg-slate-700'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Anterior
          </button>

          <button
            onClick={handleNext}
            disabled={!hasAnswer || submitting}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              hasAnswer && !submitting
                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                : 'bg-slate-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Enviando...
              </>
            ) : isLastQuestion ? (
              'Enviar'
            ) : (
              <>
                Siguiente
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SurveyModal;
