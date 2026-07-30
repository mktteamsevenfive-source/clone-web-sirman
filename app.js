/**
 * SIRMAN CATALOG CLONE - Real Scraped Data Application Logic
 * Scraped from Sirman API: 13 Categories, 208 Products, 13,149 Real Spare Parts
 */

// Application State
let SIRMAN_CATEGORIES = [];
let PRODUCTS_DATA = [];
let currentSearchQuery = "";
let currentStatusFilter = "all";
let currentSelectedCategory = null;
let currentActiveProduct = null;
let currentZoomScale = 1.0;
let isDataLoaded = false;

let supabaseClient = null;

// DOM Initialization
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Supabase client inside DOMContentLoaded for correct load order
    if (window.supabase && window.SUPABASE_CONFIG && window.SUPABASE_CONFIG.url) {
        try {
            supabaseClient = window.supabase.createClient(
                window.SUPABASE_CONFIG.url,
                window.SUPABASE_CONFIG.anonKey
            );
            console.log("[Supabase] Client initialized OK");
        } catch (e) {
            console.warn("[Supabase] Init failed:", e);
        }
    } else {
        console.warn("[Supabase] SDK or config not found, will fallback to JSON");
    }

    if (window.lucide) lucide.createIcons();

    loadRealCatalogData();

    try {
        setupEventListeners();
    } catch(e) {
        console.error("[setupEventListeners] Error:", e);
    }

    try {
        setupExplodedViewListeners();
    } catch(e) {
        console.error("[setupExplodedViewListeners] Error:", e);
    }
});

/**
 * Fetch and load real scraped catalog data
 */
async function loadRealCatalogData() {
    showLoadingState(true);

    // Try Supabase Cloud Database first if initialized
    if (supabaseClient) {
        try {
            const { data: catData, error: catErr } = await supabaseClient.from("categories").select("*").order("name");
            const { data: prodData, error: prodErr } = await supabaseClient.from("products").select("*").order("model");

            if (!catErr && !prodErr && catData && prodData) {
                SIRMAN_CATEGORIES = catData;
                PRODUCTS_DATA = prodData.map(p => ({
                    ...p,
                    categoryId: p.category_id || p.categoryId,
                    categoryName: p.category_name || p.categoryName || p.category,
                    category: p.category_name || p.category || p.categoryName,
                    pdfName: p.pdf_name || p.pdfName,
                    explodedViewId: p.exploded_view_id || p.explodedViewId,
                    partsCount: p.parts_count !== undefined ? p.parts_count : (p.partsCount || 0),
                    parts: p.parts || []
                }));

                isDataLoaded = true;
                console.log(`[SUPABASE CLOUD] Loaded ${SIRMAN_CATEGORIES.length} categories, ${PRODUCTS_DATA.length} products.`);
                initSidebarCategories();
                renderCategoryGrid();
                showLoadingState(false);
                return;
            }
        } catch (sbErr) {
            console.warn("Supabase query failed, falling back to local server:", sbErr);
        }
    }

    try {
        const catResp = await fetch("/api/categories");
        if (!catResp.ok) throw new Error(`Failed categories: ${catResp.statusText}`);
        SIRMAN_CATEGORIES = await catResp.json();

        const prodResp = await fetch("/api/products?limit=500");
        if (!prodResp.ok) throw new Error(`Failed products: ${prodResp.statusText}`);
        const prodData = await prodResp.json();
        PRODUCTS_DATA = (prodData.products || []).map(p => ({
            ...p,
            categoryId: p.categoryId || p.category_id,
            categoryName: p.categoryName || p.category_name || p.category,
            category: p.category || p.category_name || p.categoryName,
            pdfName: p.pdfName || p.pdf_name,
            explodedViewId: p.explodedViewId || p.exploded_view_id,
            partsCount: p.partsCount !== undefined ? p.partsCount : (p.parts_count || 0),
            parts: p.parts || []
        }));

        isDataLoaded = true;
        console.log(`Loaded ${SIRMAN_CATEGORIES.length} categories, ${PRODUCTS_DATA.length} products from SQLite DB.`);

        initSidebarCategories();
        renderCategoryGrid();
    } catch (err) {
        console.warn("Falling back to sirman_catalog_data.json:", err);
        try {
            const response = await fetch("./sirman_catalog_data.json");
            const data = await response.json();
            SIRMAN_CATEGORIES = data.categories || [];
            PRODUCTS_DATA = (data.products || []).map(p => ({
                ...p,
                categoryId: p.categoryId || p.category_id,
                categoryName: p.categoryName || p.category_name || p.category,
                category: p.category || p.category_name || p.categoryName,
                pdfName: p.pdfName || p.pdf_name,
                explodedViewId: p.explodedViewId || p.exploded_view_id,
                partsCount: p.partsCount !== undefined ? p.partsCount : (p.parts_count || 0),
                parts: p.parts || []
            }));
            isDataLoaded = true;
            initSidebarCategories();
            renderCategoryGrid();
        } catch (fallbackErr) {
            console.error("Data load error:", fallbackErr);
        }
    } finally {
        showLoadingState(false);
    }
}

