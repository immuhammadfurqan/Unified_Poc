window.UIAtoms = {
    Spinner: () => (
        <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        </div>
    ),

    Alert: ({ msg }) => {
        if (!msg?.text) return null;
        const styles = {
            error: "bg-red-50 border-red-100 text-red-700",
            success: "bg-green-50 border-green-100 text-green-700",
            info: "bg-blue-50 border-blue-100 text-blue-700"
        };
        const icons = { error: "alert-circle", success: "check-circle", info: "info" };
        
        return (
            <div className={`p-4 rounded-xl border ${styles[msg.type || 'info']} animate-in slide-in-from-top-2 duration-300 mb-6`}>
                <div className="flex items-center gap-3">
                    <i data-lucide={icons[msg.type || 'info']} className="w-5 h-5"></i>
                    <p className="font-medium text-sm">{msg.text}</p>
                </div>
            </div>
        );
    },

    SectionCard: ({ title, icon, children, headerAction, footer }) => (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden h-full">
            <div className="p-6 border-b border-slate-50 flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    {icon && <i data-lucide={icon} className="w-5 h-5 text-blue-600"></i>}
                    {title}
                </h3>
                {headerAction}
            </div>
            <div className="p-6">{children}</div>
            {footer && <div className="p-4 bg-slate-50 border-t border-slate-100">{footer}</div>}
        </div>
    ),

    ConnectionHeader: ({ title, desc, icon, iconColor, status, onAction, actionLabel, actionIcon, secondaryContent }) => (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 mb-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                    <div className={`p-4 rounded-2xl ${iconColor || 'bg-slate-900 text-white'}`}>
                        <i data-lucide={icon} className="w-8 h-8"></i>
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-slate-900">{title}</h3>
                        {status ? (
                            <div className="flex items-center gap-2 mt-1">
                                <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
                                <p className="text-sm font-medium text-slate-600">{status}</p>
                            </div>
                        ) : (
                            <p className="text-sm text-slate-500 mt-1">{desc}</p>
                        )}
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    {secondaryContent}
                    {onAction && (
                        <button onClick={onAction} className="bg-slate-900 text-white px-6 py-2.5 rounded-xl hover:bg-slate-800 font-bold transition-all flex items-center gap-2">
                            {actionIcon && <i data-lucide={actionIcon} className="w-4 h-4"></i>}
                            {actionLabel}
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
};
