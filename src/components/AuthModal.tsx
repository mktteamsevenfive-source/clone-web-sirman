'use client';

import React, { useState } from 'react';
import { X, Lock, Mail, User, ShieldAlert, Wrench, CheckCircle } from 'lucide-react';
import { UserRole } from '@/lib/types';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onAuthenticate: (email: string, role: UserRole) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthenticate }) => {
    const [mode, setMode] = useState<'signin' | 'signup'>('signin');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<UserRole>('technician');
    const [successMessage, setSuccessMessage] = useState('');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!email.trim()) return;

        onAuthenticate(email, role);
        setSuccessMessage(`Authenticated successfully as ${role.toUpperCase()}`);
        setTimeout(() => {
            setSuccessMessage('');
            onClose();
        }, 1200);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="bg-[#324050] text-white p-6 relative">
                    <button
                        onClick={onClose}
                        className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-full hover:bg-slate-700/50 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="bg-[#C8102E] p-2.5 rounded-xl text-white">
                            <Lock className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">Sirman Service Portal</h2>
                            <p className="text-xs text-slate-300">
                                {mode === 'signin' ? 'Sign in to access technical diagrams & prices' : 'Create new technician / dealer account'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Form Body */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {successMessage ? (
                        <div className="flex items-center gap-2 p-4 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-xl text-sm font-semibold">
                            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                            <span>{successMessage}</span>
                        </div>
                    ) : null}

                    <div>
                        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                            Email Address
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-[#C8102E] focus:outline-none"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                            Password
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl text-slate-900 focus:ring-2 focus:ring-[#C8102E] focus:outline-none"
                            />
                        </div>
                    </div>

                    {/* Role Selection */}
                    <div>
                        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                            Access Role (RBAC System)
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            <button
                                type="button"
                                onClick={() => setRole('technician')}
                                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-medium transition-all ${
                                    role === 'technician'
                                        ? 'bg-blue-50 border-blue-500 text-blue-700 ring-2 ring-blue-500/20 font-semibold'
                                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                                <Wrench className="w-4 h-4 mb-1 text-blue-600" />
                                Technician
                            </button>
                            <button
                                type="button"
                                onClick={() => setRole('dealer')}
                                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-medium transition-all ${
                                    role === 'dealer'
                                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700 ring-2 ring-emerald-500/20 font-semibold'
                                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                                <User className="w-4 h-4 mb-1 text-emerald-600" />
                                Dealer
                            </button>
                            <button
                                type="button"
                                onClick={() => setRole('admin')}
                                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-medium transition-all ${
                                    role === 'admin'
                                        ? 'bg-red-50 border-red-500 text-red-700 ring-2 ring-red-500/20 font-semibold'
                                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                                <ShieldAlert className="w-4 h-4 mb-1 text-red-600" />
                                Admin
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-[#C8102E] hover:bg-[#A00C24] text-white font-semibold py-3 rounded-xl transition-colors shadow-md text-sm mt-2"
                    >
                        {mode === 'signin' ? 'Sign In Now' : 'Create Account'}
                    </button>

                    <div className="text-center pt-2">
                        <button
                            type="button"
                            onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
                            className="text-xs text-slate-500 hover:text-slate-800 font-medium underline"
                        >
                            {mode === 'signin' ? "Don't have an account? Register here" : 'Already have an account? Sign in'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
