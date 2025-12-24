// API Client Setup
const API_URL = "/api/v1";

window.apiClient = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' }
});

// Request Interceptor
window.apiClient.interceptors.request.use(
    (config) => {
        // Safe access to AuthService
        if (window.AuthService) {
            const token = window.AuthService.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response Interceptor
window.apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            if (window.AuthService) {
                window.AuthService.removeToken();
            }
            window.location.reload();
        }
        return Promise.reject(error);
    }
);
