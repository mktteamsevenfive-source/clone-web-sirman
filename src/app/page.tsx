'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { AuthModal } from '@/components/AuthModal';
import { ExplodedViewViewer } from '@/components/ExplodedViewViewer';
import { PartsTable } from '@/components/PartsTable';
import { Category, Product, UserProfile, UserRole } from '@/lib/types';
import { supabase } from '@/lib/supabase';
import { ArrowLeft, Box, FileText, Layers, Loader2, Package, Scissors, ShieldAlert } from 'lucide-react';

export default function Home() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);

    const [user, setUser] = useState<UserProfile | null>(null);
    const [isAuthOpen, setIsAuthOpen] = useState(false);

    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    // Fetch initial catalog data from Supabase Cloud PostgreSQL
    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                const { data: catData } = await supabase.from('categories').select('*').order('name');
                const { data: prodData } = await supabase.from('products').select('*').order('model');

                if (catData && catData.length > 0) {
                    setCategories(catData);
                }
                if (prodData && prodData.length > 0) {
                    setProducts(prodData);
                }
            } catch (err) {
                console.error("Supabase fetch error:", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    // Auth handler
    const handleAuthenticate = (email: string, role: UserRole) => {
        const newUser: UserProfile = {
            id: 'user-' + Date.now(),
            email,
            role,
            created_at: new Date().toISOString(),
        };
        setUser(newUser);
    };

    const handleLogout = () => {
        setUser(null);
    };

    // Filter products
    const displayProducts = products.filter(p => {
        const matchesCategory = selectedCategory ? (p.category_id === selectedCategory.id || p.category === selectedCategory.name) : true;
        const q = searchQuery.toLowerCase().trim();
        const matchesSearch = !q || (
            p.code.toLowerCase().includes(q) ||
            p.model.toLowerCase().includes(q) ||
            p.serial.toLowerCase().includes(q) ||
            p.description.toLowerCase().includes(q)
        );
        return matchesCategory && matchesSearch;
    });

    return (
        <div className="min-h-screen bg-[#F5F7FA] flex flex-col text-slate-900 font-sans">
            {/* Navigation Header */}
            <Navbar
                onSearch={(q) => setSearchQuery(q)}
                user={user}
                onLoginClick={() => setIsAuthOpen(true)}
                onLogoutClick={handleLogout}
            />

            {/* Main Content Area */}
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* EXPLODED VIEW DETAILED PAGE */}
                {selectedProduct ? (
                    <div className="space-y-6">
                        {/* Header Breadcrumb */}
                        <div className="flex items-center justify-between bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setSelectedProduct(null)}
                                    className="flex items-center gap-2 text-xs font-bold text-slate-700 hover:text-[#C8102E] bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-xl transition-all"
                                >
                                    <ArrowLeft className="w-4 h-4" /> Back to Catalog
                                </button>
                                <div>
                                    <h1 className="text-xl font-bold text-slate-900 flex items-center gap-3">
                                        {selectedProduct.model}
                                        {selectedProduct.pdf_name && (
                                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-lg">
                                                <FileText className="w-3.5 h-3.5" />
                                                {selectedProduct.pdf_name}
                                            </span>
                                        )}
                                    </h1>
                                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                                        Code: {selectedProduct.code} • SN: {selectedProduct.serial}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Exploded View Grid Layout */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Left Pane: Diagram Canvas */}
                            <div className="lg:col-span-2">
                                <ExplodedViewViewer product={selectedProduct} />
                            </div>

                            {/* Right Pane: Spare Parts List */}
                            <div className="lg:col-span-1">
                                <PartsTable
                                    parts={selectedProduct.parts || []}
                                    userRole={user?.role || 'guest'}
                                    onLoginPrompt={() => setIsAuthOpen(true)}
                                />
                            </div>
                        </div>
                    </div>
                ) : (
                    /* CATALOG HOME & CATEGORY GRID VIEW */
                    <div className="space-y-8">
                        {/* Page Header */}
                        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                            <div>
                                <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                                    {selectedCategory ? selectedCategory.name : 'Sirman Service Catalog'}
                                </h1>
                                <p className="text-xs text-slate-500 mt-1">
                                    {selectedCategory
                                        ? `Showing ${displayProducts.length} models in ${selectedCategory.name}`
                                        : 'Select a category or search for machine models and spare part codes.'}
                                </p>
                            </div>

                            {selectedCategory && (
                                <button
                                    onClick={() => setSelectedCategory(null)}
                                    className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 px-3 py-1.5 rounded-lg shadow-sm"
                                >
                                    View All Categories
                                </button>
                            )}
                        </div>

                        {/* Loading Spinner */}
                        {loading && (
                            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                                <Loader2 className="w-10 h-10 text-[#C8102E] animate-spin mb-3" />
                                <p className="text-sm font-medium">Loading real catalog data from Supabase Cloud...</p>
                            </div>
                        )}

                        {/* Category Cards Grid (When no search & no category selected) */}
                        {!loading && !selectedCategory && !searchQuery && (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {categories.map(cat => (
                                    <div
                                        key={cat.id}
                                        onClick={() => setSelectedCategory(cat)}
                                        className="group bg-white p-5 rounded-2xl border border-slate-200 hover:border-[#C8102E]/40 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
                                    >
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="w-12 h-12 rounded-xl bg-slate-100 text-[#C8102E] flex items-center justify-center group-hover:bg-red-50 group-hover:scale-105 transition-all">
                                                <Package className="w-6 h-6" />
                                            </div>
                                            <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                                                {cat.count} models
                                            </span>
                                        </div>
                                        <h3 className="font-bold text-slate-900 text-sm group-hover:text-[#C8102E] transition-colors">
                                            {cat.name}
                                        </h3>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Products Table (When Category selected or Search triggered) */}
                        {!loading && (selectedCategory || searchQuery) && (
                            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                                <div className="p-4 border-b border-slate-100 bg-slate-50 font-semibold text-xs text-slate-600">
                                    Found {displayProducts.length} model(s)
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-xs">
                                        <thead className="bg-slate-100 text-slate-700 uppercase font-semibold text-[11px] border-b border-slate-200">
                                            <tr>
                                                <th className="p-4">Model & Part Code</th>
                                                <th className="p-4">Category</th>
                                                <th className="p-4">Description</th>
                                                <th className="p-4 text-center">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {displayProducts.map(prod => (
                                                <tr key={prod.id} className="hover:bg-slate-50/80 transition-colors">
                                                    <td className="p-4 font-medium">
                                                        <div className="font-bold text-slate-900 text-sm">{prod.model}</div>
                                                        <div className="text-slate-500 font-mono text-[11px] mt-0.5">
                                                            Code: <span className="text-[#C8102E] font-bold">{prod.code}</span> • SN: {prod.serial}
                                                        </div>
                                                    </td>
                                                    <td className="p-4 text-slate-600">{prod.category_name || prod.category}</td>
                                                    <td className="p-4 text-slate-600 max-w-sm">
                                                        {prod.description}
                                                    </td>
                                                    <td className="p-4 text-center">
                                                        <button
                                                            onClick={() => setSelectedProduct(prod)}
                                                            className="inline-flex items-center gap-1.5 bg-[#0284C7] hover:bg-[#0369A1] text-white font-bold px-3.5 py-2 rounded-xl transition-all shadow-sm"
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
                        )}
                    </div>
                )}
            </main>

            {/* Auth Modal */}
            <AuthModal
                isOpen={isAuthOpen}
                onClose={() => setIsAuthOpen(false)}
                onAuthenticate={handleAuthenticate}
            />
        </div>
    );
}
