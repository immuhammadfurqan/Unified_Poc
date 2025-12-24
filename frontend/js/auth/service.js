// Auth Service
window.AuthService = {
    getToken: () => {
        try {
            return localStorage.getItem('token');
        } catch (e) {
            console.error("AuthService: Failed to get token", e);
            return null;
        }
    },
    setToken: (token) => {
        try {
            localStorage.setItem('token', token);
        } catch (e) {
            console.error("AuthService: Failed to set token", e);
        }
    },
    removeToken: () => {
        try {
            localStorage.removeItem('token');
        } catch (e) {
            console.error("AuthService: Failed to remove token", e);
        }
    },
    isAuthenticated: () => {
        try {
            return !!localStorage.getItem('token');
        } catch (e) {
            return false;
        }
    },
    logout: () => {
        try {
            localStorage.removeItem('token');
            window.location.reload();
        } catch (e) {
            console.error("AuthService: Failed to logout", e);
            window.location.href = '/';
        }
    }
};
