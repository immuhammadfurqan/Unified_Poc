window.Dashboard = ({ setActiveTab }) => {
    const [stats, setStats] = React.useState({ 
        github: { connected: false, repos: 0 }, 
        trello: { connected: false, boards: 0 }, 
        figma: { connected: false } 
    });
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchStats = async () => {
            try {
                const [ghStatus, ghRepos] = await Promise.all([
                    window.apiClient.get('/github/status'),
                    window.apiClient.get('/github/repos').catch(() => ({ data: [] }))
                ]);
                
                let trelloConnected = false, trelloBoards = 0;
                try {
                    const b = await window.apiClient.get('/trello/boards');
                    trelloBoards = b.data.length;
                    trelloConnected = true;
                } catch (e) {}

                setStats({
                    github: { connected: ghStatus.data.connected, repos: ghRepos.data.length },
                    trello: { connected: trelloConnected, boards: trelloBoards },
                    figma: { connected: false }
                });
            } catch (e) {
                console.error("Dashboard error", e);
            } finally { 
                setLoading(false); 
            }
        };
        fetchStats();
    }, []);

    if (loading) return <window.UIAtoms.Spinner />;

    const tools = [
        { id: 'github', title: 'GitHub', icon: 'github', color: 'bg-slate-900', connected: stats.github.connected, info: stats.github.connected ? `${stats.github.repos} Repositories` : 'Click to connect' },
        { id: 'trello', title: 'Trello', icon: 'trello', color: 'bg-blue-500', connected: stats.trello.connected, info: stats.trello.connected ? `${stats.trello.boards} Boards` : 'Click to connect' },
        { id: 'figma', title: 'Figma', icon: 'figma', color: 'bg-purple-600', connected: false, info: 'Token required' }
    ];

    return (
        <div className="space-y-10 animate-in fade-in duration-500">
            <div>
                <h1 className="text-3xl font-extrabold text-slate-900">Dashboard Overview</h1>
                <p className="text-slate-500 mt-2">Everything at a glance.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {tools.map(tool => (
                    <div key={tool.id} onClick={() => setActiveTab(tool.id)} className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer group">
                        <div className="flex justify-between items-start mb-8">
                            <div className={`${tool.color} text-white p-4 rounded-2xl shadow-lg group-hover:scale-110 transition-transform`}><i data-lucide={tool.icon} className="w-8 h-8"></i></div>
                            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${tool.connected ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                                {tool.connected ? 'Active' : 'Setup'}
                            </span>
                        </div>
                        <h3 className="text-2xl font-bold text-slate-900">{tool.title}</h3>
                        <p className="text-slate-500 mt-1 font-medium">{tool.info}</p>
                        <div className="mt-8 flex items-center gap-2 text-blue-600 font-bold text-sm">Manage <i data-lucide="arrow-right" className="w-4 h-4"></i></div>
                    </div>
                ))}
            </div>
        </div>
    );
};
