'use client';

import React from 'react';
import { CategoryData } from '@/lib/data';
import { ChevronRight } from 'lucide-react';

interface CategoryCardProps {
    category: CategoryData;
    onClick: () => void;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({ category, onClick }) => {
    return (
        <div
            onClick={onClick}
            role="button"
            tabIndex={0}
            className="group relative bg-white border border-slate-200/80 hover:border-[#C8102E]/40 rounded-2xl p-6 flex flex-col items-center justify-between text-center cursor-pointer shadow-xs hover:shadow-xl hover:shadow-red-900/5 hover:-translate-y-1.5 transition-all duration-300 min-h-[185px] select-none overflow-hidden"
        >
            {/* Soft gradient accent on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-red-50/0 via-transparent to-red-500/0 group-hover:to-red-500/5 transition-all duration-500 pointer-events-none" />

            {/* Models Badge */}
            <div className="w-full flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase tracking-wider font-extrabold text-slate-400 group-hover:text-[#C8102E] transition-colors">
                    Equipment
                </span>
                <span className="text-[11px] font-mono text-slate-600 bg-slate-100/90 px-2.5 py-0.5 rounded-full font-bold group-hover:bg-red-50 group-hover:text-[#C8102E] transition-all">
                    {category.count} models
                </span>
            </div>

            {/* Category SVG Icon */}
            <div
                className="w-16 h-16 my-2 flex items-center justify-center text-slate-700 group-hover:text-[#C8102E] group-hover:scale-110 transition-all duration-300"
                dangerouslySetInnerHTML={{ __html: category.icon || '' }}
            />

            {/* Category Name & Arrow Footer */}
            <div className="w-full flex items-center justify-center gap-1.5 pt-2">
                <h3 className="text-xs sm:text-sm font-extrabold text-slate-900 group-hover:text-[#C8102E] transition-colors leading-tight">
                    {category.name}
                </h3>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-[#C8102E] group-hover:translate-x-1 transition-all" />
            </div>
        </div>
    );
};
