import { BASE_API_URL, uuid } from "./Common";
import axios from 'axios';

// Create an axios instance with base configuration
const api = axios.create({
    baseURL: BASE_API_URL
});

// Add request interceptor to include session ID in headers
api.interceptors.request.use(
    (config) => {
        const sessionId = localStorage.getItem('userSessionId');
        if (sessionId) {
            config.headers['X-Session-ID'] = sessionId;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

const DataService = {
    Init: function () {
        // Any application initialization logic comes here
    },
    GetRecommendation: async function (query) {
        console.log(BASE_API_URL);
        try {
            const response = await api.post(`${BASE_API_URL}/recommend`, { query });
            console.log(response.data)
            return response.data;
        } catch (error) {
            console.error('Error fetching recommendation:', error);
            throw error;
        }
    },
};

export default DataService;