function showLoadingState(loading) {
    const grid = document.getElementById("category-grid");
    if (!grid) return;
    if (loading) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 64px 20px;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #E2E8F0; border-top-color: #C8102E; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
                <p style="margin-top: 16px; color: #64748B; font-weight: 500; font-size: 15px;">Loading real Sirman catalog data...</p>
            </div>
            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        `;
    }
}

/**
 * Populate Sidebar Categories list
 */
function initSidebarCategories() {
    const sidebarList = document.getElementById("sidebar-category-list");
    if (!sidebarList) return;

    sidebarList.innerHTML = SIRMAN_CATEGORIES.map(cat => `
        <li class="category-item">
            <a href="#" class="category-link" data-cat-id="${cat.id}">
                ${cat.name}
                <span style="margin-left: auto; font-size: 11px; color: #94A3B8; background: #F1F5F9; padding: 2px 6px; border-radius: 10px;">${cat.count}</span>
            </a>
        </li>
    `).join("");
}

/**
 * Render Main Category Grid Cards
 */
function renderCategoryGrid() {
    const grid = document.getElementById("category-grid");
    if (!grid) return;

    let categoriesToDisplay = SIRMAN_CATEGORIES;

    if (currentSearchQuery.trim() !== "") {
        const query = currentSearchQuery.toLowerCase();
        categoriesToDisplay = SIRMAN_CATEGORIES.filter(cat => 
            cat.name.toLowerCase().includes(query) ||
            PRODUCTS_DATA.some(p => p.categoryId === cat.id && (
                p.code.toLowerCase().includes(query) ||
                p.model.toLowerCase().includes(query) ||
                p.serial.toLowerCase().includes(query) ||
                p.parts.some(pt => pt.code.toLowerCase().includes(query) || pt.name.toLowerCase().includes(query))
            ))
        );
    }

    if (categoriesToDisplay.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 48px; background: white; border-radius: 12px; border: 1px solid #E2E8F0;">
                <i data-lucide="search-x" style="width: 48px; height: 48px; color: #94A3B8; margin-bottom: 12px;"></i>
                <h3 style="font-size: 18px; font-weight: 600; color: #1E293B; margin-bottom: 6px;">No categories or products found</h3>
                <p style="color: #64748B; font-size: 14px;">Try searching for a different part code, serial number, or machine model.</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    grid.innerHTML = categoriesToDisplay.map(cat => `
        <div class="category-card" data-cat-id="${cat.id}" role="button" tabindex="0">
            <span class="category-card-count">${cat.count} models</span>
            <div class="category-icon-wrapper">
                ${cat.icon}
            </div>
            <div class="category-card-name">${cat.name}</div>
        </div>
    `).join("");
}

/**
 * Setup General UI Event Listeners
 */
function setupEventListeners() {
    // Brand Logo Click -> Go to catalog
    document.getElementById("brand-logo").addEventListener("click", () => {
        showCatalogMain();
        hideProductsView();
        hideExplodedView();
        hideFilterBadge();
        renderCategoryGrid();
    });

    // Global Search Input
    const searchInput = document.getElementById("global-search");
    const clearBtn = document.getElementById("clear-search");

    searchInput.addEventListener("input", (e) => {
        currentSearchQuery = e.target.value;
        clearBtn.hidden = currentSearchQuery.trim() === "";
        
        if (currentSearchQuery.trim() !== "") {
            showCatalogMain();
            hideExplodedView();
            showProductsView(null, currentSearchQuery);
            showFilterBadge(`Search: "${currentSearchQuery}"`);
        } else {
            hideProductsView();
            hideFilterBadge();
            renderCategoryGrid();
        }
    });

    clearBtn.addEventListener("click", () => {
        searchInput.value = "";
        currentSearchQuery = "";
        clearBtn.hidden = true;
        hideProductsView();
        hideFilterBadge();
        renderCategoryGrid();
    });

    // Reset Filter Button
    document.getElementById("reset-filter-btn").addEventListener("click", () => {
        searchInput.value = "";
        currentSearchQuery = "";
        clearBtn.hidden = true;
        currentSelectedCategory = null;
        showCatalogMain();
        hideExplodedView();
        hideProductsView();
        hideFilterBadge();
        renderCategoryGrid();
        
        document.querySelectorAll(".category-link").forEach(l => l.classList.remove("active"));
    });

    // Category Card Click
    document.getElementById("category-grid").addEventListener("click", (e) => {
        const card = e.target.closest(".category-card");
        if (card) {
            const catId = card.getAttribute("data-cat-id");
            const categoryObj = SIRMAN_CATEGORIES.find(c => c.id === catId);
            if (categoryObj) {
                currentSelectedCategory = categoryObj;
                showProductsView(categoryObj);
                showFilterBadge(`Category: ${categoryObj.name}`);
            }
        }
    });

    // Sidebar Category Link Click
    document.getElementById("sidebar-category-list").addEventListener("click", (e) => {
        const link = e.target.closest(".category-link");
        if (link) {
            e.preventDefault();
            document.querySelectorAll(".category-link").forEach(l => l.classList.remove("active"));
            link.classList.add("active");

            const catId = link.getAttribute("data-cat-id");
            const categoryObj = SIRMAN_CATEGORIES.find(c => c.id === catId);
            if (categoryObj) {
                currentSelectedCategory = categoryObj;
                showCatalogMain();
                hideExplodedView();
                showProductsView(categoryObj);
                showFilterBadge(`Category: ${categoryObj.name}`);
            }
        }
    });

    // Back to catalog button
    document.getElementById("back-to-catalog").addEventListener("click", () => {
        hideProductsView();
        hideFilterBadge();
        renderCategoryGrid();
    });

    // Status Radio Filters
    document.getElementById("status-filter-group").addEventListener("change", (e) => {
        if (e.target.name === "status-filter") {
            currentStatusFilter = e.target.value;
            if (!document.getElementById("products-view").hidden) {
                renderProductsTable();
            } else {
                renderCategoryGrid();
            }
        }
    });

    // Modal Close
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("product-modal").addEventListener("click", (e) => {
        if (e.target.id === "product-modal") closeModal();
    });
}

/**
 * Display Products Table View
 */
function showProductsView(categoryObj, searchQuery = "") {
    const grid = document.getElementById("category-grid");
    const productsView = document.getElementById("products-view");
    const pageTitle = document.getElementById("page-title");

    grid.hidden = true;
    productsView.hidden = false;

    if (categoryObj) {
        pageTitle.textContent = categoryObj.name;
    } else if (searchQuery) {
        pageTitle.textContent = `Search Results`;
    }

    renderProductsTable();
}

/**
 * Hide Products View & return to category grid
 */
function hideProductsView() {
    document.getElementById("category-grid").hidden = false;
    document.getElementById("products-view").hidden = true;
    document.getElementById("page-title").textContent = "Catalog";
}

/**
 * Render Products Table with Real Scraped Products
 */
function renderProductsTable() {
    const tbody = document.getElementById("products-table-body");
    const countEl = document.getElementById("products-count");

    let filtered = PRODUCTS_DATA;

    if (currentSelectedCategory) {
        filtered = filtered.filter(p => p.categoryId === currentSelectedCategory.id);
    }

    if (currentSearchQuery.trim() !== "") {
        const q = currentSearchQuery.toLowerCase();
        filtered = filtered.filter(p => 
            p.code.toLowerCase().includes(q) ||
            p.model.toLowerCase().includes(q) ||
            p.serial.toLowerCase().includes(q) ||
            p.description.toLowerCase().includes(q) ||
            p.parts.some(pt => pt.code.toLowerCase().includes(q) || pt.name.toLowerCase().includes(q))
        );
    }

    if (currentStatusFilter !== "all") {
        filtered = filtered.filter(p => p.status === currentStatusFilter);
    }

    countEl.textContent = `${filtered.length} model(s) found`;

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 32px; color: #64748B;">
                    No products match the selected criteria.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(p => `
        <tr>
            <td>
                <div class="product-img-thumb" style="display: flex; align-items: center; justify-content: center; background: #F1F5F9;">
                    <i data-lucide="package" style="width: 24px; height: 24px; color: #C8102E;"></i>
                </div>
            </td>
            <td>
                <div style="font-weight: 600; color: #1E293B; cursor: pointer;" onclick="openExplodedViewForProduct('${p.id}')">
                    ${p.model}
                </div>
                <div style="margin-top: 2px;">
                    <span class="part-code-badge">${p.code}</span>
                    <span style="font-size: 11px; color: #64748B; margin-left: 6px;">SN: ${p.serial}</span>
                </div>
            </td>
            <td>${p.category}</td>
            <td style="color: #475569; max-width: 280px;">
                ${p.description}
                ${p.pdfName ? `<div style="font-size: 11px; color: #0284C7; margin-top: 2px;"><i data-lucide="file-text" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle;"></i> ${p.pdfName}</div>` : ''}
            </td>
            <td>
                <span class="status-tag in-production" style="font-size: 12px;">
                    ${p.partsCount} Spare Parts
                </span>
            </td>
            <td>
                <button class="btn-view-details" style="background: #0284C7; color: white; border: none; font-weight: 600;" onclick="openExplodedViewForProduct('${p.id}')">
                    <i data-lucide="scissors" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i>
                    Exploded View
                </button>
            </td>
        </tr>
    `).join("");

    if (window.lucide) lucide.createIcons();
}

/**
 * Filter Badge Controls
 */
function showFilterBadge(text) {
    const badge = document.getElementById("active-filter-badge");
    document.getElementById("filter-badge-text").textContent = text;
    badge.hidden = false;
}

function hideFilterBadge() {
    document.getElementById("active-filter-badge").hidden = true;
}

/**
 * Modal Handling
 */
window.openProductModal = function(productId) {
    const product = PRODUCTS_DATA.find(p => String(p.id) === String(productId) || p.code === productId);
    if (!product) return;

    const modalContent = document.getElementById("modal-content");
    modalContent.innerHTML = `
        <div class="modal-product-header">
            <div class="modal-product-img" style="display: flex; align-items: center; justify-content: center; background: #F8FAFC;">
                <i data-lucide="box" style="width: 56px; height: 56px; color: #C8102E;"></i>
            </div>
            <div class="modal-product-info">
                <span class="part-code-badge" style="font-size: 14px;">${product.code}</span>
                <h2 style="margin-top: 6px; font-size: 22px;">${product.model}</h2>
                <span class="status-tag in-production">In production</span>
            </div>
        </div>

        <p style="color: #475569; font-size: 14px; margin-bottom: 20px;">
            ${product.description}
        </p>

        <div class="modal-spec-grid">
            <div class="spec-item">
                <label>Serial Number</label>
                <span>${product.serial}</span>
            </div>
            <div class="spec-item">
                <label>Category</label>
                <span>${product.category}</span>
            </div>
            <div class="spec-item">
                <label>PDF Diagram</label>
                <span>${product.pdfName || "N/A"}</span>
            </div>
            <div class="spec-item">
                <label>Total Parts</label>
                <span>${product.partsCount} items</span>
            </div>
        </div>
    `;

    document.getElementById("product-modal").hidden = false;
    if (window.lucide) lucide.createIcons();
};

function closeModal() {
    document.getElementById("product-modal").hidden = true;
}

/* ==========================================================================
   EXPLODED VIEW PAGE LOGIC - REAL SCRAPED SPARE PARTS INTEGRATION
   ========================================================================== */

function setupExplodedViewListeners() {
    // Back to Catalog breadcrumb button
    document.getElementById("btn-back-catalog").addEventListener("click", () => {
        hideExplodedView();
        showCatalogMain();
    });

    // View mode toggle buttons (Exploded view only / List only / Both)
    const modeToggle = document.getElementById("view-mode-toggle");
    if (modeToggle) {
        modeToggle.addEventListener("click", (e) => {
            const btn = e.target.closest(".mode-btn");
            if (btn) {
                const mode = btn.getAttribute("data-mode");
                modeToggle.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                const workspace = document.getElementById("exploded-workspace");
                workspace.className = `exploded-workspace mode-${mode}`;
            }
        });
    }

    // Zoom Controls
    const viewport = document.getElementById("diagram-viewport");
    document.getElementById("zoom-in").addEventListener("click", () => {
        currentZoomScale = Math.min(currentZoomScale + 0.25, 2.5);
        viewport.style.transform = `scale(${currentZoomScale})`;
    });

    document.getElementById("zoom-out").addEventListener("click", () => {
        currentZoomScale = Math.max(currentZoomScale - 0.25, 0.6);
        viewport.style.transform = `scale(${currentZoomScale})`;
    });

    document.getElementById("zoom-reset").addEventListener("click", () => {
        currentZoomScale = 1.0;
        viewport.style.transform = `scale(1.0)`;
    });

    document.getElementById("zoom-fit").addEventListener("click", () => {
        currentZoomScale = 1.0;
        viewport.style.transform = `scale(1.0)`;
    });

    // Hotspot group clicks -> Highlight matching parts in real list
    const popover = document.getElementById("part-popover-menu");
    document.querySelectorAll(".hotspot-group").forEach(group => {
        group.addEventListener("click", (e) => {
            e.stopPropagation();
            const refId = group.getAttribute("data-part-id");
            highlightPartsByRef(refId);
        });
    });

    // Click outside popover to close
    document.addEventListener("click", (e) => {
        if (popover && !e.target.closest("#part-popover-menu") && !e.target.closest(".hotspot-group")) {
            popover.hidden = true;
        }
    });

    // Click part item in right list -> Highlight diagram hotspot
    const partsListContainer = document.getElementById("parts-scroll-list");
    if (partsListContainer) {
        partsListContainer.addEventListener("click", (e) => {
            const item = e.target.closest(".part-row-item");
            if (item) {
                const ref = item.getAttribute("data-ref");
                document.querySelectorAll(".part-row-item").forEach(r => r.classList.remove("highlighted"));
                item.classList.add("highlighted");

                document.querySelectorAll(".hotspot-group").forEach(h => {
                    h.classList.remove("active");
                    if (h.getAttribute("data-part-id") === ref) {
                        h.classList.add("active");
                    }
                });
            }
        });
    }
}

/**
 * Open Exploded View Page for a specific Real Product
 */
window.openExplodedViewForProduct = async function(productId) {
    let product = PRODUCTS_DATA.find(p => String(p.id) === String(productId) || p.code === productId);
    if (!product) {
        try {
            const resp = await fetch(`/api/products/${productId}`);
            if (resp.ok) product = await resp.json();
        } catch (e) { console.error(e); }
    }
    if (!product) {
        console.warn(`Product ${productId} not found`);
        return;
    }

    if (!product.parts || product.parts.length === 0) {
        if (supabaseClient) {
            try {
                const { data: partsData } = await supabaseClient.from("parts").select("*").eq("product_id", product.id).order("ref");
                if (partsData && partsData.length > 0) product.parts = partsData;
            } catch (e) { console.error("Supabase parts fetch err:", e); }
        }
        if (!product.parts || product.parts.length === 0) {
            try {
                const resp = await fetch(`/api/products/${product.id}`);
                if (resp.ok) {
                    const fullProd = await resp.json();
                    product.parts = fullProd.parts || [];
                }
            } catch (e) { console.error(e); }
        }
    }

    currentActiveProduct = product;

    const catalogContainer = document.getElementById("catalog-container");
    const explodedPage = document.getElementById("exploded-view-page");
    const titleEl = document.getElementById("exploded-product-title");

    if (catalogContainer) catalogContainer.hidden = true;
    if (explodedPage) explodedPage.hidden = false;

    // Update Product Title & PDF Info
    if (titleEl) {
        titleEl.innerHTML = `
            ${product.model}
            ${product.pdfName ? `<span style="display: inline-flex; align-items: center; gap: 4px; background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; border-radius: 6px; padding: 2px 8px; font-size: 12px; font-weight: 600; margin-left: 10px; vertical-align: middle;"><i data-lucide="file-text" style="width: 13px; height: 13px;"></i> ${product.pdfName}</span>` : ''}
        `;
    }

    // Render Real Spare Parts for this product
    renderRealSparePartsList(product);

    // Render Diagram Image or Fallback Notice
    renderDiagramCanvas(product);

    // Reset zoom
    currentZoomScale = 1.0;

    const popover = document.getElementById("part-popover-menu");
    if (popover) popover.hidden = true;

    if (window.lucide) lucide.createIcons();
};

/**
 * Render Diagram Canvas (Real Image if downloaded, or fallback state)
 */
function renderDiagramCanvas(product) {
    const canvasContainer = document.getElementById("diagram-canvas-container");
    if (!canvasContainer) return;

    if (!product || !product.pdfName) {
        canvasContainer.innerHTML = `
            <div class="diagram-viewport" id="diagram-viewport" style="text-align: center; padding: 60px 20px;">
                <i data-lucide="file-question" style="width: 48px; height: 48px; color: #94A3B8; margin-bottom: 12px;"></i>
                <h3 style="font-size: 16px; font-weight: 600; color: #1E293B;">No Diagram File Specified</h3>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    // Show loading state immediately to clear any initial template artwork
    canvasContainer.innerHTML = `
        <div class="diagram-viewport" id="diagram-viewport" style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 480px; padding: 32px 20px;">
            <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #E2E8F0; border-top-color: #0284C7; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
            <p style="margin-top: 16px; color: #64748B; font-weight: 500; font-size: 14px;">Loading ${product.pdfName} diagram image...</p>
        </div>
    `;

    // Construct Supabase Storage CDN URL
    const supabaseProjectUrl = "https://ofrerwyoasklgsejlbzr.supabase.co";
    const cdnUrl = `${supabaseProjectUrl}/storage/v1/object/public/diagram_images/${product.pdfName}.png`;
    const localImgPath = `./diagram_images/${product.pdfName}.png`;

    const testImg = new Image();
    testImg.onload = function() {
        canvasContainer.innerHTML = `
            <div class="diagram-viewport" id="diagram-viewport" style="display: flex; justify-content: center; align-items: center; min-height: 500px; padding: 24px;">
                <img src="${cdnUrl}" alt="${product.model} Exploded View Diagram" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); background: white;">
            </div>
        `;
    };

    testImg.onerror = function() {
        // Fallback to local image path
        const fallbackImg = new Image();
        fallbackImg.onload = function() {
            canvasContainer.innerHTML = `
                <div class="diagram-viewport" id="diagram-viewport" style="display: flex; justify-content: center; align-items: center; min-height: 500px; padding: 24px;">
                    <img src="${localImgPath}" alt="${product.model} Exploded View Diagram" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); background: white;">
                </div>
            `;
        };
        fallbackImg.onerror = function() {
            canvasContainer.innerHTML = `
                <div class="diagram-viewport" id="diagram-viewport" style="display: flex; align-items: center; justify-content: center; min-height: 480px; padding: 32px 20px;">
                    <div style="background: white; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 32px; max-width: 540px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                        <i data-lucide="image-off" style="width: 44px; height: 44px; color: #94A3B8; margin-bottom: 12px;"></i>
                        <h3 style="font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">Diagram Image Not Available</h3>
                        <p style="font-size: 13px; color: #64748B; margin-bottom: 8px;">
                            File: <code style="background: #F1F5F9; padding: 2px 8px; border-radius: 4px; color: #0284C7; font-weight: 600;">${product.pdfName}.png</code>
                        </p>
                    </div>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        };
        fallbackImg.src = localImgPath;
    };

    testImg.src = cdnUrl;
}                    <h3 style="font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 4px;">Diagram Image Not Downloaded Yet</h3>
                    <p style="font-size: 13px; color: #64748B; margin-bottom: 16px;">
                        File: <code style="background: #F1F5F9; padding: 2px 8px; border-radius: 4px; color: #0284C7; font-weight: 600;">${product.pdfName}</code>
                    </p>
                    <div style="font-size: 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: left; color: #334155; font-family: monospace;">
                        <span style="color: #64748B;"># Run script in terminal to download diagram images:</span><br>
                        <strong style="color: #0284C7;">python download_diagrams.py</strong>
                    </div>
                </div>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    };

    testImg.src = imgPath;
}

/**
 * Backward compatibility alias
 */
window.openExplodedView = function(modelCode) {
    openExplodedViewForProduct(modelCode);
};

/**
 * Render real spare parts into the right pane (#parts-scroll-list)
 */
function renderRealSparePartsList(product) {
    const listContainer = document.getElementById("parts-scroll-list");
    const countTag = document.getElementById("parts-count-tag");

    if (!listContainer) return;

    const parts = product.parts || [];
    if (countTag) {
        countTag.textContent = `${parts.length} items`;
    }

    if (parts.length === 0) {
        listContainer.innerHTML = `
            <div style="padding: 24px; text-align: center; color: #64748B;">
                <i data-lucide="info" style="width: 32px; height: 32px; color: #94A3B8; margin-bottom: 8px;"></i>
                <p style="font-size: 14px;">No spare parts listed for this model yet.</p>
            </div>
        `;
        return;
    }

    listContainer.innerHTML = parts.map((pt, idx) => `
        <div class="part-row-item ${idx === 0 ? 'highlighted' : ''}" data-part-id="${pt.code}" data-ref="${pt.ref}" data-code="${pt.code}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div class="part-row-code">
                    ${pt.ref ? `<span style="display: inline-block; background: #0284C7; color: white; border-radius: 4px; padding: 1px 6px; font-size: 11px; margin-right: 6px; font-weight: 700;">${pt.ref}</span>` : ''}
                    ${pt.code}
                </div>
                ${pt.price > 0 ? `<div style="font-weight: 700; color: #16A34A; font-size: 13px;">€ ${pt.price.toFixed(2)}</div>` : ''}
            </div>
            <div class="part-row-desc" style="margin-top: 4px;">${pt.name}</div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; font-size: 11px; color: #64748B;">
                <span>${pt.stock > 0 ? `<span style="color: #16A34A; font-weight: 600;">In Stock (${pt.stock})</span>` : '<span style="color: #94A3B8;">Check Availability</span>'}</span>
                ${pt.view_name ? `<span style="font-size: 10px; color: #94A3B8;">${pt.view_name}</span>` : ''}
            </div>
        </div>
    `).join("");
}

/**
 * Highlight parts by diagram reference number
 */
function highlightPartsByRef(refId) {
    const listContainer = document.getElementById("parts-scroll-list");
    if (!listContainer || !currentActiveProduct) return;

    let matchedRow = null;
    document.querySelectorAll(".part-row-item").forEach(row => {
        const rowRef = row.getAttribute("data-ref");
        const rowCode = row.getAttribute("data-code");
        if (rowRef === refId || rowCode === refId) {
            row.classList.add("highlighted");
            if (!matchedRow) matchedRow = row;
        } else {
            row.classList.remove("highlighted");
        }
    });

    if (matchedRow) {
        matchedRow.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}

function hideExplodedView() {
    const catalogContainer = document.getElementById("catalog-container");
    const explodedPage = document.getElementById("exploded-view-page");

    if (explodedPage) explodedPage.hidden = true;
    if (catalogContainer) catalogContainer.hidden = false;
}

function showCatalogMain() {
    const catalogContainer = document.getElementById("catalog-container");
    const explodedPage = document.getElementById("exploded-view-page");

    if (explodedPage) explodedPage.hidden = true;
    if (catalogContainer) catalogContainer.hidden = false;
}
