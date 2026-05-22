const API_BASE_URL = import.meta.env.VITE_APP_API_URL;

const SurveyService = {
  checkStatus: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/survey/status/${userId}`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al verificar estado de encuesta');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in checkSurveyStatus:', error);
      throw error;
    }
  },

  submit: async (userId, answers) => {
    try {
      const response = await fetch(`${API_BASE_URL}/survey/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al enviar encuesta');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in submitSurvey:', error);
      throw error;
    }
  },

  getResults: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/survey/results`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al obtener resultados');
      }

      return await response.json();
    } catch (error) {
      console.error('Error in getSurveyResults:', error);
      throw error;
    }
  }
};

export default SurveyService;
