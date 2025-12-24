window.Trello = () => {
    const [boards, setBoards] = React.useState([]);
    const [selectedBoard, setSelectedBoard] = React.useState(null);
    const [lists, setLists] = React.useState([]);
    const [cardName, setCardName] = React.useState("");
    const [selectedListId, setSelectedListId] = React.useState("");
    const [manualToken, setManualToken] = React.useState("");
    const [msg, setMsg] = React.useState({ text: "", type: "" });
    const [loading, setLoading] = React.useState(false);

    const fetchBoards = async () => {
        try {
            const res = await window.apiClient.get('/trello/boards');
            setBoards(res.data);
        } catch (e) {}
    };

    React.useEffect(() => { fetchBoards(); }, []);

    const handleSaveToken = async () => {
        if (!manualToken) return;
        try {
            await window.apiClient.post('/integrations/token', { provider: "trello", token: manualToken });
            setMsg({ text: "Trello token updated", type: "success" });
            setManualToken("");
            fetchBoards();
        } catch (e) { setMsg({ text: "Failed to save token", type: "error" }); }
    };

    const handleFetchLists = async (id) => {
        setLoading(true);
        try {
            const res = await window.apiClient.get(`/trello/boards/${id}/lists`);
            setLists(res.data);
            setSelectedBoard(id);
            if (res.data.length > 0) setSelectedListId(res.data[0].id);
        } catch (e) { setMsg({ text: "Failed to load lists", type: "error" }); }
        finally { setLoading(false); }
    };

    const handleCreateCard = async (e) => {
        e.preventDefault();
        try {
            await window.apiClient.post('/trello/cards', { list_id: selectedListId, name: cardName });
            setMsg({ text: "Card added successfully!", type: "success" });
            setCardName("");
        } catch (e) { setMsg({ text: "Failed to create card", type: "error" }); }
    };

    return (
        <div className="animate-in fade-in">
            <window.UIAtoms.ConnectionHeader 
                title="Trello Integration" desc="Manage your project boards and cards" icon="trello" iconColor="bg-blue-500 text-white"
                secondaryContent={<input className="bg-slate-50 border p-2.5 rounded-xl text-sm outline-none w-48 focus:ring-2 focus:ring-blue-500" placeholder="Update Token" value={manualToken} onChange={e => setManualToken(e.target.value)} />}
                onAction={handleSaveToken} actionLabel="Save"
            />
            
            <window.UIAtoms.Alert msg={msg} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <window.UIAtoms.SectionCard title="Your Boards" icon="layout" headerAction={<button onClick={fetchBoards} className="text-blue-600 font-bold text-xs hover:underline">Refresh</button>}>
                    <div className="divide-y divide-slate-50 -mx-6 -my-6 max-h-[400px] overflow-y-auto">
                        {boards.length === 0 ? <div className="p-12 text-center text-slate-400 italic">Connect Trello to see boards</div> : boards.map(b => (
                            <div key={b.id} className={`p-4 px-6 flex justify-between items-center transition-colors ${selectedBoard === b.id ? 'bg-blue-50' : 'hover:bg-slate-50'}`}>
                                <span className="font-bold text-slate-900">{b.name}</span>
                                <button onClick={() => handleFetchLists(b.id)} className={`px-4 py-1.5 rounded-lg text-sm font-bold transition-all ${selectedBoard === b.id ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                                    {selectedBoard === b.id ? 'Selected' : 'Select'}
                                </button>
                            </div>
                        ))}
                    </div>
                </window.UIAtoms.SectionCard>

                <window.UIAtoms.SectionCard title="Quick Card" icon="plus-square">
                    {!selectedBoard ? (
                        <div className="p-12 text-center text-slate-300"><i data-lucide="arrow-left" className="w-12 h-12 mx-auto mb-4 opacity-20"></i><p>Select a board to create cards</p></div>
                    ) : loading ? <window.UIAtoms.Spinner /> : (
                        <form onSubmit={handleCreateCard} className="space-y-6">
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase mb-2 tracking-widest">Target List</label>
                                <select className="w-full bg-slate-50 border p-4 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" value={selectedListId} onChange={e => setSelectedListId(e.target.value)}>
                                    {lists.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase mb-2 tracking-widest">Card Title</label>
                                <input className="w-full bg-slate-50 border p-4 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" placeholder="Task description" value={cardName} onChange={e => setCardName(e.target.value)} required />
                            </div>
                            <button className="w-full bg-blue-600 text-white py-4 rounded-xl font-bold shadow-lg shadow-blue-100 flex items-center justify-center gap-2"><i data-lucide="check" className="w-5 h-5"></i> Create Card</button>
                        </form>
                    )}
                </window.UIAtoms.SectionCard>
            </div>
        </div>
    );
};
