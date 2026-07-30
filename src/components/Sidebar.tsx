'use client';

import React from 'react';
import { CategoryData } from '@/lib/data';

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
        <aside className="w-full lg:w-60 flex-shrink-0 space-y-6">
            {/* Categories Section */}
            <div>
                <h2 className="text-sm font-bold text-slate-900 tracking-tight mb-3">
                    Categories
                </h2>
                <ul className="space-y-1">
                    {categories.map((cat) => {
                        const isSelected = selectedCategory?.id === cat.id;
                        return (
                            <li key={cat.id}>
                                <button
                                    onClick={() => onSelectCategory(isSelected ? null : cat)}
                                    className={`w-full flex items-center justify-between text-xs py-1.5 px-2 rounded-lg transition-all text-left ${
                                        isSelected
                                            ? 'bg-red-50 text-[#C8102E] font-semibold border-l-2 border-[#C8102E]'
                                            : 'text-slate-600 hover:text-[#C8102E] hover:bg-slate-100/60'
                                    }`}
                                >
                                    <span className="truncate pr-2">{cat.name}</span>
                                    <span
                                        className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono flex-shrink-0 ${
                                            isSelected
                                                ? 'bg-red-100 text-[#C8102E]'
                                                : 'bg-slate-100 text-slate-400'
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

            <div className="border-t border-slate-200" />

            {/* See Your Catalog Toggle */}
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800">
                    See your catalog
                </span>
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

            <div className="border-t border-slate-200" />

            {/* Status Radio Filters */}
            <div className="space-y-2">
                {[
                    { id: 'all', label: 'All' },
                    { id: 'in_production', label: 'In production' },
                    { id: 'out_of_production', label: 'Out of production' },
                ].map((item) => (
                    <label
                        key={item.id}
                        className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer hover:text-slate-900 select-none"
                    >
                        <input
                            type="radio"
                            name="statusFilter"
                            checked={statusFilter === item.id}
                            onChange={() => onStatusFilterChange(item.id as any)}
                            className="sr-only"
                        />
                        <div
                            className={`w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all ${
                                statusFilter === item.id
                                    ? 'border-[#0284C7] bg-white'
                                    : 'border-slate-300 hover:border-slate-400'
                            }`}
                        >
                            {statusFilter === item.id && (
                                <div className="w-2 h-2 rounded-full bg-[#0284C7]" />
                            )}
                        </div>
                        <span>{item.label}</span>
                    </label>
                ))}
            </div>
        </aside>
    );
};
