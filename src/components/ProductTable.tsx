'use client';

import React from 'react';
import { ProductData } from '@/lib/data';
import { Scissors, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

interface ProductTableProps {
    products: ProductData[];
    onSelectProduct: (product: ProductData) => void;
}

export const ProductTable: React.FC<ProductTableProps> = ({ products, onSelectProduct }) => {
    return (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-700 uppercase font-semibold text-[11px] border-b border-slate-200">
                        <tr>
                            <th className="py-3.5 px-4">Model & Code</th>
                            <th className="py-3.5 px-4">Category</th>
                            <th className="py-3.5 px-4">Description</th>
                            <th className="py-3.5 px-4">Status</th>
                            <th className="py-3.5 px-4 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {products.map((prod) => (
                            <tr
                                key={prod.id}
                                className="hover:bg-slate-50/80 transition-colors group"
                            >
                                <td className="py-3.5 px-4">
                                    <div className="font-bold text-slate-900 text-sm group-hover:text-[#C8102E] transition-colors">
                                        {prod.model}
                                    </div>
                                    <div className="text-slate-500 font-mono text-[11px] mt-0.5">
                                        Code: <span className="text-[#C8102E] font-bold">{prod.code}</span> • SN: {prod.serial}
                                    </div>
                                </td>
                                <td className="py-3.5 px-4 text-slate-600 font-medium">
                                    {prod.category_name || prod.category}
                                </td>
                                <td className="py-3.5 px-4 text-slate-600 max-w-sm">
                                    {prod.description}
                                </td>
                                <td className="py-3.5 px-4">
                                    {prod.status === 'out_of_production' ? (
                                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-md">
                                            <AlertCircle className="w-3 h-3 text-slate-400" />
                                            Out of prod.
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                            In production
                                        </span>
                                    )}
                                </td>
                                <td className="py-3.5 px-4 text-center">
                                    <button
                                        onClick={() => onSelectProduct(prod)}
                                        className="inline-flex items-center gap-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-semibold text-xs px-3.5 py-1.5 rounded-xl transition-all shadow-sm active:scale-95 cursor-pointer"
                                    >
                                        <Scissors className="w-3.5 h-3.5" />
                                        Exploded View
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
