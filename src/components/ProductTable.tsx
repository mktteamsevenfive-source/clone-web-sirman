'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ProductData, cleanText } from '@/lib/data';
import { Scissors, CheckCircle2, AlertCircle, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

interface ProductTableProps {
    products: ProductData[];
    onSelectProduct: (product: ProductData) => void;
}

export const ProductTable: React.FC<ProductTableProps> = ({ products, onSelectProduct }) => {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(25);
    const containerRef = useRef<HTMLDivElement>(null);

    // Reset to page 1 whenever products list changes
    useEffect(() => {
        setCurrentPage(1);
    }, [products]);

    const totalItems = products.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
    const safePage = Math.min(currentPage, totalPages);

    const startIndex = (safePage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
    const currentProducts = products.slice(startIndex, endIndex);

    const handlePageChange = (newPage: number) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
            if (containerRef.current) {
                containerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    };

    // Helper to generate page numbers with ellipsis
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxPagesToShow = 5;

        if (totalPages <= maxPagesToShow + 2) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            pages.push(1);
            if (safePage > 3) pages.push('...');

            const start = Math.max(2, safePage - 1);
            const end = Math.min(totalPages - 1, safePage + 1);

            for (let i = start; i <= end; i++) pages.push(i);

            if (safePage < totalPages - 2) pages.push('...');
            pages.push(totalPages);
        }
        return pages;
    };

    return (
        <div ref={containerRef} className="bg-white border border-slate-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            {/* Table Container */}
            <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/90 text-slate-700 uppercase font-extrabold text-[11px] border-b border-slate-200/80">
                        <tr>
                            <th className="py-3.5 px-4">Model & Code</th>
                            <th className="py-3.5 px-4">Category</th>
                            <th className="py-3.5 px-4">Description</th>
                            <th className="py-3.5 px-4">Status</th>
                            <th className="py-3.5 px-4 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {currentProducts.map((prod) => {
                            const cleanModel = cleanText(prod.model);
                            const cleanDesc = cleanText(prod.description);
                            const cleanCat = cleanText(prod.category_name || prod.category);

                            return (
                                <tr
                                    key={prod.id}
                                    className="hover:bg-slate-50/80 transition-colors group"
                                >
                                    <td className="py-3.5 px-4">
                                        <div className="font-bold text-slate-900 text-sm group-hover:text-[#C8102E] transition-colors">
                                            {cleanModel}
                                        </div>
                                        <div className="text-slate-500 font-mono text-[11px] mt-0.5">
                                            Code: <span className="text-[#C8102E] font-bold">{prod.code}</span> • SN: {prod.serial}
                                        </div>
                                    </td>
                                    <td className="py-3.5 px-4 text-slate-600 font-semibold">
                                        {cleanCat}
                                    </td>
                                    <td className="py-3.5 px-4 text-slate-600 max-w-sm">
                                        {cleanDesc}
                                    </td>
                                <td className="py-3.5 px-4">
                                    {prod.status === 'out_of_production' ? (
                                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-500 bg-slate-100 border border-slate-200/80 px-2 py-0.5 rounded-md">
                                            <AlertCircle className="w-3 h-3 text-slate-400" />
                                            Discontinued
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                            In production
                                        </span>
                                    )}
                                </td>
                                <td className="py-3.5 px-4 text-center">
                                    <button
                                        onClick={() => onSelectProduct(prod)}
                                        className="inline-flex items-center gap-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-extrabold text-xs px-3.5 py-1.5 rounded-xl transition-all shadow-2xs active:scale-95 cursor-pointer"
                                    >
                                        <Scissors className="w-3.5 h-3.5" />
                                        Exploded View
                                    </button>
                                </td>
                            </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Pagination Controls Bar */}
            <div className="bg-slate-50/90 border-t border-slate-200/80 px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                {/* Range Stats & Per Page Selector */}
                <div className="flex items-center gap-4 text-slate-600 font-medium">
                    <span>
                        Showing <strong className="text-slate-900 font-bold">{totalItems > 0 ? startIndex + 1 : 0}</strong> to{' '}
                        <strong className="text-slate-900 font-bold">{endIndex}</strong> of{' '}
                        <strong className="text-slate-900 font-bold">{totalItems.toLocaleString()}</strong> models
                    </span>

                    <div className="flex items-center gap-1.5">
                        <span className="text-slate-400">Show</span>
                        <select
                            value={itemsPerPage}
                            onChange={(e) => {
                                setItemsPerPage(Number(e.target.value));
                                setCurrentPage(1);
                            }}
                            className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#C8102E]/20 focus:border-[#C8102E] cursor-pointer"
                        >
                            <option value={15}>15</option>
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                        </select>
                        <span className="text-slate-400">per page</span>
                    </div>
                </div>

                {/* Page Navigation Buttons */}
                {totalPages > 1 && (
                    <div className="flex items-center gap-1">
                        {/* First Page */}
                        <button
                            onClick={() => handlePageChange(1)}
                            disabled={safePage === 1}
                            className="p-1.5 rounded-lg border border-slate-200/80 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
                            title="First Page"
                        >
                            <ChevronsLeft className="w-4 h-4" />
                        </button>

                        {/* Previous Page */}
                        <button
                            onClick={() => handlePageChange(safePage - 1)}
                            disabled={safePage === 1}
                            className="p-1.5 rounded-lg border border-slate-200/80 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
                            title="Previous Page"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>

                        {/* Numbered Buttons */}
                        <div className="flex items-center gap-1">
                            {getPageNumbers().map((p, idx) => {
                                if (typeof p === 'string') {
                                    return (
                                        <span key={idx} className="px-2 py-1 text-slate-400 font-bold">
                                            ...
                                        </span>
                                    );
                                }
                                const isCurrent = p === safePage;
                                return (
                                    <button
                                        key={p}
                                        onClick={() => handlePageChange(p)}
                                        className={`min-w-[32px] h-8 px-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                                            isCurrent
                                                ? 'bg-[#C8102E] text-white shadow-xs'
                                                : 'bg-white border border-slate-200/80 text-slate-700 hover:bg-slate-100'
                                        }`}
                                    >
                                        {p}
                                    </button>
                                );
                            })}
                        </div>

                        {/* Next Page */}
                        <button
                            onClick={() => handlePageChange(safePage + 1)}
                            disabled={safePage === totalPages}
                            className="p-1.5 rounded-lg border border-slate-200/80 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
                            title="Next Page"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>

                        {/* Last Page */}
                        <button
                            onClick={() => handlePageChange(totalPages)}
                            disabled={safePage === totalPages}
                            className="p-1.5 rounded-lg border border-slate-200/80 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
                            title="Last Page"
                        >
                            <ChevronsRight className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
