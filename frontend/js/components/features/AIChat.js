window.AIChat = () => {
    const [messages, setMessages] = React.useState([]);
    const [input, setInput] = React.useState("");
    const [loading, setLoading] = React.useState(false);
    const scrollRef = React.useRef(null);

    React.useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, loading]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: "user", content: input };
        const newMsgs = [...messages, userMsg];
        setMessages(newMsgs);
        setInput("");
        setLoading(true);

        try {
            // Create a temporary assistant message to stream content into
            const assistantMsgId = Date.now();
            setMessages(prev => [...prev, { 
                role: "assistant", 
                content: "", 
                id: assistantMsgId,
                tools: [] // Track tool executions
            }]);

            const sanitizedMessages = newMsgs
                .filter(msg => ['user', 'assistant', 'system'].includes(msg.role))
                .map(msg => ({
                    role: msg.role,
                    content: String(msg.content ?? "")
                }));

            const response = await fetch('/api/v1/agent/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${window.AuthService.getToken()}`
                },
                body: JSON.stringify({ messages: sanitizedMessages })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // Process all complete lines
                buffer = lines.pop() || ''; 

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        
                        setMessages(prev => {
                            const currentMsgs = [...prev];
                            const msgIndex = currentMsgs.findIndex(m => m.id === assistantMsgId);
                            if (msgIndex === -1) return prev;
                            
                            const msg = { ...currentMsgs[msgIndex] };

                            if (event.type === 'content') {
                                msg.content = (msg.content || "") + event.content;
                            } else if (event.type === 'tool_start') {
                                msg.tools = [...(msg.tools || []), { 
                                    name: event.name, 
                                    status: 'running', 
                                    args: event.args 
                                }];
                            } else if (event.type === 'tool_result') {
                                const tools = [...(msg.tools || [])];
                                const toolIdx = tools.findLastIndex(t => t.name === event.name && t.status === 'running');
                                if (toolIdx !== -1) {
                                    tools[toolIdx] = { ...tools[toolIdx], status: 'completed', result: event.result };
                                }
                                msg.tools = tools;
                            }
                            
                            currentMsgs[msgIndex] = msg;
                            return currentMsgs;
                        });
                    } catch (e) {
                        console.error("Error parsing stream line:", line, e);
                    }
                }
            }

        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: "assistant", content: "Error: " + err.message }]);
        } finally {
            setLoading(false);
        }
    };

    const renderToolArgs = (tool) => {
        if (!tool?.args) return null;
        if (tool.name === 'run_terminal_command') {
            return (
                <div className="font-mono text-xs text-gray-500 truncate pl-5">
                    $ {tool.args.command}
                </div>
            );
        }
        if (tool.name === 'write_sandbox_file') {
            return (
                <div className="font-mono text-xs text-gray-500 pl-5">
                    {tool.args.path}
                </div>
            );
        }
        if (tool.name === 'read_sandbox_file') {
            return (
                <div className="font-mono text-xs text-gray-500 pl-5">
                    {tool.args.path}
                </div>
            );
        }
        if (tool.name === 'list_sandbox_files') {
            return (
                <div className="font-mono text-xs text-gray-500 pl-5">
                    {tool.args.path || '/app'}
                </div>
            );
        }
        return null;
    };

    const renderToolResult = (tool) => {
        if (tool?.status !== 'completed') return null;
        if (tool.result == null) return null;

        if (tool.name === 'setup_dev_environment') {
            const hostPort = tool.result.host_port;
            return (
                <div className="text-xs text-gray-600 pl-5">
                    {hostPort ? `App port: http://localhost:${hostPort}` : 'App port not exposed yet'}
                </div>
            );
        }

        if (tool.name === 'run_terminal_command') {
            return (
                <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-gray-700 bg-gray-100 border border-gray-200 rounded p-2">
                    {tool.result.output || ''}
                </pre>
            );
        }

        if (tool.name === 'write_sandbox_file') {
            const content = tool.args?.content;
            if (!content) return null;
            return (
                <details className="mt-2 pl-5">
                    <summary className="text-xs text-gray-600 cursor-pointer">View file content</summary>
                    <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-gray-700 bg-gray-100 border border-gray-200 rounded p-2">
                        {content}
                    </pre>
                </details>
            );
        }

        if (tool.name === 'read_sandbox_file') {
            return (
                <pre className="mt-2 whitespace-pre-wrap font-mono text-xs text-gray-700 bg-gray-100 border border-gray-200 rounded p-2">
                    {tool.result}
                </pre>
            );
        }

        if (tool.name === 'list_sandbox_files') {
            const files = Array.isArray(tool.result.files) ? tool.result.files : [];
            return (
                <div className="mt-2 pl-5">
                    <div className="text-xs text-gray-600">Files: {files.length}</div>
                    {files.length > 0 && (
                        <pre className="mt-1 whitespace-pre-wrap font-mono text-xs text-gray-700 bg-gray-100 border border-gray-200 rounded p-2">
                            {files.join('\n')}
                        </pre>
                    )}
                </div>
            );
        }

        return null;
    };

    return (
        <div className="h-full flex flex-col bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                    <i data-lucide="bot" className="w-5 h-5 text-indigo-600"></i>
                    AI Developer
                </h2>
                <span className="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full font-medium">GPT-5</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50" ref={scrollRef}>
                {messages.length === 0 && (
                    <div className="text-center py-10 text-gray-400">
                        <i data-lucide="code-2" className="w-12 h-12 mx-auto mb-3 opacity-50"></i>
                        <p>Ask me to create an app, write a script, or manage your repo.</p>
                    </div>
                )}
                
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-lg p-4 shadow-sm ${
                            msg.role === 'user' 
                                ? 'bg-indigo-600 text-white' 
                                : 'bg-white border border-gray-200 text-gray-800'
                        }`}>
                            {/* Render Tool Executions */}
                            {msg.tools && msg.tools.length > 0 && (
                                <div className="mb-3 space-y-2">
                                    {msg.tools.map((tool, idx) => (
                                        <div key={idx} className="text-sm bg-gray-50 border border-gray-200 rounded p-2">
                                            <div className="flex items-center gap-2 mb-1">
                                                {tool.status === 'running' ? (
                                                    <i data-lucide="loader-2" className="w-3 h-3 animate-spin text-blue-500"></i>
                                                ) : (
                                                    <i data-lucide="check-circle" className="w-3 h-3 text-green-500"></i>
                                                )}
                                                <span className="font-mono text-xs font-semibold text-gray-700">{tool.name}</span>
                                            </div>
                                            {renderToolArgs(tool)}
                                            {renderToolResult(tool)}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Render Content */}
                            <div className="whitespace-pre-wrap leading-relaxed text-sm">
                                {msg.content}
                            </div>
                        </div>
                    </div>
                ))}
                
                {loading && !messages[messages.length - 1]?.id && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                            <i data-lucide="loader" className="w-5 h-5 animate-spin text-indigo-600"></i>
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSend} className="p-4 bg-white border-t border-gray-200">
                <div className="relative">
                    <input
                        type="text"
                        className="w-full pl-4 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                        placeholder="Build a React app..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button 
                        type="submit" 
                        disabled={loading || !input.trim()}
                        className="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <i data-lucide="send" className="w-5 h-5"></i>
                    </button>
                </div>
            </form>
        </div>
    );
}
