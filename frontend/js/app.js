function App() {
    const [token, setToken] = React.useState(null);
    const [isLoading, setIsLoading] = React.useState(true);
    const [activeTab, setActiveTab] = React.useState('dashboard');

    // Initial load
    React.useEffect(() => {
        // Simple delay to ensure all components are loaded
        const timer = setTimeout(() => {
            const storedToken = window.AuthService ? window.AuthService.getToken() : null;
            if (storedToken) {
                setToken(storedToken);
            }
            setIsLoading(false);

            // Handle OAuth callbacks
            const urlParams = new URLSearchParams(window.location.search);
            const callback = urlParams.get('callback');
            if (callback === 'github') setActiveTab('github');
            else if (callback === 'trello') setActiveTab('trello');

            if (window.lucide) window.lucide.createIcons();
        }, 200);
        
        return () => clearTimeout(timer);
    }, []);

    // Update icons when tab changes
    React.useEffect(() => {
        if (window.lucide) window.lucide.createIcons();
    }, [activeTab]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                    <p className="text-gray-500 text-sm">Loading...</p>
                </div>
            </div>
        );
    }

    if (!token) return <window.Login onLoginSuccess={(t) => setToken(t)} />;

    const renderContent = () => {
        switch (activeTab) {
            case 'dashboard': return <window.Dashboard setActiveTab={setActiveTab} />;
            case 'github': return <window.GitHub />;
            case 'trello': return <window.Trello />;
            case 'figma': return <window.Figma />;
            case 'ai': return <window.AIChat />;
            default: return <window.Dashboard setActiveTab={setActiveTab} />;
        }
    };

    return (
        <window.Layout 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            onLogout={() => { 
                window.AuthService.removeToken(); 
                setToken(null); 
            }}
        >
            {renderContent()}
        </window.Layout>
    );
}

// Initialize when ready
function initApp() {
    try {
        const rootElement = document.getElementById('root');
        if (!rootElement) {
            console.error("Root element not found!");
            return;
        }
        
        const root = ReactDOM.createRoot(rootElement);
        root.render(<App />);
        console.log("App initialized successfully");
    } catch (error) {
        console.error("Failed to initialize app:", error);
    }
}

// Wait for Babel to process all scripts
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initApp, 300));
} else {
    setTimeout(initApp, 300);
}
