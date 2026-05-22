const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const RegistrationService = {
  /**
   * Check if a username is available
   */
  checkUsernameAvailability: async (username) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/registration/check-username`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username })
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking username availability:', error);
      throw error;
    }
  },

  /**
   * Register a new user with questionnaire answers
   */
  registerUser: async (registrationData) => {
    try {
      console.log('Registering user with data:', registrationData);
      const response = await fetch(`${API_BASE_URL}/registration/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      return data;
    } catch (error) {
      console.error('Error registering user:', error);
      throw error;
    }
  }
};

export default RegistrationService;