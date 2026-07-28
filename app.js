/**
 * SIRMAN CATALOG CLONE - Application Logic
 * Categories sourced from: api-service.sirman.com/service-dwh/categories
 * Scraped: 2026-07-29
 */

// 1. Real Category Data from Sirman API
// Real category data from api-service.sirman.com/service-dwh/categories (1282 total items)
const SIRMAN_CATEGORIES = [
    {
        id: "microwaves-ovens",
        sirman_id: 18,
        name: "Microwaves ovens",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M15 25 H85 V75 H15 Z M22 32 H65 V68 H22 Z M72 32 H78 V36 H72 Z M72 42 H78 V46 H72 Z M75 58 A5 5 0 1 0 75 68 A5 5 0 1 0 75 58 Z M28 42 Q 35 35 42 42 T 56 42" stroke="currentColor" stroke-width="3" fill="none"/><path d="M28 54 Q 35 47 42 54 T 56 54" stroke="currentColor" stroke-width="3" fill="none"/></svg>`,
        count: 4,
        subcategories: ["PANASONIC 60HZ","PANASONIC","MINNEAPOLIS","TOPWAVE"]
    },
    {
        id: "snack-pizza",
        sirman_id: 2,
        name: "Snack and pizza",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M20 70 L50 25 L80 70 Z M20 74 H80 V78 H20 Z M38 52 A5 5 0 1 0 38 62 A5 5 0 1 0 38 52 Z M58 45 A4 4 0 1 0 58 53 A4 4 0 1 0 58 45 Z M52 60 A4 4 0 1 0 52 68 A4 4 0 1 0 52 60 Z"/></svg>`,
        count: 27,
        subcategories: ["HOT DOG / BREAD WARMERS 60HZ","PIZZA KNEADERS 60HZ","PIZZA KNEADERS","HOT DOG / BREAD WARMERS","WAFFLE IRON","CONTACT GRILLS","PANINI GRILL"]
    },
    {
        id: "consumables-accessories",
        sirman_id: 27,
        name: "Consumables and accessories",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M50 20 A30 30 0 1 0 50 80 A30 30 0 1 0 50 20 Z M50 35 A15 15 0 1 1 50 65 A15 15 0 1 1 50 35 Z"/><circle cx="75" cy="45" r="10"/></svg>`,
        count: 13,
        subcategories: ["ACCESSORIES","BAGS FOR VACUUM MACHINES","ACCESSORIES FOR SLICERS","ACCESSORIES FOR MEAT MACHINES"]
    },
    {
        id: "laundry",
        sirman_id: 28,
        name: "Laundry",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M22 20 H78 V80 H22 Z M50 35 A18 18 0 1 0 50 71 A18 18 0 1 0 50 35 Z M50 43 A10 10 0 1 1 50 63 A10 10 0 1 1 50 43 Z"/><circle cx="32" cy="28" r="3"/><circle cx="42" cy="28" r="3"/></svg>`,
        count: 3,
        subcategories: ["WASHING MACHINE","DRYER","MANGLE"]
    },
    {
        id: "food-processors",
        sirman_id: 3,
        name: "Food processors",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M50 25 C30 25 18 42 18 55 H82 C82 42 70 25 50 25 Z M47 15 H53 V25 H47 Z M15 58 H85 V64 H15 Z M22 68 H78 V72 H22 Z"/></svg>`,
        count: 30,
        subcategories: ["CUTTERS","VEGETABLE CUTTERS","PLANETARY MIXERS","SPIRAL MIXERS","DOUGH LAMINATORS","TUMBLERS"]
    },
    {
        id: "cooking-machines",
        sirman_id: 31,
        name: "Cooking machines",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M40 15 C40 15 42 22 38 27 M50 12 C50 12 52 20 48 26 M60 15 C60 15 62 22 58 27" stroke="currentColor" stroke-width="4" stroke-linecap="round" fill="none"/><path d="M20 40 H80 V46 H20 Z M24 48 H76 V65 C76 73.3 69.3 80 61 80 H39 C30.7 80 24 73.3 24 65 Z M15 48 H21 V56 H15 Z M79 48 H85 V56 H79 Z"/></svg>`,
        count: 11,
        subcategories: ["SOFTCOOKER","SOFTCOOKER CONTAINER","BBQ","SALAMANDERS","INDUCTION HOBS","CONVECTION OVENS","EASYSOFT","CW"]
    },
    {
        id: "bar-machines",
        sirman_id: 4,
        name: "Bar machines",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M70,30 H25 C22.2,30 20,32.2 20,35 V60 C20,68.3 26.7,75 35,75 H50 C58.3,75 65,68.3 65,60 V55 H70 C76.6,55 82,49.6 82,43 C82,35.8 76.6,30 70,30 Z M70,47 H65 V38 H70 C72.8,38 75,40.2 75,43 C75,45.8 72.8,47 70,47 Z M15,82 H75 V88 H15 Z"/></svg>`,
        count: 15,
        subcategories: ["ICE CRUSHERS","BLENDERS","CITRUS JUICERS","DRINK MIXERS","ICE SPAGHETTI","SLOW JUICER","MILKSHAKER 60HZ","DISPLAY CABINETS"]
    },
    {
        id: "packaging-machines",
        sirman_id: 5,
        name: "Packaging machines",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M25 30 H75 V80 H25 Z M35 20 H65 V28 H35 Z M35 45 A6 6 0 1 0 35 57 A6 6 0 1 0 35 45 Z M55 45 A6 6 0 1 0 55 57 A6 6 0 1 0 55 45 Z M45 62 A6 6 0 1 0 45 74 A6 6 0 1 0 45 62 Z"/></svg>`,
        count: 9,
        subcategories: ["VACUUM PACKAGING MACHINES","WRAPPING MACHINES","SEALERS","THERMOSEALERS","VACUUM PACKAGING MACHINES 60HZ"]
    },
    {
        id: "scales",
        sirman_id: 51,
        name: "Scales",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M35 25 H65 L78 78 H22 Z"/><text x="32" y="60" font-family="Outfit, sans-serif" font-size="22" font-weight="800" fill="#FFFFFF">KG</text></svg>`,
        count: 15,
        subcategories: ["CICLONE 20","CICLONE 28","CICLONE 36","VORTEX 43","VORTEX 55","VORTEX 75","STORM","KIRO","MINNEAPOLIS"]
    },
    {
        id: "ozone-generators",
        sirman_id: 52,
        name: "Ozone generators",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><text x="15" y="68" font-family="Outfit, sans-serif" font-size="52" font-weight="800">O</text><text x="56" y="76" font-family="Outfit, sans-serif" font-size="34" font-weight="800">3</text><circle cx="80" cy="35" r="2"/><circle cx="88" cy="45" r="3"/><circle cx="75" cy="55" r="1.5"/></svg>`,
        count: 7,
        subcategories: ["O3 TOWER","O3 PORT","PP EXPO","PPJ 6","PPJ 10","PPJ 20","PP ECO"]
    },
    {
        id: "slicers",
        sirman_id: 6,
        name: "Slicers",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M75 22 A28 28 0 0 0 47 50 A28 28 0 0 0 75 78 V22 Z M60 22 A28 28 0 0 0 32 50 A28 28 0 0 0 60 78 V22 Z M45 22 A28 28 0 0 0 17 50 A28 28 0 0 0 45 78 V22 Z"/></svg>`,
        count: 65,
        subcategories: ["AGATA","TOPAZ","PERLA","MINI","SELCE","GALILEO EVO","CANOVA","PALLADIO","GALILEO","SMART","MIRRA","GEMMA","GIOTTO","LEONARDO","MANTEGNA","RAFFAELLO","TIZIANO EVO"]
    },
    {
        id: "dishwashers",
        sirman_id: 61,
        name: "Dishwashers",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M70 30 H25 C22.2 30 20 32.2 20 35 V60 C20 68.3 26.7 75 35 75 H50 C58.3 75 65 68.3 65 60 V55 H70 C76.6 55 82 49.6 82 43 C82 35.8 76.6 30 70 30 Z M70 47 H65 V38 H70 C72.8 38 75 40.2 75 43 C75 45.8 72.8 47 70 47 Z M15 82 H75 V88 H15 Z"/><path d="M25 22 Q 45 15 65 22" stroke="currentColor" stroke-width="3" fill="none"/></svg>`,
        count: 2,
        subcategories: ["HP WASH","OSMO3"]
    },
    {
        id: "meat-processors",
        sirman_id: 7,
        name: "Meat processors",
        icon: `<svg viewBox="0 0 100 100" fill="currentColor"><path d="M35 25 C20 25 15 40 22 58 C28 73 50 82 72 75 C85 70 88 52 78 38 C68 24 50 25 35 25 Z M42 42 A8 8 0 1 1 42 58 A8 8 0 1 1 42 42 Z"/></svg>`,
        count: 28,
        subcategories: ["MEAT GRINDERS","SAUSAGE STUFFERS","MEAT MIXERS","BONE SAWS","KNIFE STERILIZERS","TENDERISER","HORIZONTAL CUTTER","HAMBURGER PRESSES","HAMBURGER ATTACHMENTS"]
    }
];

