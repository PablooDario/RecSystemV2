const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const LoginService = {
  login: async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username: username.toLowerCase(),
          password 
        })
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Usuario o contraseña incorrectos');
        } else if (response.status === 404) {
          throw new Error('Usuario no encontrado');
        } else {
          throw new Error(data.detail || 'Error al iniciar sesión');
        }
      }

      // Store user data in localStorage for persistent session
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('username', data.username);
      localStorage.setItem('isAuthenticated', 'true');

      return data;
    } catch (error) {
      console.error('Error in login:', error);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('isAuthenticated');
  },

  isAuthenticated: () => {
    return localStorage.getItem('isAuthenticated') === 'true';
  },

  getCurrentUser: () => {
    return localStorage.getItem('username');
  },

  getUserId: () => {
    const userId = localStorage.getItem('user_id');
    return userId ? parseInt(userId) : null;
  }
};

export default LoginService;