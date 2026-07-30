'use client';

import React, { useState } from 'react';
import { UserRole } from '@/lib/types';
import { X, Lock, Mail, ShieldAlert, Wrench, User, CheckCircle2 } from 'lucide-react';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onAuthenticate: (email: string, role: UserRole) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
    isOpen,
    onClose,
    onAuthenticate,
}) => {
    const [email, setEmail] = useState('');
    const [role, setRole] = useState<UserRole>('technician');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!email.trim()) return;
        onAuthenticate(email, role);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl max-w-md w-full overflow-hidden">
                {/* Header */}
                <div className="p-6 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                            <span className="text-[#C8102E]">SIRMAN</span> Service Auth
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                            Sign in to view trade prices, stock, and technical manuals.
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Role Selection */}
                    <div>
                        <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
                            Select Account Type
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { id: 'technician', label: 'Technician', icon: Wrench },
                                { id: 'dealer', label: 'Dealer', icon: User },
                                { id: 'admin', label: 'Admin', icon: ShieldAlert },
                            ].map((r) => {
                                const IconComp = r.icon;
                                const isSelected = role === r.id;
                                return (
                                    <button
                                        key={r.id}
                                        type="button"
                                        onClick={() => setRole(r.id as UserRole)}
                                        className={`flex flex-col items-center gap-1.5 p-3 rounded-2xl border text-xs font-semibold transition-all ${
                                            isSelected
                                                ? 'bg-red-50 border-[#C8102E] text-[#C8102E] shadow-sm'
                                                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                                        }`}
                                    >
                                        <IconComp className="w-4 h-4" />
                                        <span>{r.label}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Email Input */}
                    <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Email Address
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="service.tech@sirman.com"
                                className="w-full bg-slate-50 text-slate-900 text-sm rounded-xl pl-10 pr-4 py-2.5 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20 focus:border-[#C8102E] transition-all"
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        className="w-full bg-[#C8102E] hover:bg-[#A00C24] text-white font-bold text-sm py-3 rounded-xl transition-all shadow-md active:scale-98 cursor-pointer"
                    >
                        Sign In as {role.toUpperCase()}
                    </button>
                </form>
            </div>
        </div>
    );
};