// Real machine models from Sirman API subcategories
const MOCK_PRODUCTS = [
    /* Bar machines - Citrus Juicers */
    { code: "APOLLO-2015", serial: "SN-2015-0901", model: "APOLLO - from 2015.01", category: "Bar machines", categoryId: "bar-machines", description: "Citrus juicer with lever and stainless steel bowl", status: "in_production", hasExplodedView: true, specs: { power: "150W", speed: "320 RPM", weight: "3.8 kg", origin: "Italy" } },
    { code: "SIR-BM-ICE-34", serial: "SN-2024-3401", model: "ATLANTIS Ice Crusher", category: "Bar machines", categoryId: "bar-machines", description: "Heavy-duty bar ice crusher for cocktails and beverages", status: "in_production", specs: { power: "350W", capacity: "120 kg/h", weight: "8.2 kg", origin: "Italy" } },
    { code: "SIR-BM-BL-36", serial: "SN-2024-3601", model: "PRIMO Blender", category: "Bar machines", categoryId: "bar-machines", description: "High-speed commercial blender with 1.5L Tritan jug", status: "in_production", specs: { power: "750W", speed: "18000 RPM", weight: "4.5 kg", origin: "Italy" } },
    { code: "SIR-BM-SJ-881", serial: "SN-2023-8811", model: "SLOW JUICER", category: "Bar machines", categoryId: "bar-machines", description: "Cold press slow juicer for maximum juice extraction", status: "in_production", specs: { power: "150W", rpm: "60 RPM", weight: "5.2 kg", origin: "Italy" } },
    /* Slicers */
    { code: "SIR-SL-GALILEO", serial: "SN-2024-1001", model: "GALILEO EVO", category: "Slicers", categoryId: "slicers", description: "Premium gravity feed slicer with precision blade adjustment", status: "in_production", specs: { blade: "300 mm", power: "210W", cutThickness: "0-15 mm", origin: "Italy" } },
    { code: "SIR-SL-AGATA-1", serial: "SN-2024-0101", model: "AGATA", category: "Slicers", categoryId: "slicers", description: "High-performance slicer for delicatessen and butchers", status: "in_production", specs: { blade: "250 mm", power: "185W", cutThickness: "0-13 mm", origin: "Italy" } },
    { code: "SIR-SL-TOPAZ-11", serial: "SN-2022-1101", model: "TOPAZ", category: "Slicers", categoryId: "slicers", description: "Entry-level slicer for deli counters and small shops", status: "in_production", specs: { blade: "220 mm", power: "150W", cutThickness: "0-10 mm", origin: "Italy" } },
    { code: "SIR-SL-CANOVA-LG", serial: "SN-2018-0091", model: "CANOVA 60HZ", category: "Slicers", categoryId: "slicers", description: "60Hz export model slicer for international markets", status: "out_of_production", specs: { blade: "300 mm", power: "210W", statusNotice: "Legacy model - parts available", origin: "Italy" } },
    { code: "SIR-SL-MIRRA", serial: "SN-2024-2201", model: "MIRRA", category: "Slicers", categoryId: "slicers", description: "Manual gravity slicer with ergonomic ring guard", status: "in_production", specs: { blade: "195 mm", power: "135W", cutThickness: "0-10 mm", origin: "Italy" } },
    /* Meat processors */
    { code: "SIR-MP-TC22", serial: "SN-2024-9981", model: "TC 22 Meat Grinder", category: "Meat processors", categoryId: "meat-processors", description: "Professional meat mincer, neck system Enterprise", status: "in_production", specs: { power: "1100W", output: "300 kg/h", weight: "31 kg", origin: "Italy" } },
    { code: "SIR-MP-TENDER", serial: "SN-2024-6321", model: "TENDERISER", category: "Meat processors", categoryId: "meat-processors", description: "Automatic meat tenderiser for steaks and escalopes", status: "in_production", specs: { power: "370W", width: "205 mm", weight: "16 kg", origin: "Italy" } },
    { code: "SIR-MP-SAW-44", serial: "SN-2023-4401", model: "BONE SAW CS 710", category: "Meat processors", categoryId: "meat-processors", description: "Bandsaw for cutting frozen meat and bones in butcher shops", status: "in_production", specs: { power: "750W", blade: "1810 mm", weight: "45 kg", origin: "Italy" } },
    /* Cooking machines */
    { code: "SIR-CK-SOFTCOOKER", serial: "SN-2024-6751", model: "SOFTCOOKER Y09", category: "Cooking machines", categoryId: "cooking-machines", description: "Precision temperature water bath with Wi-Fi, 50L tank", status: "in_production", specs: { power: "2000W", tempRange: "24°C - 99°C", tankCapacity: "50L", origin: "Italy" } },
    { code: "SIR-CK-EASYSOFT", serial: "SN-2024-9461", model: "EASYSOFT", category: "Cooking machines", categoryId: "cooking-machines", description: "Compact sous vide cooker for restaurants and catering", status: "in_production", specs: { power: "1200W", tempRange: "25°C - 95°C", tankCapacity: "22L", origin: "Italy" } },
    { code: "SIR-CK-CONVEC-619", serial: "SN-2021-6191", model: "CONVECTION OVEN", category: "Cooking machines", categoryId: "cooking-machines", description: "Electric convection oven with steam injection system", status: "in_production", specs: { power: "3400W", maxTemp: "300°C", capacity: "5x GN 1/1", origin: "Italy" } },
    /* Packaging */
    { code: "SIR-PK-VACUUM-692", serial: "SN-2024-6921", model: "W8 40 Vacuum Sealer", category: "Packaging machines", categoryId: "packaging-machines", description: "Chamber vacuum sealer with Busch 20m³/h pump", status: "in_production", specs: { sealBar: "410 mm", pump: "Busch 20 m³/h", power: "750W", origin: "Italy" } },
    { code: "SIR-PK-THERMOS-716", serial: "SN-2023-7161", model: "THERMOSEALER", category: "Packaging machines", categoryId: "packaging-machines", description: "Automatic thermosealer for trays and containers", status: "in_production", specs: { power: "1500W", maxTraySize: "400x300 mm", weight: "35 kg", origin: "Italy" } },
    /* Scales */
    { code: "SIR-SC-CICLONE20", serial: "SN-2024-5961", model: "CICLONE 20", category: "Scales", categoryId: "scales", description: "Price computing scale 20kg, dual LCD display, rechargeable", status: "in_production", specs: { capacity: "20 kg", precision: "5 g", plateSize: "250x200 mm", origin: "Italy" } },
    { code: "SIR-SC-VORTEX55", serial: "SN-2024-1904", model: "VORTEX 55", category: "Scales", categoryId: "scales", description: "High-capacity scale 55kg for supermarkets and retail", status: "in_production", specs: { capacity: "55 kg", precision: "10 g", plateSize: "350x280 mm", origin: "Italy" } },
    /* Ozone generators */
    { code: "SIR-OZ-TOWER", serial: "SN-2024-1389", model: "O3 TOWER", category: "Ozone generators", categoryId: "ozone-generators", description: "Freestanding ozone generator for large kitchen areas", status: "in_production", specs: { ozoneOutput: "12 g/h", coverage: "300 m³", weight: "8.5 kg", origin: "Italy" } },
    { code: "SIR-OZ-PORT", serial: "SN-2024-1390", model: "O3 PORT", category: "Ozone generators", categoryId: "ozone-generators", description: "Portable ozone generator for food storage rooms", status: "in_production", specs: { ozoneOutput: "5 g/h", coverage: "120 m³", weight: "2.1 kg", origin: "Italy" } },
    /* Snack & pizza */
    { code: "SIR-SP-PIZZA", serial: "SN-2024-5501", model: "STROMBOLI Pizza Oven", category: "Snack and pizza", categoryId: "snack-pizza", description: "Electric single-deck pizza oven with refractory stone floor", status: "in_production", specs: { power: "3000W", maxTemp: "450°C", chamberSize: "410x360 mm", origin: "Italy" } },
    /* Dishwashers */
    { code: "SIR-DW-HPWASH", serial: "SN-2024-1491", model: "HP WASH", category: "Dishwashers", categoryId: "dishwashers", description: "High-pressure undercounter glasswasher for bars and cafes", status: "in_production", specs: { power: "2500W", capacity: "720 racks/h", washTemp: "60°C", origin: "Italy" } },
    { code: "SIR-DW-OSMO3", serial: "SN-2023-1499", model: "OSMO3", category: "Dishwashers", categoryId: "dishwashers", description: "Ozone-based dishwasher with zero chemical rinse system", status: "in_production", specs: { power: "1800W", capacity: "360 racks/h", technology: "O3 Ozone", origin: "Italy" } }
];

