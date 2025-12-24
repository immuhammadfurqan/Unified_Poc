window.GitHub = () => {
    const [repos, setRepos] = React.useState([]);
    const [repoName, setRepoName] = React.useState("");
    const [isPrivate, setIsPrivate] = React.useState(false);
    const [status, setStatus] = React.useState({ connected: false, username: null, loading: true });
    const [msg, setMsg] = React.useState({ text: "", type: "" });
    const [actionLoading, setActionLoading] = React.useState(false);

    const checkStatus = async () => {
        try {
            const res = await window.apiClient.get('/github/status');
            setStatus({ ...res.data, loading: false });
            if (res.data.connected) {
                const r = await window.apiClient.get('/github/repos');
                setRepos(r.data);
            }
        } catch (e) { setStatus({ connected: false, loading: false }); }
    };

    const handleCallback = async (code, state) => {
        setMsg({ text: "Completing GitHub connection...", type: "info" });
        try {
            await window.apiClient.post('/github/callback', { code, state });
            setMsg({ text: "GitHub connected successfully!", type: "success" });
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
            checkStatus();
        } catch (err) {
            setMsg({ text: "Failed to complete connection: " + (err.response?.data?.detail || err.message), type: "error" });
        }
    };

    React.useEffect(() => { 
        checkStatus(); 

        const urlParams = new URLSearchParams(window.location.search);
        const callback = urlParams.get('callback');
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (callback === 'github' && code && state) {
            handleCallback(code, state);
        }
    }, []);

    const handleConnect = async () => {
        try {
            const res = await window.apiClient.get('/github/connect');
            window.location.href = res.data.authorization_url;
        } catch (e) { setMsg({ text: "Failed to initiate connection", type: "error" }); }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            await window.apiClient.post('/github/repos', { name: repoName, private: isPrivate });
            setMsg({ text: `Successfully created ${isPrivate ? 'private' : 'public'} repository: ${repoName}`, type: "success" });
            setRepoName("");
            checkStatus();
        } catch (err) { setMsg({ text: err.response?.data?.detail || "Creation failed", type: "error" }); }
        finally { setActionLoading(false); }
    };

    if (status.loading) return <window.UIAtoms.Spinner />;

    return (
        <div className="animate-in fade-in">
            <window.UIAtoms.ConnectionHeader 
                title="GitHub Integration" desc="Connect to manage your repositories" icon="github" 
                status={status.connected ? `Connected as @${status.username}` : null}
                onAction={!status.connected ? handleConnect : null} actionLabel="Connect Account" actionIcon="external-link"
            />
            
            <window.UIAtoms.Alert msg={msg} />

            {status.connected && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <window.UIAtoms.SectionCard title="New Repository" icon="plus-circle">
                        <form onSubmit={handleCreate} className="space-y-4">
                            <input className="w-full bg-slate-50 border p-4 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" placeholder="Repository Name" value={repoName} onChange={e => setRepoName(e.target.value)} required />
                            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl cursor-pointer" onClick={() => setIsPrivate(!isPrivate)}>
                                <input type="checkbox" checked={isPrivate} onChange={() => {}} className="w-5 h-5 rounded text-blue-600" />
                                <span className="text-sm font-bold">Private Repository</span>
                            </div>
                            <button disabled={actionLoading} className="w-full bg-blue-600 text-white py-4 rounded-xl font-bold shadow-lg shadow-blue-100 disabled:opacity-50">
                                {actionLoading ? "Creating..." : "Create Repository"}
                            </button>
                        </form>
                    </window.UIAtoms.SectionCard>
                    <div className="lg:col-span-2">
                        <window.UIAtoms.SectionCard title="Your Repositories" icon="list" headerAction={<button onClick={checkStatus} className="p-2 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-blue-600"><i data-lucide="refresh-cw" className="w-5 h-5"></i></button>}>
                            <div className="divide-y divide-slate-50 -mx-6 -my-6 max-h-[500px] overflow-y-auto">
                                {repos.length === 0 ? <div className="p-12 text-center text-slate-400 italic">No repositories found</div> : repos.map(r => (
                                    <div key={r.id} className="p-4 px-6 flex justify-between items-center hover:bg-slate-50 group">
                                        <div className="flex items-center gap-4">
                                            <div className="p-2.5 bg-blue-50 rounded-xl"><i data-lucide={r.private ? "lock" : "globe"} className="w-4 h-4 text-blue-600"></i></div>
                                            <span className="font-bold text-slate-900">{r.name}</span>
                                        </div>
                                        <a href={r.html_url} target="_blank" className="p-2 text-slate-300 hover:text-blue-600 hover:bg-blue-50 rounded-lg"><i data-lucide="external-link" className="w-4 h-4"></i></a>
                                    </div>
                                ))}
                            </div>
                        </window.UIAtoms.SectionCard>
                    </div>
                </div>
            )}
        </div>
    );
};
