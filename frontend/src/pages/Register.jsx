import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import RegistrationService from '../services/registration.service';

const Register = ({ onContinueToQuestionnaire }) => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    gender: '',
    age: ''
  });

  const [errors, setErrors] = useState({});
  const [usernameChecking, setUsernameChecking] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState(null);

  const checkUsername = async (username) => {
    if (username.length < 3) {
      setUsernameAvailable(null);
      return;
    }

    setUsernameChecking(true);
    try {
      const data = await RegistrationService.checkUsernameAvailability(username);
      setUsernameAvailable(data.available);
    } catch (error) {
      console.error('Error checking username:', error);
      setUsernameAvailable(null);
    } finally {
      setUsernameChecking(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }

    if (name === 'username') {
      checkUsername(value);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.username) {
      newErrors.username = 'El username es requerido';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Mínimo 3 caracteres';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Solo letras, números y guiones bajos';
    } else if (usernameAvailable === false) {
      newErrors.username = 'Este username no está disponible';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Mínimo 6 caracteres';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    if (formData.age && (formData.age < 13 || formData.age > 120)) {
      newErrors.age = 'Edad debe estar entre 13 y 120 años';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateForm()) {
      const userData = {
        username: formData.username.toLowerCase(),
        password: formData.password,
        gender: formData.gender || null,
        age: formData.age ? parseInt(formData.age) : null
      };

      try {
        sessionStorage.setItem('registrationData', JSON.stringify(userData));
      } catch (error) {
        console.error('Error saving to sessionStorage:', error);
      }

      if (onContinueToQuestionnaire) {
        onContinueToQuestionnaire(userData);
      }
      
      navigate('/questionnaire');
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
            Crea tu cuenta
          </h1>
          <p className="text-gray-400 text-lg">
            Completa tus datos para comenzar
          </p>
        </div>

        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
          
          <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 backdrop-blur-sm rounded-2xl p-8 border border-purple-500/20">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Username <span className="text-pink-400">*</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 bg-slate-900/50 border ${
                      errors.username ? 'border-red-500' : 'border-slate-700'
                    } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                    placeholder="tunombre123"
                  />
                  {usernameChecking && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">⏳</span>
                  )}
                  {!usernameChecking && usernameAvailable === true && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-400 text-xl">✓</span>
                  )}
                  {!usernameChecking && usernameAvailable === false && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400 text-xl">✗</span>
                  )}
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  Solo letras, números y guiones bajos (_)
                </p>
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
                  className={`w-full px-4 py-3 bg-slate-900/50 border ${
                    errors.password ? 'border-red-500' : 'border-slate-700'
                  } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                  placeholder="Mínimo 6 caracteres"
                />
                {errors.password && (
                  <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                    <span>⚠</span> {errors.password}
                  </p>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Confirmar contraseña <span className="text-pink-400">*</span>
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 bg-slate-900/50 border ${
                    errors.confirmPassword ? 'border-red-500' : 'border-slate-700'
                  } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                  placeholder="Repite tu contraseña"
                />
                {errors.confirmPassword && (
                  <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                    <span>⚠</span> {errors.confirmPassword}
                  </p>
                )}
              </div>

              {/* Gender */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Género (opcional)
                </label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition cursor-pointer"
                >
                  <option value="">Prefiero no decir</option>
                  <option value="masculino">Masculino</option>
                  <option value="femenino">Femenino</option>
                  <option value="otro">Otro</option>
                </select>
              </div>

              {/* Age */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Edad (opcional)
                </label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 bg-slate-900/50 border ${
                    errors.age ? 'border-red-500' : 'border-slate-700'
                  } rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition`}
                  placeholder="Tu edad"
                  min="13"
                  max="120"
                />
                {errors.age && (
                  <p className="text-red-400 text-sm mt-1 flex items-center gap-1">
                    <span>⚠</span> {errors.age}
                  </p>
                )}
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={usernameAvailable === false}
                className={`w-full py-3.5 font-semibold rounded-xl transition-all duration-300 ${
                  usernameAvailable === false
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white transform hover:scale-[1.02] hover:shadow-lg hover:shadow-purple-500/50'
                }`}
              >
                Continuar al cuestionario
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm">
                ¿Ya tienes cuenta?{' '}
                <a href="/login" className="text-purple-400 hover:text-purple-300 font-medium transition">
                  Iniciar sesión
                </a>
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

export default Register;