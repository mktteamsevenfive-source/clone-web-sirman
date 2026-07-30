'use client';

import React, { useState } from 'react';
import { X, QrCode, Search, CheckCircle2 } from 'lucide-react';

interface BarcodeModalProps {
    isOpen: boolean;
    onClose: () => void;
    onScanCode: (scannedCode: string) => void;
}

export const BarcodeModal: React.FC<BarcodeModalProps> = ({
    isOpen,
    onClose,
    onScanCode,
}) => {
    const [barcodeInput, setBarcodeInput] = useState('');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!barcodeInput.trim()) return;
        onScanCode(barcodeInput.trim());
        setBarcodeInput('');
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl max-w-md w-full overflow-hidden">
                {/* Header */}
                <div className="p-5 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-xl bg-red-50 text-[#C8102E] flex items-center justify-center">
                            <QrCode className="w-4 h-4" />
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900 text-sm">
                                Search Using Barcode / Serial
                            </h3>
                            <p className="text-[11px] text-slate-500">
                                Scan or enter machine/part barcode.
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-full transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Form / Scanner Simulator */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Simulated Scanner Viewport */}
                    <div className="border-2 border-dashed border-red-300 bg-red-50/50 rounded-2xl p-6 text-center space-y-2 relative overflow-hidden">
                        <div className="w-12 h-12 rounded-2xl bg-white text-[#C8102E] mx-auto flex items-center justify-center shadow-sm">
                            <QrCode className="w-6 h-6 animate-pulse" />
                        </div>
                        <p className="text-xs font-semibold text-slate-800">
                            Position barcode or QR code inside the frame
                        </p>
                        <p className="text-[10px] text-slate-500">
                            Supports Part Code (e.g. IB4000710, GL10DC01) & Serial Number
                        </p>
                    </div>

                    {/* Manual Code Input */}
                    <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                            Barcode Number / Part Code
                        </label>
                        <div className="relative">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                value={barcodeInput}
                                onChange={(e) => setBarcodeInput(e.target.value)}
                                placeholder="e.g. IB4000710 or SIR-BAR-1273"
                                className="w-full bg-slate-50 text-slate-900 text-sm rounded-xl pl-10 pr-4 py-2.5 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20 focus:border-[#C8102E] transition-all font-mono"
                                autoFocus
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-[#C8102E] hover:bg-[#A00C24] text-white font-bold text-sm py-3 rounded-xl transition-all shadow-md active:scale-98 cursor-pointer"
                    >
                        Search Catalog
                    </button>
                </form>
            </div>
        </div>
    );
};
