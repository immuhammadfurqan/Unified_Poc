window.Login = ({ onLoginSuccess }) => {
    const [isRegister, setIsRegister] = React.useState(false);
    const [email, setEmail] = React.useState("");
    const [password, setPassword] = React.useState("");
    const [error, setError] = React.useState("");
    const [loading, setLoading] = React.useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await window.apiClient.post(isRegister ? "/auth/register" : "/auth/login", { email, password });
            window.AuthService.setToken(res.data.access_token);
            onLoginSuccess(res.data.access_token);
        } catch (err) {
            setError(err.response?.data?.detail || "Authentication failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4">
            <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl border border-slate-100">
                <div className="text-center">
                    <div className="inline-flex bg-blue-600 p-4 rounded-2xl shadow-lg mb-6 text-white"><i data-lucide="zap" className="h-8 w-8"></i></div>
                    <h2 className="text-3xl font-extrabold text-slate-900">{isRegister ? "Join Unified POC" : "Welcome Back"}</h2>
                    <p className="mt-2 text-slate-500 text-sm">{isRegister ? "Start managing your multi-platform integrations" : "Sign in to manage your connected accounts"}</p>
                </div>
                
                {error && <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm border border-red-100 animate-in fade-in">{error}</div>}

                <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
                    <input type="email" required className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} />
                    <input type="password" required className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
                    <button type="submit" disabled={loading} className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-lg shadow-blue-100 disabled:opacity-70">
                        {loading ? "Processing..." : (isRegister ? "Create Account" : "Sign In")}
                    </button>
                </form>

                <div className="text-center pt-4">
                    <button onClick={() => { setIsRegister(!isRegister); setError(""); }} className="text-sm font-bold text-blue-600 hover:text-blue-500">
                        {isRegister ? "Already have an account? Sign in" : "Need an account? Sign up for free"}
                    </button>
                </div>
            </div>
        </div>
    );
};
