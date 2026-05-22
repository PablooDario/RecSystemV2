import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogIn, UserPlus, Menu, X } from 'lucide-react';

const Navbar = ({ isLoggedIn, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleRecommendationsClick = () => {
    if (isLoggedIn) {
      navigate('/recommendations');
    } else {
      navigate('/login');
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">AI</span>
              </div>
              <span className="text-white font-bold text-xl hidden sm:block">CineMatch</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <button
              onClick={handleRecommendationsClick}
              className="text-gray-300 hover:text-white transition-colors"
            >
              Recomendaciones
            </button>

            {/* Search Bar */}
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar películas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-64 px-4 py-2 pl-10 bg-slate-800 text-white rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button onClick={handleSearch} className="absolute left-3 top-2.5">
                <Search className="w-5 h-5 text-gray-400 hover:text-white transition-colors" />
              </button>
            </div>

            {/* Auth Buttons */}
            {!isLoggedIn ? (
              <div className="flex items-center space-x-4">
                <Link
                  to="/login"
                  className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
                >
                  <LogIn className="w-5 h-5" />
                  <span>Iniciar sesión</span>
                </Link>
                <Link
                  to="/register"
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-full transition-colors"
                >
                  <UserPlus className="w-5 h-5" />
                  <span>Registrarse</span>
                </Link>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link to="/profile" className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors">
                  <User className="w-5 h-5" />
                  <span>Perfil</span>
                </Link>
                <button
                  onClick={onLogout}
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-gray-300 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-slate-900 border-t border-slate-800">
          <div className="px-4 py-4 space-y-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar películas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-4 py-2 bg-slate-800 text-white rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <button
              onClick={handleRecommendationsClick}
              className="block w-full text-left text-gray-300 hover:text-white"
            >
              Recomendaciones
            </button>
            {!isLoggedIn ? (
              <>
                <Link to="/login" className="block text-gray-300 hover:text-white">
                  Iniciar sesión
                </Link>
                <Link to="/register" className="block text-purple-400 hover:text-purple-300">
                  Registrarse
                </Link>
              </>
            ) : (
              <>
                <Link to="/profile" className="block text-gray-300 hover:text-white">
                  Perfil
                </Link>
                <button onClick={onLogout} className="block w-full text-left text-gray-300 hover:text-white">
                  Cerrar sesión
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;