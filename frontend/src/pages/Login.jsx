import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import LoginService from '../services/login.service';

const Login = ({ onLogin }) => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
    if (loginError) {
      setLoginError(null);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username) {
      newErrors.username = 'El username es requerido';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Mínimo 3 caracteres';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setLoginError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await LoginService.login(formData.username, formData.password);

      if (onLogin) {
        onLogin(result);
      }

      navigate('/');
      
    } catch (error) {
      console.error('Error en login:', error);
      setLoginError(error.message || 'Error al iniciar sesión. Por favor intenta de nuevo.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] relative overflow-hidden flex items-center justify-center py-20 px-4">
      <div className="absolute inset-0">
        <div 
          className="absolute w-[600px] h-[600px] rounded-full blur-[120px] opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.6) 0%, rgba(139, 92, 246, 0) 70%)',
            animation: 'float1 18s ease-in-out infinite',
            top: '10%',
            left: '-10%'
          }}
        />
        <div 
          className="absolute w-[500px] h-[500px] rounded-full blur-[110px] opacity-25"
          style={{
            background: 'radial-gradient(circle, rgba(236, 72, 153, 0.5) 0%, rgba(236, 72, 153, 0) 70%)',
            animation: 'float2 22s ease-in-out infinite',
            bottom: '10%',
            right: '-5%'
          }}
        />
      </div>

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            Bienvenido de nuevo
          </h1>
          <p className="text-gray-400 text-lg">
            Ingresa tus credenciales para continuar
          </p>
        </div>

        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
          
          <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20">
            <form onSubmit={handleSubmit} className="space-y-5">
              {loginError && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
                  <span className="text-red-400 text-xl flex-shrink-0">⚠</span>
                  <p className="text-red-300 text-sm">{loginError}</p>
                </div>
              )}

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Username <span className="text-pink-400">*</span>
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  autoComplete="username"
                  className={`w-full px-4 py-3 bg-slate-900/50 border ${
                    errors.username ? 'border-red-500' : 'border-slate-700'
                  } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                  placeholder="tunombre123"
                  disabled={isSubmitting}
                />
                {errors.username && (
                  <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                    <span>⚠</span> {errors.username}
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Contraseña <span className="text-pink-400">*</span>
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  className={`w-full px-4 py-3 bg-slate-900/50 border ${
                    errors.password ? 'border-red-500' : 'border-slate-700'
                  } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                  placeholder="Tu contraseña"
                  disabled={isSubmitting}
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                    <span>⚠</span> {errors.password}
                  </p>
                )}
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className={`w-full py-3.5 font-semibold rounded-xl transition-all duration-300 ${
                  isSubmitting
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white transform hover:scale-[1.02] hover:shadow-lg hover:shadow-purple-500/50'
                }`}
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Iniciando sesión...
                  </span>
                ) : (
                  'Iniciar sesión'
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm">
                ¿Eres nuevo?{' '}
                <Link 
                  to="/register" 
                  className="text-purple-400 hover:text-purple-300 font-medium transition"
                >
                  Regístrate
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(50px, -30px) scale(1.1); }
        }
        @keyframes float2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-40px, 30px) scale(0.9); }
        }
      `}</style>
    </div>
  );
};

export default Login;