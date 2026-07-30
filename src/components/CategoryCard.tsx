'use client';

import React from 'react';
import { CategoryData } from '@/lib/data';

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
            className="group relative bg-white border border-slate-200 hover:border-[#C8102E]/30 rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 min-h-[175px] select-none"
        >
            {/* Models Badge */}
            <span className="absolute top-3 right-3 text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full font-medium group-hover:bg-red-50 group-hover:text-[#C8102E] transition-colors">
                {category.count} models
            </span>

            {/* Category SVG Icon */}
            <div
                className="w-16 h-16 mb-4 flex items-center justify-center text-slate-700 group-hover:text-[#C8102E] group-hover:scale-110 transition-all duration-300"
                dangerouslySetInnerHTML={{ __html: category.icon || '' }}
            />

            {/* Category Name */}
            <h3 className="text-xs sm:text-sm font-bold text-slate-900 group-hover:text-[#C8102E] transition-colors leading-tight">
                {category.name}
            </h3>
        </div>
    );
};
