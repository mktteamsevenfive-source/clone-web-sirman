'use client';

import React, { useState } from 'react';
import { Part, UserRole } from '@/lib/types';
import { Search, ShoppingCart, Lock } from 'lucide-react';

interface PartsTableProps {
    parts: Part[];
    userRole?: UserRole;
    onLoginPrompt?: () => void;
}

export const PartsTable: React.FC<PartsTableProps> = ({ parts, userRole = 'guest', onLoginPrompt }) => {
    const [query, setQuery] = useState('');

    const filteredParts = parts.filter(pt =>
        pt.code.toLowerCase().includes(query.toLowerCase()) ||
        pt.name.toLowerCase().includes(query.toLowerCase()) ||
        (pt.ref && pt.ref.toLowerCase().includes(query.toLowerCase()))
    );

    const isPrivileged = userRole === 'technician' || userRole === 'dealer' || userRole === 'admin';

    return (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
            {/* Header & Filter */}
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between gap-3">
                <div>
                    <h3 className="font-bold text-slate-800 text-sm">Spare Parts List</h3>
                    <p className="text-xs text-slate-500">{filteredParts.length} of {parts.length} items</p>
                </div>
                <div className="relative w-48">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Filter parts..."
                        className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C8102E]"
                    />
                </div>
            </div>

            {/* Parts List */}
            <div className="divide-y divide-slate-100 overflow-y-auto max-h-[500px]">
                {filteredParts.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 text-xs">
                        No spare parts match filter.
                    </div>
                ) : (
                    filteredParts.map((pt, idx) => (
                        <div key={idx} className="p-3.5 hover:bg-slate-50 transition-colors flex flex-col gap-1.5">
                            <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2">
                                    {pt.ref && (
                                        <span className="bg-[#0284C7] text-white text-[10px] font-extrabold px-1.5 py-0.5 rounded">
                                            REF {pt.ref}
                                        </span>
                                    )}
                                    <span className="font-bold text-slate-900 text-xs font-mono">{pt.code}</span>
                                </div>

                                {/* Price / Role protection */}
                                {isPrivileged ? (
                                    <span className="text-xs font-bold text-emerald-600">
                                        € {pt.price ? pt.price.toFixed(2) : '0.00'}
                                    </span>
                                ) : (
                                    <button
                                        onClick={onLoginPrompt}
                                        className="flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200"
                                        title="Sign in to view price"
                                    >
                                        <Lock className="w-3 h-3" />
                                        Sign in for price
                                    </button>
                                )}
                            </div>

                            <p className="text-xs text-slate-600 font-medium leading-relaxed">{pt.name}</p>

                            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                                <span>
                                    {pt.stock > 0 ? (
                                        <span className="text-emerald-600 font-semibold">In Stock ({pt.stock})</span>
                                    ) : (
                                        <span className="text-slate-400">Available on request</span>
                                    )}
                                </span>
                                {pt.view_name && (
                                    <span className="text-[10px] text-slate-400 truncate max-w-[120px]">
                                        {pt.view_name}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
