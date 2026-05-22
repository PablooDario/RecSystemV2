import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

const MainLayout = ({ isLoggedIn, onLogout }) => {
  return (
    <div className="min-h-screen bg-slate-900">
      <Navbar isLoggedIn={isLoggedIn} onLogout={onLogout} />
      <main>
        <Outlet />
      </main>
      <footer className="bg-slate-950 py-8 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-400">
          <p>© 2026 CineMatch. Sistema de recomendación inteligente de películas.</p>
          <p className="mt-2 text-sm">Datos proporcionados por The Movie Database (TMDB)</p>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;