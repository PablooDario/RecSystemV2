import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useLocation } from 'react-router-dom';

import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Questionnaire from './pages/Questionnaire';
import MovieDetail from './pages/MovieDetail';
import Profile from './pages/Profile';
import SearchResult from './pages/SearchResult';
import PersonalityResults from './pages/PersonalityResults';
import Recommendations from './pages/Recommendations';
import LoginService from './services/login.service';

// Minimal ScrollToTop component
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0); // Scroll to top on route change
  }, [pathname]);

  return null;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authKey, setAuthKey] = useState(0);
  const [registrationData, setRegistrationData] = useState(null);

  // Check auth status on mount and when storage changes
  useEffect(() => {
    const checkAuth = () => {
      const isAuth = LoginService.isAuthenticated();
      const username = LoginService.getCurrentUser();

      if (isAuth && username) {
        setIsLoggedIn(true);
        setCurrentUser(username);
      } else {
        setIsLoggedIn(false);
        setCurrentUser(null);
      }
    };

    checkAuth();
    window.addEventListener('storage', checkAuth);
    const interval = setInterval(checkAuth, 500);

    return () => {
      window.removeEventListener('storage', checkAuth);
      clearInterval(interval);
    };
  }, []);

  // Recover registration data from session storage
  useEffect(() => {
    try {
      const savedData = sessionStorage.getItem('registrationData');
      if (savedData) setRegistrationData(JSON.parse(savedData));
    } catch (error) {
      console.error('Error recovering registration data:', error);
    }
  }, []);

  const handleLogin = (userData) => {
    setIsLoggedIn(true);
    setCurrentUser(userData.username);
    setAuthKey((prev) => prev + 1);
  };

  const handleLogout = () => {
    LoginService.logout();
    setIsLoggedIn(false);
    setCurrentUser(null);
    setAuthKey((prev) => prev + 1);
  };

  const handleContinueToQuestionnaire = (userData) => {
    setRegistrationData(userData);
  };

  const handleRegistrationComplete = () => {
    setRegistrationData(null);
  };

  return (
    <Router>
      <ScrollToTop />
      <Routes>
        <Route
          element={
            <MainLayout
              isLoggedIn={isLoggedIn}
              onLogout={handleLogout}
              currentUser={currentUser}
            />
          }
        >
          <Route path="/" element={<Home key={authKey} />} />
          <Route path="/movie/:id" element={<MovieDetail key={authKey} />} />
          <Route path="/profile" element={<Profile key={authKey} />} />
          <Route path="/search" element={<SearchResult key={authKey} />} />
          <Route path="/recommendations" element={<Recommendations key={authKey} />} />
        </Route>

        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route
            path="/register"
            element={
              <Register onContinueToQuestionnaire={handleContinueToQuestionnaire} />
            }
          />
          <Route
            path="/questionnaire"
            element={
              <Questionnaire
                userData={registrationData}
                onComplete={handleRegistrationComplete}
              />
            }
          />
          <Route path="/personality-results" element={<PersonalityResults />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
