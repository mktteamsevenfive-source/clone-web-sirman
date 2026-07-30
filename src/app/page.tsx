'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { Sidebar } from '@/components/Sidebar';
import { CategoryCard } from '@/components/CategoryCard';
import { ProductTable } from '@/components/ProductTable';
import { ExplodedViewViewer } from '@/components/ExplodedViewViewer';
import { PartsTable } from '@/components/PartsTable';
import { CategoryData, ProductData, FALLBACK_CATEGORIES, FALLBACK_PRODUCTS, getRealPartsForProduct } from '@/lib/data';
import { supabase } from '@/lib/supabase';
import { ChevronLeft, Loader2, X, SearchX } from 'lucide-react';

export default function Home() {
    const [categories, setCategories] = useState<CategoryData[]>(FALLBACK_CATEGORIES);
    const [products, setProducts] = useState<ProductData[]>(FALLBACK_PRODUCTS);
    const [loading, setLoading] = useState(true);
    const [partsLoading, setPartsLoading] = useState(false);

    const [activeTab, setActiveTab] = useState<'home' | 'catalog'>('catalog');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<CategoryData | null>(null);
    const [selectedProduct, setSelectedProduct] = useState<ProductData | null>(null);
    const [statusFilter, setStatusFilter] = useState<'all' | 'in_production' | 'out_of_production'>('all');
    const [userCatalogToggle, setUserCatalogToggle] = useState(false);
    const [selectedRef, setSelectedRef] = useState<string | null>(null);


    // Fetch initial categories and products from Supabase Cloud PostgreSQL
    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                const { data: catData, error: catErr } = await supabase.from('categories').select('*').order('name');
                const { data: prodData, error: prodErr } = await supabase.from('products').select('*').order('model');

                if (!catErr && catData && catData.length > 0) {
                    const fallbackMap: Record<string, string> = {};
                    FALLBACK_CATEGORIES.forEach(c => { fallbackMap[c.id] = c.icon; });

                    const mappedCats: CategoryData[] = catData.map((c: any) => ({
                        ...c,
                        icon: c.icon || fallbackMap[c.id] || `<svg viewBox="0 0 100 100" fill="currentColor"><circle cx="50" cy="50" r="30"/></svg>`
                    }));
                    setCategories(mappedCats);
                }

                if (!prodErr && prodData && prodData.length > 0) {
                    const mappedProds: ProductData[] = prodData.map((p: any) => ({
                        ...p,
                        category_id: p.category_id || p.categoryId,
                        category_name: p.category_name || p.categoryName || p.category,
                        pdf_name: p.pdf_name || p.pdfName,
                        exploded_view_id: p.exploded_view_id || p.explodedViewId,
                        parts_count: p.parts_count !== undefined ? p.parts_count : (p.partsCount || 0),
                        status: p.discontinued ? 'out_of_production' : 'in_production',
                        parts: getRealPartsForProduct(p.id, p.code)
                    }));
                    setProducts(mappedProds);
                }
            } catch (err) {
                console.warn("Supabase fetch notice, using cached Sirman data:", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    // Handle selecting a product & fetching its real model-specific spare parts
    const handleSelectProduct = async (prod: ProductData) => {
        // First set product with exact real parts for this model
        const modelParts = getRealPartsForProduct(prod.id, prod.code);
        setSelectedProduct({ ...prod, parts: modelParts });
        setPartsLoading(true);

        try {
            // Also fetch from Supabase 'parts' table for live prices & stock
            const { data: partsData, error } = await supabase
                .from('parts')
                .select('*')
                .eq('product_id', prod.id)
                .order('code');

            if (!error && partsData && partsData.length > 0) {
                const suggestedMap = new Set(modelParts.filter(p => p.suggested).map(p => p.code));
                const mergedParts = partsData.map((pt: any) => ({
                    ...pt,
                    suggested: suggestedMap.has(pt.code) || pt.suggested
                }));
                setSelectedProduct((prev) => prev ? { ...prev, parts: mergedParts } : null);
            }
        } catch (err) {
            console.warn("Supabase parts fetch notice:", err);
        } finally {
            setPartsLoading(false);
        }
    };

    // Reset filters
    const handleResetFilters = () => {
        setSearchQuery('');
        setSelectedCategory(null);
        setSelectedProduct(null);
        setStatusFilter('all');
    };

    // Filter products
    const displayProducts = products.filter((p) => {
        const matchesCategory = selectedCategory
            ? (p.category_id === selectedCategory.id || p.category === selectedCategory.name || (p as any).categoryId === selectedCategory.id)
            : true;

        const q = searchQuery.toLowerCase().trim();
        const matchesSearch = !q || (
            (p.code && p.code.toLowerCase().includes(q)) ||
            (p.model && p.model.toLowerCase().includes(q)) ||
            (p.serial && p.serial.toLowerCase().includes(q)) ||
            (p.description && p.description.toLowerCase().includes(q))
        );

        let matchesStatus = true;
        if (statusFilter === 'in_production') {
            matchesStatus = p.status === 'in_production';
        } else if (statusFilter === 'out_of_production') {
            matchesStatus = p.status === 'out_of_production';
        }

        return matchesCategory && matchesSearch && matchesStatus;
    });

    // Display Categories in grid
    const displayCategories = categories.filter((cat) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase().trim();
        return (
            cat.name.toLowerCase().includes(q) ||
            products.some(
                (p) =>
                    (p.category_id === cat.id || p.category === cat.name || (p as any).categoryId === cat.id) &&
                    (
                        (p.code && p.code.toLowerCase().includes(q)) ||
                        (p.model && p.model.toLowerCase().includes(q)) ||
                        (p.serial && p.serial.toLowerCase().includes(q))
                    )
            )
        );
    });

    return (
        <div className="min-h-screen bg-[#F8FAFC] flex flex-col text-slate-900 font-sans">
            {/* Navbar Header */}
            <Navbar
                searchQuery={searchQuery}
                onSearchChange={(q) => {
                    setSearchQuery(q);
                    if (q.trim() !== '') setSelectedProduct(null);
                }}
                onClearSearch={() => setSearchQuery('')}
                activeTab={activeTab}
                onTabChange={(tab) => {
                    setActiveTab(tab);
                    if (tab === 'catalog') handleResetFilters();
                }}
                onBrandClick={handleResetFilters}
            />

            {/* Main Content Body */}
            <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {selectedProduct ? (
                    /* EXPLODED VIEW WORKSPACE */
                    <div className="space-y-6 animate-fade-in">
                        {/* Header Breadcrumb */}
                        <div className="flex items-center justify-between bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setSelectedProduct(null)}
                                    className="flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-[#C8102E] bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-xl transition-all cursor-pointer"
                                >
                                    <ChevronLeft className="w-4 h-4" /> Back to Catalog
                                </button>
                                <div>
                                    <h1 className="text-xl font-bold text-slate-900">
                                        {selectedProduct.model}
                                    </h1>
                                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                                        Code: <span className="text-[#C8102E] font-bold">{selectedProduct.code}</span> • Serial: {selectedProduct.serial}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Exploded View Grid Layout */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="lg:col-span-2 overflow-hidden [overflow:hidden_!important]">
                                <ExplodedViewViewer
                                    product={selectedProduct}
                                    selectedRef={selectedRef}
                                    onSelectPartRef={(ref) => setSelectedRef((prev) => (prev === ref ? null : ref))}
                                />
                            </div>
                            <div className="lg:col-span-1">
                                <PartsTable
                                    parts={selectedProduct.parts || []}
                                    loading={partsLoading}
                                    selectedRef={selectedRef}
                                    onSelectPartRef={(ref) => setSelectedRef((prev) => (prev === ref ? null : ref))}
                                />
                            </div>
                        </div>

                    </div>
                ) : (
                    /* MAIN CATALOG VIEW (Sidebar + Category Grid or Products Table) */
                    <div className="flex flex-col lg:flex-row gap-8">
                        {/* Left Sidebar Filters */}
                        <Sidebar
                            categories={categories}
                            selectedCategory={selectedCategory}
                            onSelectCategory={(cat) => setSelectedCategory(cat)}
                            userCatalogToggle={userCatalogToggle}
                            onToggleUserCatalog={(val) => setUserCatalogToggle(val)}
                            statusFilter={statusFilter}
                            onStatusFilterChange={(val) => setStatusFilter(val)}
                        />

                        {/* Right Main Catalog Area */}
                        <section className="flex-1 space-y-6">
                            {/* Page Header */}
                            <div className="flex items-center justify-between">
                                <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                                    {selectedCategory ? selectedCategory.name : 'Catalog'}
                                </h1>

                                {(searchQuery || selectedCategory || statusFilter !== 'all') && (
                                    <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-[#0284C7] px-3 py-1 rounded-full text-xs font-semibold">
                                        <span>
                                            {selectedCategory
                                                ? `Category: ${selectedCategory.name}`
                                                : searchQuery
                                                ? `Search: "${searchQuery}"`
                                                : `Filter: ${statusFilter}`}
                                        </span>
                                        <button onClick={handleResetFilters} className="hover:text-slate-900 cursor-pointer">
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* Loading Indicator */}
                            {loading && (
                                <div className="flex flex-col items-center justify-center py-24 text-slate-400">
                                    <Loader2 className="w-10 h-10 text-[#C8102E] animate-spin mb-3" />
                                    <p className="text-xs font-semibold text-slate-600">Loading catalog models from Supabase...</p>
                                </div>
                            )}

                            {/* CATEGORY GRID (Default view when no category or search is active) */}
                            {!loading && !selectedCategory && !searchQuery && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                                    {displayCategories.map((cat) => (
                                        <CategoryCard
                                            key={cat.id}
                                            category={cat}
                                            onClick={() => setSelectedCategory(cat)}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* PRODUCT TABLE (Shown when category clicked or search entered) */}
                            {!loading && (selectedCategory || searchQuery) && (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <button
                                            onClick={() => {
                                                setSelectedCategory(null);
                                                setSearchQuery('');
                                            }}
                                            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-[#C8102E] transition-colors cursor-pointer"
                                        >
                                            <ChevronLeft className="w-4 h-4" /> Back to Categories
                                        </button>
                                        <span className="text-xs text-slate-500 font-mono">
                                            {displayProducts.length} model(s) found
                                        </span>
                                    </div>

                                    {displayProducts.length === 0 ? (
                                        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center">
                                            <SearchX className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                                            <h3 className="font-bold text-slate-800 text-sm mb-1">
                                                No machine models match your criteria
                                            </h3>
                                            <p className="text-xs text-slate-500">
                                                Try searching for a different part code or serial number.
                                            </p>
                                        </div>
                                    ) : (
                                        <ProductTable
                                            products={displayProducts}
                                            onSelectProduct={handleSelectProduct}
                                        />
                                    )}
                                </div>
                            )}
                        </section>
                    </div>
                )}
            </main>
        </div>
    );
}
