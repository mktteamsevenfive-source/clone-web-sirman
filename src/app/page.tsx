'use client';

import React, { useEffect, useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { Sidebar } from '@/components/Sidebar';
import { CategoryCard } from '@/components/CategoryCard';
import { ProductTable } from '@/components/ProductTable';
import { ExplodedViewViewer } from '@/components/ExplodedViewViewer';
import { PartsTable } from '@/components/PartsTable';
import { CategoryData, ProductData, PartData, FALLBACK_CATEGORIES, FALLBACK_PRODUCTS, getRealPartsForProduct, deduplicateCategories, cleanText } from '@/lib/data';
import { supabase } from '@/lib/supabase';
import { ChevronLeft, Loader2, X, SearchX, ShoppingBag, Trash2, Send, CheckCircle } from 'lucide-react';

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

    // Cart state
    const [cart, setCart] = useState<{ part: PartData; quantity: number }[]>([]);
    const [inquirySent, setInquirySent] = useState(false);

    // Fetch initial categories and products from Supabase Cloud PostgreSQL
    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                const { data: catData, error: catErr } = await supabase.from('categories').select('*').order('name');

                // Paginate products to bypass Supabase 1000-row default limit
                const PAGE_SIZE = 1000;
                let allProdData: any[] = [];
                let page = 0;
                let keepFetching = true;
                while (keepFetching) {
                    const from = page * PAGE_SIZE;
                    const to = from + PAGE_SIZE - 1;
                    const { data: batch, error } = await supabase
                        .from('products')
                        .select('*')
                        .range(from, to)
                        .order('model');
                    if (error || !batch || batch.length === 0) {
                        keepFetching = false;
                    } else {
                        allProdData = allProdData.concat(batch);
                        if (batch.length < PAGE_SIZE) keepFetching = false;
                        page++;
                    }
                }

                console.log('[Sirman] Categories loaded:', catData?.length);
                console.log('[Sirman] Products loaded:', allProdData.length);

                if (!catErr && catData && catData.length > 0) {
                    const fallbackMap: Record<string, string> = {};
                    FALLBACK_CATEGORIES.forEach(c => { fallbackMap[c.id] = c.icon; });

                    const mappedCats: CategoryData[] = deduplicateCategories(catData.map((c: any) => ({
                        ...c,
                        name: cleanText(c.name),
                        icon: c.icon || fallbackMap[c.id] || `<svg viewBox="0 0 100 100" fill="currentColor"><circle cx="50" cy="50" r="30"/></svg>`
                    })));
                    setCategories(mappedCats);

                    console.log('[Sirman] Normalized Category IDs:', mappedCats.map(c => c.id));
                }

                if (allProdData.length > 0) {
                    const mappedProds: ProductData[] = allProdData.map((p: any) => ({
                        ...p,
                        model: cleanText(p.model),
                        description: cleanText(p.description),
                        category_id: p.category_id || p.categoryId,
                        category_name: cleanText(p.category_name || p.categoryName || p.category),
                        category: cleanText(p.category_name || p.categoryName || p.category),
                        pdf_name: p.pdf_name || p.pdfName,
                        exploded_view_id: p.exploded_view_id || p.explodedViewId,
                        parts_count: p.parts_count !== undefined ? p.parts_count : (p.partsCount || 0),
                        status: p.discontinued ? 'out_of_production' : 'in_production',
                        parts: []
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

    const isUrlInitializedRef = React.useRef(false);

    // 1. Initial State Restoration from URL query parameters on mount/load
    useEffect(() => {
        if (loading || products.length === 0 || isUrlInitializedRef.current) return;
        isUrlInitializedRef.current = true;

        const params = new URLSearchParams(window.location.search);
        const prodCodeOrId = params.get('product') || params.get('p') || params.get('code');
        const catId = params.get('category') || params.get('c');
        const q = params.get('q');
        const ref = params.get('ref');
        const tab = params.get('tab');

        if (tab === 'home' || tab === 'catalog') {
            setActiveTab(tab as 'home' | 'catalog');
        }
        if (q) {
            setSearchQuery(q);
        }
        if (catId && categories.length > 0) {
            const foundCat = categories.find(c => c.id === catId || c.name.toLowerCase() === catId.toLowerCase());
            if (foundCat) setSelectedCategory(foundCat);
        }
        if (prodCodeOrId) {
            const cleanKey = prodCodeOrId.toLowerCase().trim();
            const foundProd = products.find(p =>
                String(p.id).toLowerCase() === cleanKey ||
                p.code.toLowerCase() === cleanKey ||
                (p.pdf_name && p.pdf_name.toLowerCase().replace(/\.pdf$/i, '') === cleanKey)
            );
            if (foundProd) {
                handleSelectProduct(foundProd);
            }
        }
        if (ref) {
            setSelectedRef(ref);
        }
    }, [loading, products.length, categories.length]);

    // 2. Sync state changes to URL search params without triggering page reloads
    useEffect(() => {
        if (loading || !isUrlInitializedRef.current) return;
        const params = new URLSearchParams();

        if (activeTab === 'home') params.set('tab', 'home');
        if (selectedProduct) {
            params.set('product', selectedProduct.code || String(selectedProduct.id));
            if (selectedRef) params.set('ref', selectedRef);
        } else {
            if (selectedCategory) params.set('category', selectedCategory.id);
            if (searchQuery) params.set('q', searchQuery);
        }

        const newQuery = params.toString();
        const newRelativePathQuery = window.location.pathname + (newQuery ? `?${newQuery}` : '');
        if (window.location.search !== (newQuery ? `?${newQuery}` : '')) {
            window.history.replaceState(null, '', newRelativePathQuery);
        }
    }, [selectedProduct, selectedCategory, searchQuery, selectedRef, activeTab, loading]);

    // 3. Listen to browser Back / Forward buttons (popstate)
    useEffect(() => {
        const handlePopState = () => {
            const params = new URLSearchParams(window.location.search);
            const prodCodeOrId = params.get('product') || params.get('p') || params.get('code');
            const catId = params.get('category') || params.get('c');
            const q = params.get('q') || '';
            const ref = params.get('ref') || null;
            const tab = (params.get('tab') as 'home' | 'catalog') || 'catalog';

            setActiveTab(tab);
            setSearchQuery(q);
            setSelectedRef(ref);

            if (catId) {
                const foundCat = categories.find(c => c.id === catId || c.name.toLowerCase() === catId.toLowerCase());
                setSelectedCategory(foundCat || null);
            } else {
                setSelectedCategory(null);
            }

            if (prodCodeOrId) {
                const cleanKey = prodCodeOrId.toLowerCase().trim();
                const foundProd = products.find(p =>
                    String(p.id).toLowerCase() === cleanKey ||
                    p.code.toLowerCase() === cleanKey ||
                    (p.pdf_name && p.pdf_name.toLowerCase().replace(/\.pdf$/i, '') === cleanKey)
                );
                if (foundProd) handleSelectProduct(foundProd);
            } else {
                setSelectedProduct(null);
            }
        };

        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, [products, categories]);

    // Add to cart helper
    const handleAddToCart = (part: PartData) => {
        setCart((prev) => {
            const existingIndex = prev.findIndex((item) => item.part.code === part.code);
            if (existingIndex > -1) {
                const updated = [...prev];
                updated[existingIndex] = {
                    ...updated[existingIndex],
                    quantity: updated[existingIndex].quantity + 1,
                };
                return updated;
            }
            return [...prev, { part, quantity: 1 }];
        });
    };

    // Calculate cart totals
    const cartItemCount = cart.reduce((sum, i) => sum + i.quantity, 0);
    const cartTotalPrice = cart.reduce((sum, i) => sum + (i.part.price || 14.5) * i.quantity, 0);
    const cartCountMap: Record<string, number> = {};
    cart.forEach((i) => {
        cartCountMap[i.part.code] = i.quantity;
    });

    // Helper to fetch parts from hotspot diagram JSON elements if DB parts are empty
    const fetchPartsFromHotspots = async (pdfName?: string, modelName?: string): Promise<PartData[]> => {
        if (!pdfName) return [];
        const cleanPdf = pdfName.replace(/\.pdf$/i, '').replace(/\.png$/i, '').replace(/\.webp$/i, '');
        const cleanSafe = cleanPdf.replace(/ /g, '_');

        const urlsToTry = Array.from(new Set([
            `/hotspots/${cleanPdf}.json`,
            `/hotspots/${cleanSafe}.json`,
            `https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/${cleanPdf}.json`,
            `https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/${cleanSafe}.json`,
        ]));

        for (const url of urlsToTry) {
            try {
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    const elems: any[] = data.clickableElements || [];
                    const refMap = new Map<string, PartData>();

                    elems.forEach((elem: any, idx: number) => {
                        const refId = String(elem.itemId || elem.matchedItemId || idx + 1);
                        if (!refMap.has(refId)) {
                            refMap.set(refId, {
                                id: `hs_${refId}`,
                                code: `P-${refId}`,
                                name: `Part Ref #${refId}`,
                                price: 14.50,
                                stock: 10,
                                ref: refId,
                            });
                        }
                    });

                    if (refMap.size > 0) {
                        return Array.from(refMap.values()).sort((a, b) => {
                            const numA = parseInt(a.ref || '0', 10);
                            const numB = parseInt(b.ref || '0', 10);
                            return (isNaN(numA) || isNaN(numB)) ? (a.ref || '').localeCompare(b.ref || '') : numA - numB;
                        });
                    }
                }
            } catch {
                // try next URL
            }
        }
        return [];
    };

    // Handle selecting a product & fetching its real model-specific spare parts
    const handleSelectProduct = async (prod: ProductData) => {
        const modelParts = getRealPartsForProduct(prod.id, prod.code);
        setSelectedProduct({ ...prod, parts: modelParts });
        setPartsLoading(true);

        try {
            const { data: partsData, error } = await supabase
                .from('parts')
                .select('*')
                .eq('product_id', prod.id)
                .order('code');

            if (!error && partsData && partsData.length > 0) {
                // Deduplicate parts by (code, ref)
                const uniqueMap = new Map<string, any>();
                partsData.forEach((pt: any) => {
                    const key = `${pt.code}_${pt.ref || ''}`;
                    if (!uniqueMap.has(key)) {
                        uniqueMap.set(key, pt);
                    }
                });
                const uniqueParts = Array.from(uniqueMap.values());
                const suggestedMap = new Set(modelParts.filter(p => p.suggested).map(p => p.code));
                const mergedParts = uniqueParts.map((pt: any) => ({
                    ...pt,
                    suggested: suggestedMap.has(pt.code) || pt.suggested
                }));
                setSelectedProduct((prev) => prev ? { ...prev, parts: mergedParts } : null);
            } else {
                // If Supabase parts is empty, fallback to hotspot diagram JSON elements!
                const hsParts = await fetchPartsFromHotspots(prod.pdf_name, prod.model);
                if (hsParts.length > 0) {
                    setSelectedProduct((prev) => prev ? { ...prev, parts: hsParts } : null);
                }
            }
        } catch (err) {
            console.warn("Supabase parts fetch notice:", err);
            const hsParts = await fetchPartsFromHotspots(prod.pdf_name, prod.model);
            if (hsParts.length > 0) {
                setSelectedProduct((prev) => prev ? { ...prev, parts: hsParts } : null);
            }
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
            ? (
                p.category_id === selectedCategory.id ||
                (p as any).category_id === String(selectedCategory.sirman_id) ||
                (p.category_name && p.category_name.toLowerCase().trim() === selectedCategory.name.toLowerCase().trim()) ||
                (p.category && p.category.toLowerCase().trim() === selectedCategory.name.toLowerCase().trim()) ||
                ((p as any).categoryId === selectedCategory.id)
            )
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
        <div className="min-h-screen bg-[#F8FAFC] flex flex-col text-slate-900 font-sans pb-24">
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
                        <div className="flex items-center justify-between bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setSelectedProduct(null)}
                                    className="flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-[#C8102E] bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-xl transition-all cursor-pointer shadow-2xs"
                                >
                                    <ChevronLeft className="w-4 h-4" /> Back to Catalog
                                </button>
                                <div>
                                    <h1 className="text-xl font-extrabold text-slate-900">
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
                                    cartCountMap={cartCountMap}
                                    onAddToCart={handleAddToCart}
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
                                    <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-[#0284C7] px-3.5 py-1.5 rounded-full text-xs font-bold shadow-2xs">
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
                                            className="inline-flex items-center gap-1 text-xs font-bold text-slate-600 hover:text-[#C8102E] transition-colors cursor-pointer"
                                        >
                                            <ChevronLeft className="w-4 h-4" /> Back to Categories
                                        </button>
                                        <span className="text-xs text-slate-500 font-mono font-semibold">
                                            {displayProducts.length} model(s) found
                                        </span>
                                    </div>

                                    {displayProducts.length === 0 ? (
                                        <div className="bg-white border border-slate-200/80 rounded-2xl p-12 text-center shadow-xs">
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

            {/* STICKY CART SUMMARY BAR */}
            {cart.length > 0 && (
                <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-[92%] max-w-2xl bg-slate-900/95 backdrop-blur-md text-white border border-slate-700/80 rounded-2xl p-4 shadow-2xl flex items-center justify-between gap-4 animate-slide-up">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#C8102E] rounded-xl flex items-center justify-center font-bold text-white relative shadow-sm">
                            <ShoppingBag className="w-5 h-5" />
                            <span className="absolute -top-1.5 -right-1.5 bg-white text-[#C8102E] text-[10px] font-extrabold w-5 h-5 rounded-full flex items-center justify-center border-2 border-slate-900">
                                {cartItemCount}
                            </span>
                        </div>
                        <div>
                            <div className="text-xs font-extrabold text-white flex items-center gap-2">
                                Spare Parts Order ({cartItemCount} item{cartItemCount > 1 ? 's' : ''})
                            </div>
                            <div className="text-xs text-slate-400 font-mono">
                                Total: <span className="text-emerald-400 font-extrabold text-sm">€{cartTotalPrice.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setCart([])}
                            className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-xl transition-all cursor-pointer"
                            title="Clear cart"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => {
                                setInquirySent(true);
                                setTimeout(() => setInquirySent(false), 3000);
                            }}
                            className="inline-flex items-center gap-2 bg-[#C8102E] hover:bg-[#A00C24] text-white text-xs font-extrabold px-4 py-2.5 rounded-xl transition-all shadow-md active:scale-95 cursor-pointer"
                        >
                            {inquirySent ? (
                                <>
                                    <CheckCircle className="w-4 h-4 text-emerald-300" />
                                    Inquiry Sent!
                                </>
                            ) : (
                                <>
                                    <Send className="w-4 h-4" />
                                    Send Inquiry
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