// App State
let currentSearchQuery = "";
let currentStatusFilter = "all";
let currentSelectedCategory = null;
let currentZoomScale = 1.0;

// DOM Elements
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    initSidebarCategories();
    renderCategoryGrid();
    setupEventListeners();
    setupExplodedViewListeners();
});

// Populate Sidebar Categories
function initSidebarCategories() {
    const sidebarList = document.getElementById("sidebar-category-list");
    if (!sidebarList) return;

    sidebarList.innerHTML = SIRMAN_CATEGORIES.map(cat => `
        <li class="category-item">
            <a href="#" class="category-link" data-cat-id="${cat.id}">
                ${cat.name}
            </a>
        </li>
    `).join("");
}

// Render Category Grid Cards
function renderCategoryGrid() {
    const grid = document.getElementById("category-grid");
    if (!grid) return;

    let categoriesToDisplay = SIRMAN_CATEGORIES;

    // Filter by search query if applicable
    if (currentSearchQuery.trim() !== "") {
        const query = currentSearchQuery.toLowerCase();
        categoriesToDisplay = SIRMAN_CATEGORIES.filter(cat => 
            cat.name.toLowerCase().includes(query) ||
            MOCK_PRODUCTS.some(p => p.categoryId === cat.id && (
                p.code.toLowerCase().includes(query) ||
                p.serial.toLowerCase().includes(query) ||
                p.model.toLowerCase().includes(query) ||
                p.description.toLowerCase().includes(query)
            ))
        );
    }

    if (categoriesToDisplay.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 48px; background: white; border-radius: 12px; border: 1px solid #E2E8F0;">
                <i data-lucide="search-x" style="width: 48px; height: 48px; color: #94A3B8; margin-bottom: 12px;"></i>
                <h3 style="font-size: 18px; font-weight: 600; color: #1E293B; margin-bottom: 6px;">No categories or products found</h3>
                <p style="color: #64748B; font-size: 14px;">Try searching for a different part code, serial number, or machine category.</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    grid.innerHTML = categoriesToDisplay.map(cat => `
        <div class="category-card" data-cat-id="${cat.id}" role="button" tabindex="0">
            <span class="category-card-count">${cat.count}</span>
            <div class="category-icon-wrapper">
                ${cat.icon}
            </div>
            <div class="category-card-name">${cat.name}</div>
        </div>
    `).join("");
}

// Event Listeners setup
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

// Display Products Table View
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

// Hide Products View & return to catalog grid
function hideProductsView() {
    document.getElementById("category-grid").hidden = false;
    document.getElementById("products-view").hidden = true;
    document.getElementById("page-title").textContent = "Catalog";
}

// Render Products Table
function renderProductsTable() {
    const tbody = document.getElementById("products-table-body");
    const countEl = document.getElementById("products-count");

    let filtered = MOCK_PRODUCTS;

    if (currentSelectedCategory) {
        filtered = filtered.filter(p => p.categoryId === currentSelectedCategory.id);
    }

    if (currentSearchQuery.trim() !== "") {
        const q = currentSearchQuery.toLowerCase();
        filtered = filtered.filter(p => 
            p.code.toLowerCase().includes(q) ||
            p.serial.toLowerCase().includes(q) ||
            p.model.toLowerCase().includes(q) ||
            p.description.toLowerCase().includes(q)
        );
    }

    if (currentStatusFilter !== "all") {
        filtered = filtered.filter(p => p.status === currentStatusFilter);
    }

    countEl.textContent = `${filtered.length} item(s) found`;

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
                    <i data-lucide="package" style="width: 24px; height: 24px; color: #64748B;"></i>
                </div>
            </td>
            <td>
                <div style="font-weight: 600; color: #1E293B; cursor: pointer;" onclick="openExplodedView('${p.code}')">
                    ${p.model}
                </div>
                <div style="margin-top: 2px;">
                    <span class="part-code-badge">${p.code}</span>
                    <span style="font-size: 11px; color: #64748B; margin-left: 6px;">SN: ${p.serial}</span>
                </div>
            </td>
            <td>${p.category}</td>
            <td style="color: #475569; max-width: 280px;">${p.description}</td>
            <td>
                <span class="status-tag ${p.status === 'in_production' ? 'in-production' : 'out-of-production'}">
                    ${p.status === 'in_production' ? 'In production' : 'Out of production'}
                </span>
            </td>
            <td>
                <button class="btn-view-details" style="background: #0284C7; color: white; border: none; font-weight: 600;" onclick="openExplodedView('${p.code}')">
                    <i data-lucide="scissors" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i>
                    Exploded View
                </button>
            </td>
        </tr>
    `).join("");

    if (window.lucide) lucide.createIcons();
}

// Show/Hide Filter Badges
function showFilterBadge(text) {
    const badge = document.getElementById("active-filter-badge");
    document.getElementById("filter-badge-text").textContent = text;
    badge.hidden = false;
}

function hideFilterBadge() {
    document.getElementById("active-filter-badge").hidden = true;
}

// Modal handling
window.openProductModal = function(code) {
    const product = MOCK_PRODUCTS.find(p => p.code === code);
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
                <span class="status-tag ${product.status === 'in_production' ? 'in-production' : 'out-of-production'}">
                    ${product.status === 'in_production' ? 'In production' : 'Out of production'}
                </span>
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
            ${Object.entries(product.specs).map(([key, val]) => `
                <div class="spec-item">
                    <label>${key.replace(/([A-Z])/g, ' $1').toUpperCase()}</label>
                    <span>${val}</span>
                </div>
            `).join("")}
        </div>
    `;

    document.getElementById("product-modal").hidden = false;
    if (window.lucide) lucide.createIcons();
};

function closeModal() {
    document.getElementById("product-modal").hidden = true;
}

/* ==========================================================================
   EXPLODED VIEW PAGE LOGIC
   ========================================================================== */

function setupExplodedViewListeners() {
    // Back to Catalog breadcrumb button
    document.getElementById("btn-back-catalog").addEventListener("click", () => {
        hideExplodedView();
        showCatalogMain();
    });

    // View mode toggle buttons (Exploded view only / List only / Both)
    const modeToggle = document.getElementById("view-mode-toggle");
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

    // Hotspot group clicks -> Show Part Popover Menu
    const popover = document.getElementById("part-popover-menu");
    document.querySelectorAll(".hotspot-group").forEach(group => {
        group.addEventListener("click", (e) => {
            e.stopPropagation();
            const partId = group.getAttribute("data-part-id");
            
            // Highlight part in right list
            document.querySelectorAll(".part-row-item").forEach(row => {
                row.classList.remove("highlighted");
                if (row.getAttribute("data-part-id") === partId) {
                    row.classList.add("highlighted");
                    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });

            // Toggle popover menu
            popover.hidden = false;
        });
    });

    // Click outside popover to close
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#part-popover-menu") && !e.target.closest(".hotspot-group")) {
            popover.hidden = true;
        }
    });

    // Click part item in right list -> Highlight diagram hotspot
    document.getElementById("parts-scroll-list").addEventListener("click", (e) => {
        const item = e.target.closest(".part-row-item");
        if (item) {
            const partId = item.getAttribute("data-part-id");
            document.querySelectorAll(".part-row-item").forEach(r => r.classList.remove("highlighted"));
            item.classList.add("highlighted");

            document.querySelectorAll(".hotspot-group").forEach(h => {
                h.classList.remove("active");
                if (h.getAttribute("data-part-id") === partId) {
                    h.classList.add("active");
                }
            });
        }
    });
}

// Navigation helpers
window.openExplodedView = function(modelCode) {
    const catalogContainer = document.getElementById("catalog-container");
    const explodedPage = document.getElementById("exploded-view-page");

    if (catalogContainer) catalogContainer.hidden = true;
    if (explodedPage) explodedPage.hidden = false;

    // Reset zoom
    currentZoomScale = 1.0;
    document.getElementById("diagram-viewport").style.transform = `scale(1.0)`;
    document.getElementById("part-popover-menu").hidden = true;

    if (window.lucide) lucide.createIcons();
};

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
