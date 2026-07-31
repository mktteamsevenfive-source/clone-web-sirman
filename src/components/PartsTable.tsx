'use client';

import React, { useState, useEffect, useRef } from 'react';
import { PartData } from '@/lib/data';
import { Search, ShoppingCart, CheckCircle2, Loader2, Star, Target, Check } from 'lucide-react';

interface PartsTableProps {
    parts: PartData[];
    loading?: boolean;
    selectedRef?: string | null;
    onSelectPartRef?: (ref: string) => void;
    cartCountMap?: Record<string, number>;
    onAddToCart?: (part: PartData) => void;
}

export const PartsTable: React.FC<PartsTableProps> = ({
    parts,
    loading = false,
    selectedRef,
    onSelectPartRef,
    cartCountMap = {},
    onAddToCart,
}) => {
    const [query, setQuery] = useState('');
    const [onlySuggested, setOnlySuggested] = useState(false);
    const itemRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

    const filteredParts = parts.filter((p) => {
        const matchesQuery =
            !query ||
            (p.code && p.code.toLowerCase().includes(query.toLowerCase())) ||
            (p.name && p.name.toLowerCase().includes(query.toLowerCase())) ||
            (p.ref && p.ref.toLowerCase().includes(query.toLowerCase()));

        const matchesSuggested = !onlySuggested || p.suggested;

        return matchesQuery && matchesSuggested;
    });

    const suggestedCount = parts.filter((p) => p.suggested).length;

    // Helper to check normalized ref equality
    const isRefEqual = (ref1?: string | null, ref2?: string | null) => {
        if (!ref1 || !ref2) return false;
        const norm1 = ref1.trim().toUpperCase().replace(/^0+/, '');
        const norm2 = ref2.trim().toUpperCase().replace(/^0+/, '');
        if (norm1 === norm2) return true;

        const hasLetter1 = /[A-Z]$/.test(norm1);
        const hasLetter2 = /[A-Z]$/.test(norm2);
        if (hasLetter1 && hasLetter2) return false;

        const base1 = norm1.replace(/[A-Z]$/, '');
        const base2 = norm2.replace(/[A-Z]$/, '');
        return base1 === base2;
    };

    // Auto-scroll to selected ref
    useEffect(() => {
        if (!selectedRef) return;
        const normSelected = selectedRef.replace(/^0+/, '');
        const targetElement = itemRefs.current[normSelected];
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, [selectedRef]);

    return (
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full">
            {/* Header & Part Search Input + Suggested Filter Checkbox */}
            <div className="p-4 bg-slate-50/80 border-b border-slate-200/80">
                <div className="flex items-center justify-between mb-3 gap-2">
                    <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2 flex-wrap">
                        Spare Parts List ({parts.length})
                        {selectedRef && (
                            <span className="inline-flex items-center gap-1 bg-red-100 text-[#C8102E] text-[11px] font-bold px-2.5 py-0.5 rounded-full border border-red-200 animate-pulse">
                                <Target className="w-3 h-3" /> Selected Ref #{selectedRef}
                            </span>
                        )}
                    </h3>

                    {/* Suggested Checkbox Filter */}
                    <label className="flex items-center gap-1.5 text-xs font-bold text-slate-700 cursor-pointer select-none bg-white border border-slate-200/80 px-2.5 py-1 rounded-xl hover:border-slate-300 transition-all shadow-2xs">
                        <input
                            type="checkbox"
                            checked={onlySuggested}
                            onChange={(e) => setOnlySuggested(e.target.checked)}
                            className="rounded text-[#C8102E] focus:ring-[#C8102E] w-3.5 h-3.5 cursor-pointer"
                        />
                        <span className="flex items-center gap-1">
                            <Star className={`w-3.5 h-3.5 ${onlySuggested ? 'fill-amber-400 text-amber-500' : 'text-slate-400'}`} />
                            Suggested {suggestedCount > 0 && `(${suggestedCount})`}
                        </span>
                    </label>
                </div>

                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Filter by part code, name, or Ref #..."
                        className="w-full bg-white text-slate-900 text-xs rounded-xl pl-9 pr-3 py-2 border border-slate-200/80 focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20 focus:border-[#C8102E] transition-all shadow-inner"
                    />
                </div>
            </div>

            {/* Spare Parts List */}
            <div className="flex-1 overflow-y-auto max-h-[500px] divide-y divide-slate-100">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                        <Loader2 className="w-7 h-7 text-[#C8102E] animate-spin mb-2" />
                        <span className="text-xs font-semibold">Loading real spare parts...</span>
                    </div>
                ) : filteredParts.length === 0 ? (
                    <div className="text-center py-12 text-slate-400 text-xs font-medium">
                        {onlySuggested
                            ? 'No suggested spare parts found for this filter.'
                            : 'No spare parts found for this model.'}
                    </div>
                ) : (
                    filteredParts.map((part, idx) => {
                        const normRef = part.ref ? part.ref.replace(/^0+/, '') : '';
                        const isSelected = isRefEqual(part.ref, selectedRef);
                        const countInCart = cartCountMap[part.code] || 0;

                        return (
                            <div
                                key={part.id || part.code || idx}
                                ref={(el) => {
                                    if (normRef) itemRefs.current[normRef] = el;
                                }}
                                onClick={() => {
                                    if (part.ref && onSelectPartRef) {
                                        onSelectPartRef(part.ref);
                                    }
                                }}
                                className={`p-3.5 transition-all flex items-center justify-between gap-3 text-xs cursor-pointer border-l-4 ${
                                    isSelected
                                        ? 'bg-red-50/90 border-l-[#C8102E] ring-1 ring-red-200 shadow-sm'
                                        : 'bg-white hover:bg-slate-50 border-l-transparent'
                                }`}
                            >
                                <div className="space-y-0.5 min-w-0 flex-1">
                                    <div className="font-mono font-bold text-slate-900 flex items-center gap-1.5 flex-wrap">
                                        {part.ref && (
                                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                                isSelected
                                                    ? 'bg-[#C8102E] text-white shadow-xs'
                                                    : 'bg-slate-100 text-slate-600'
                                            }`}>
                                                Ref #{part.ref}
                                            </span>
                                        )}
                                        <span className="text-[#C8102E] flex items-center gap-1 font-bold">
                                            {part.code}
                                            {part.suggested && (
                                                <span className="text-amber-500 font-bold" title="Suggested Spare Part">
                                                    ★
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                    <div className={`font-semibold truncate ${isSelected ? 'text-[#C8102E]' : 'text-slate-700'}`}>
                                        {part.name}
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] text-slate-400">
                                        <span className="flex items-center gap-1 text-emerald-600 font-bold">
                                            <CheckCircle2 className="w-3 h-3" /> In Stock ({part.stock || 10})
                                        </span>
                                    </div>
                                </div>

                                {/* Price & Add Action */}
                                <div className="text-right flex-shrink-0 space-y-1.5">
                                    <div className="font-extrabold text-slate-900 text-xs">
                                        €{(part.price || 14.5).toFixed(2)}
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (onAddToCart) onAddToCart(part);
                                        }}
                                        className={`inline-flex items-center gap-1.5 text-[10px] font-extrabold px-3 py-1.5 rounded-xl transition-all shadow-2xs active:scale-95 cursor-pointer ${
                                            countInCart > 0
                                                ? 'bg-emerald-600 hover:bg-emerald-700 text-white ring-2 ring-emerald-200'
                                                : 'bg-[#C8102E] hover:bg-[#A00C24] text-white'
                                        }`}
                                    >
                                        {countInCart > 0 ? (
                                            <>
                                                <Check className="w-3 h-3 stroke-[3]" />
                                                Added ({countInCart})
                                            </>
                                        ) : (
                                            <>
                                                <ShoppingCart className="w-3 h-3" />
                                                Add
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};
