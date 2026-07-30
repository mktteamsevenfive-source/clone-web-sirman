'use client';

import React from 'react';
import { Search, X } from 'lucide-react';

interface NavbarProps {
    searchQuery: string;
    onSearchChange: (query: string) => void;
    onClearSearch: () => void;
    activeTab: 'home' | 'catalog';
    onTabChange: (tab: 'home' | 'catalog') => void;
    onBrandClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
    searchQuery,
    onSearchChange,
    onClearSearch,
    activeTab,
    onTabChange,
    onBrandClick,
}) => {
    return (
        <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
            {/* Top Header Row */}
            <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 gap-4">
                    {/* Brand Logo */}
                    <div
                        onClick={onBrandClick}
                        className="flex items-center gap-2 cursor-pointer group select-none"
                    >
                        <span className="font-heading text-2xl sm:text-3xl font-extrabold text-[#C8102E] tracking-tight group-hover:opacity-90 transition-opacity">
                            SIRMAN
                        </span>
                        <span className="bg-red-50 text-[#C8102E] border border-red-100 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider">
                            SERVICE
                        </span>
                    </div>

                    {/* Search Bar */}
                    <div className="flex-1 max-w-xl mx-2 sm:mx-6">
                        <div className="relative group">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-[#C8102E] transition-colors" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => onSearchChange(e.target.value)}
                                placeholder="Search part codes or serial number..."
                                className="w-full bg-slate-50 hover:bg-slate-100/80 focus:bg-white text-slate-900 placeholder:text-slate-400 text-sm rounded-xl pl-10 pr-10 py-2 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20 focus:border-[#C8102E] transition-all shadow-inner"
                            />
                            {searchQuery.trim() !== '' && (
                                <button
                                    onClick={onClearSearch}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors"
                                    title="Clear search"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Sub-Header Navigation */}
            <div className="bg-[#324050] text-white border-t border-slate-700/50">
                <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
                    <nav className="flex space-x-1 text-sm font-medium">
                        <button
                            onClick={() => onTabChange('home')}
                            className={`px-5 py-3 relative transition-all ${
                                activeTab === 'home'
                                    ? 'text-white font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[3px] after:bg-white'
                                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                            }`}
                        >
                            Home
                        </button>
                        <button
                            onClick={() => onTabChange('catalog')}
                            className={`px-5 py-3 relative transition-all ${
                                activeTab === 'catalog'
                                    ? 'text-white font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[3px] after:bg-white'
                                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                            }`}
                        >
                            Catalog
                        </button>
                    </nav>
                </div>
            </div>
        </header>
    );
};
