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
            const response = await api.post(`/recommend`, { query });
            console.log(response.data)
            return response.data;
        } catch (error) {
            console.error('Error fetching recommendation:', error);
            throw error;
        }
    },
    UploadFiles: async function (pdfFile, csvFile, projectId, locationId, endpointId) {
        const formData = new FormData();
        formData.append("pdf_file", pdfFile);
        formData.append("csv_file", csvFile);
        formData.append("project_id", projectId);
        formData.append("location_id", locationId);
        formData.append("endpoint_id", endpointId);

        try {
            const response = await api.post(`/process-pdf/`, formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            return response.data;
        } catch (error) {
            console.log(error)
            console.error("Error uploading files:", error);
            throw error;
        }
    },
    GetGrade: async function () {
        try {
            const response = await api.post(`/get-grade/`);
            return response.data;
        } catch (error) {
            console.error("Error fetching grade");
            throw error;
        }
    },
};

export default DataService;