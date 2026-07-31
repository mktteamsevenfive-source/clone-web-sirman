import fallbackCatalog from '../../sirman_catalog_data.json';

export interface CategoryData {
    id: string;
    sirman_id: number;
    name: string;
    count: number;
    icon: string;
}

export interface PartData {
    id: number | string;
    code: string;
    name: string;
    price: number;
    stock: number;
    ref?: string;
    view_name?: string;
    suggested?: boolean;
}

export interface ProductData {
    id: number | string;
    code: string;
    model: string;
    serial: string;
    category_id: string;
    category_name: string;
    category?: string;
    description: string;
    pdf_name?: string;
    exploded_view_id?: string;
    parts_count?: number;
    parts?: PartData[];
    status?: 'in_production' | 'out_of_production';
}

export const SUGGESTED_PARTS_MAP = new Set<string>();

// Helper function to retrieve fallback spare parts for machine model ID
export function getRealPartsForProduct(productId: number | string, productCode?: string): PartData[] {
    const pIdNum = Number(productId);

    // Search in sirman_catalog_data.json fallback
    const fallbackProds = (fallbackCatalog.products || []) as any[];
    const fallbackProd = fallbackProds.find(
        (p) => Number(p.id) === pIdNum || p.code === productCode
    );

    if (fallbackProd && fallbackProd.parts && fallbackProd.parts.length > 0) {
        return fallbackProd.parts.map((pt: any) => ({
            ...pt,
            suggested: pt.suggested || SUGGESTED_PARTS_MAP.has(`${pIdNum}_${pt.code}`) || SUGGESTED_PARTS_MAP.has(pt.code)
        }));
    }

    return [];
}

// Helper to normalize and deduplicate categories by lowercase name
export function deduplicateCategories(rawCategories: CategoryData[]): CategoryData[] {
    const map = new Map<string, CategoryData>();

    rawCategories.forEach((cat) => {
        const normKey = cat.name.trim().toLowerCase();
        if (map.has(normKey)) {
            const existing = map.get(normKey)!;
            // Prefer Title Case or larger count
            const newName = cat.name[0] === cat.name[0].toUpperCase() ? cat.name : existing.name;
            map.set(normKey, {
                ...existing,
                name: newName,
                count: Math.max(existing.count, cat.count),
                icon: existing.icon && !existing.icon.includes('circle cx="50"') ? existing.icon : (cat.icon || existing.icon),
            });
        } else {
            // Capitalize properly if needed
            const formattedName = cat.name.charAt(0).toUpperCase() + cat.name.slice(1);
            map.set(normKey, {
                ...cat,
                name: formattedName,
                id: cat.id || normKey.replace(/ /g, '-'),
            });
        }
    });

    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
}

export const FALLBACK_CATEGORIES: CategoryData[] = deduplicateCategories(
    Array.isArray(fallbackCatalog.categories)
        ? (fallbackCatalog.categories as any[]).map((c: any) =>
              typeof c === 'string'
                  ? { id: c.toLowerCase().replace(/ /g, '-'), name: c, count: 20, icon: '<svg viewBox="0 0 100 100" fill="currentColor"><circle cx="50" cy="50" r="30"/></svg>' }
                  : c
          )
        : []
);


// Helper to sanitize HTML tags and decode entities in scraped text fields
export function cleanText(str?: string | null): string {
    if (!str) return '';
    let cleaned = String(str);

    // 1. Strip HTML tags
    cleaned = cleaned.replace(/<[^>]*>/gi, ' ');

    // 2. Decode common HTML entities
    cleaned = cleaned
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');

    // 3. Normalize multiple spaces
    return cleaned.replace(/\s+/g, ' ').trim();
}

export const FALLBACK_PRODUCTS: ProductData[] = (fallbackCatalog.products || []).map((p: any) => ({
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
    parts: getRealPartsForProduct(p.id, p.code)
}));
