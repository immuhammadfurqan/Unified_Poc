window.Layout = ({ children, activeTab, setActiveTab, onLogout }) => {
    const items = [
        { id: 'dashboard', label: 'Dashboard', icon: 'layout-grid' },
        { id: 'github', label: 'GitHub', icon: 'github' },
        { id: 'trello', label: 'Trello', icon: 'trello' },
        { id: 'figma', label: 'Figma', icon: 'figma' },
        { id: 'ai', label: 'AI Assistant', icon: 'sparkles' },
    ];

    React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); }, [activeTab]);

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            <aside className="w-64 bg-slate-900 text-white flex flex-col shadow-2xl z-20">
                <div className="p-8"><div className="flex items-center gap-3"><div className="bg-blue-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/20"><i data-lucide="zap" className="w-6 h-6"></i></div><h1 className="text-xl font-bold tracking-tight">Unified POC</h1></div></div>
                <nav className="flex-1 px-4 py-6 space-y-2">
                    {items.map(item => (
                        <button key={item.id} onClick={() => setActiveTab(item.id)} className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl text-sm font-bold transition-all ${activeTab === item.id ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/20 translate-x-1' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}>
                            <i data-lucide={item.icon} className="w-5 h-5"></i>{item.label}
                        </button>
                    ))}
                </nav>
                <div className="p-6 border-t border-slate-800"><button onClick={onLogout} className="w-full flex items-center gap-4 px-5 py-4 rounded-2xl text-sm font-bold text-slate-500 hover:bg-red-500/10 hover:text-red-400 transition-all"><i data-lucide="log-out" className="w-5 h-5"></i>Logout</button></div>
            </aside>
            <main className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-100 flex items-center justify-between px-10 z-10 sticky top-0">
                    <h2 className="text-xl font-bold text-slate-800 capitalize">{activeTab === 'ai' ? 'Intelligent Assistant' : activeTab}</h2>
                    <div className="flex items-center gap-3"><span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse"></span><span className="text-sm font-bold text-slate-500">System Ready</span></div>
                </header>
                <div className="flex-1 overflow-y-auto p-10 bg-slate-50/30 scroll-smooth">
                    <div className="max-w-6xl mx-auto">{children}</div>
                </div>
            </main>
        </div>
    );
};
