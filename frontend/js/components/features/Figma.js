window.Figma = () => {
    const [fileKey, setFileKey] = React.useState("");
    const [data, setData] = React.useState(null);
    const [token, setToken] = React.useState("");
    const [msg, setMsg] = React.useState({ text: "", type: "" });
    const [loading, setLoading] = React.useState(false);

    const handleAnalyze = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await window.apiClient.get(`/figma/analyze/${fileKey}`);
            setData(res.data);
            setMsg({ text: "Analysis complete", type: "success" });
        } catch (err) { setMsg({ text: "Analysis failed", type: "error" }); }
        finally { setLoading(false); }
    };

    const handleSaveToken = async () => {
        if (!token) return;
        try {
            await window.apiClient.post('/integrations/token', { provider: "figma", token });
            setMsg({ text: "Figma token saved", type: "success" });
            setToken("");
        } catch (e) { setMsg({ text: "Failed to save token", type: "error" }); }
    };

    return (
        <div className="animate-in fade-in">
            <window.UIAtoms.ConnectionHeader 
                title="Figma Analysis" desc="Extract frame metadata from design files" icon="figma" iconColor="bg-purple-600 text-white"
                secondaryContent={<input className="bg-slate-50 border p-2.5 rounded-xl text-sm outline-none w-48 focus:ring-2 focus:ring-purple-500" placeholder="Set API Token" value={token} onChange={e => setToken(e.target.value)} />}
                onAction={handleSaveToken} actionLabel="Update"
            />
            
            <window.UIAtoms.Alert msg={msg} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <window.UIAtoms.SectionCard title="Analyze File" icon="search">
                    <form onSubmit={handleAnalyze} className="space-y-4">
                        <input className="w-full bg-slate-50 border p-4 rounded-xl outline-none focus:ring-2 focus:ring-purple-500" placeholder="Figma File Key" value={fileKey} onChange={e => setFileKey(e.target.value)} required />
                        <button disabled={loading} className="w-full bg-purple-600 text-white py-4 rounded-xl font-bold shadow-lg shadow-purple-100 flex items-center justify-center gap-2">
                            {loading ? "Analyzing..." : <><i data-lucide="layers" className="w-5 h-5"></i> Analyze Layers</>}
                        </button>
                    </form>
                </window.UIAtoms.SectionCard>
                <div className="lg:col-span-2">
                    {data ? (
                        <window.UIAtoms.SectionCard title={data.file_name} headerAction={<span className="text-[10px] bg-green-100 text-green-700 px-2 py-1 rounded font-bold uppercase">{data.raw_data_summary}</span>}>
                            <div className="bg-slate-900 -mx-6 -my-6 p-6 overflow-auto max-h-[500px]">
                                <pre className="text-xs text-blue-300 font-mono leading-relaxed">{JSON.stringify(data.frames, null, 2)}</pre>
                            </div>
                        </window.UIAtoms.SectionCard>
                    ) : <div className="h-full bg-white rounded-2xl border-2 border-dashed border-slate-100 flex flex-col items-center justify-center p-12 text-slate-300"><i data-lucide="image" className="w-16 h-16 opacity-10 mb-4"></i><p className="font-medium">No results to display</p></div>}
                </div>
            </div>
        </div>
    );
};
