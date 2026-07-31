'use client';

import React from 'react';
import { CategoryData } from '@/lib/data';
import { Layers, Filter, Check } from 'lucide-react';

interface SidebarProps {
    categories: CategoryData[];
    selectedCategory: CategoryData | null;
    onSelectCategory: (cat: CategoryData | null) => void;
    userCatalogToggle: boolean;
    onToggleUserCatalog: (val: boolean) => void;
    statusFilter: 'all' | 'in_production' | 'out_of_production';
    onStatusFilterChange: (val: 'all' | 'in_production' | 'out_of_production') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    categories,
    selectedCategory,
    onSelectCategory,
    userCatalogToggle,
    onToggleUserCatalog,
    statusFilter,
    onStatusFilterChange,
}) => {
    return (
        <aside className="w-full lg:w-64 flex-shrink-0 space-y-5 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-sm">
            {/* Categories Section Header */}
            <div>
                <div className="flex items-center justify-between mb-3 px-1">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-[#C8102E]" />
                        Categories
                    </h2>
                    {selectedCategory && (
                        <button
                            onClick={() => onSelectCategory(null)}
                            className="text-[11px] font-semibold text-[#C8102E] hover:underline"
                        >
                            Reset
                        </button>
                    )}
                </div>

                <ul className="space-y-1 max-h-[420px] overflow-y-auto pr-1">
                    {categories.map((cat) => {
                        const isSelected = selectedCategory?.id === cat.id;
                        return (
                            <li key={cat.id}>
                                <button
                                    onClick={() => onSelectCategory(isSelected ? null : cat)}
                                    className={`w-full flex items-center justify-between text-xs py-2 px-2.5 rounded-xl transition-all text-left group cursor-pointer ${
                                        isSelected
                                            ? 'bg-red-50 text-[#C8102E] font-bold shadow-sm ring-1 ring-red-200'
                                            : 'text-slate-700 hover:text-[#C8102E] hover:bg-slate-50'
                                    }`}
                                >
                                    <span className="truncate pr-2">{cat.name}</span>
                                    <span
                                        className={`text-[10px] px-2 py-0.5 rounded-full font-mono flex-shrink-0 transition-colors ${
                                            isSelected
                                                ? 'bg-[#C8102E] text-white font-bold'
                                                : 'bg-slate-100 text-slate-500 group-hover:bg-red-100 group-hover:text-[#C8102E]'
                                        }`}
                                    >
                                        {cat.count}
                                    </span>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            </div>

            <div className="border-t border-slate-100" />

            {/* Custom Catalog Toggle */}
            <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-3 flex items-center justify-between">
                <div>
                    <span className="text-xs font-bold text-slate-800 block">
                        See your catalog
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                        Filter tailored equipment
                    </span>
                </div>
                <button
                    type="button"
                    onClick={() => onToggleUserCatalog(!userCatalogToggle)}
                    className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        userCatalogToggle ? 'bg-[#C8102E]' : 'bg-slate-300'
                    }`}
                >
                    <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            userCatalogToggle ? 'translate-x-5' : 'translate-x-0'
                        }`}
                    />
                </button>
            </div>

            <div className="border-t border-slate-100" />

            {/* Production Status Filter - Modern Segmented Controls */}
            <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 px-1 flex items-center gap-1.5">
                    <Filter className="w-3.5 h-3.5 text-[#0284C7]" />
                    Production Status
                </h3>

                <div className="bg-slate-100 p-1 rounded-xl flex flex-col gap-1">
                    {[
                        { id: 'all', label: 'All Statuses' },
                        { id: 'in_production', label: 'In Production' },
                        { id: 'out_of_production', label: 'Discontinued' },
                    ].map((item) => {
                        const active = statusFilter === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => onStatusFilterChange(item.id as any)}
                                className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                                    active
                                        ? 'bg-white text-slate-900 font-bold shadow-sm'
                                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
                                }`}
                            >
                                <span>{item.label}</span>
                                {active && <Check className="w-3.5 h-3.5 text-[#0284C7]" />}
                            </button>
                        );
                    })}
                </div>
            </div>
        </aside>
    );
};
