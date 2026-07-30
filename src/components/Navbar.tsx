'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Search, User, ShieldCheck, LogIn, LogOut, Wrench } from 'lucide-react';
import { UserProfile } from '@/lib/types';

interface NavbarProps {
    onSearch?: (query: string) => void;
    user?: UserProfile | null;
    onLoginClick?: () => void;
    onLogoutClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
    onSearch,
    user,
    onLoginClick,
    onLogoutClick,
}) => {
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setSearchQuery(val);
        if (onSearch) onSearch(val);
    };

    return (
        <header className="sticky top-0 z-50 bg-[#324050] text-white shadow-md">
            {/* Top Bar */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 gap-4">
                    {/* Brand Logo */}
                    <Link href="/" className="flex items-center gap-2 group">
                        <span className="text-2xl font-black tracking-tight text-white group-hover:text-red-400 transition-colors">
                            SIRMAN
                        </span>
                        <span className="bg-[#C8102E] text-white text-xs px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                            SERVICE
                        </span>
                    </Link>

                    {/* Live Search Bar */}
                    <div className="flex-1 max-w-xl mx-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={handleSearchChange}
                                placeholder="Search part codes, model names, or serial numbers..."
                                className="w-full bg-slate-800/80 text-white placeholder-slate-400 text-sm rounded-lg pl-10 pr-4 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#C8102E] focus:border-transparent transition-all"
                            />
                        </div>
                    </div>

                    {/* Auth & Role Section */}
                    <div className="flex items-center gap-3">
                        {user ? (
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
                                    {user.role === 'admin' ? (
                                        <ShieldCheck className="w-4 h-4 text-red-400" />
                                    ) : user.role === 'technician' ? (
                                        <Wrench className="w-4 h-4 text-blue-400" />
                                    ) : (
                                        <User className="w-4 h-4 text-emerald-400" />
                                    )}
                                    <div className="text-xs">
                                        <div className="font-semibold text-white truncate max-w-[120px]">{user.email}</div>
                                        <div className="text-[10px] text-slate-400 capitalize">{user.role}</div>
                                    </div>
                                </div>
                                <button
                                    onClick={onLogoutClick}
                                    className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                                    title="Sign Out"
                                >
                                    <LogOut className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={onLoginClick}
                                className="flex items-center gap-2 bg-[#C8102E] hover:bg-[#A00C24] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all shadow-sm"
                            >
                                <LogIn className="w-4 h-4" />
                                Sign In / Register
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Sub-nav Category bar */}
            <div className="bg-[#273342] border-t border-slate-700/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <nav className="flex space-x-6 text-xs font-medium py-2.5 overflow-x-auto scrollbar-none">
                        <Link href="/" className="text-white hover:text-red-400 whitespace-nowrap transition-colors">
                            Home Catalog
                        </Link>
                        <span className="text-slate-600">|</span>
                        <span className="text-slate-400 whitespace-nowrap">
                            13 Categories • 208 Models • 13,149 Spare Parts
                        </span>
                    </nav>
                </div>
            </div>
        </header>
    );
};
