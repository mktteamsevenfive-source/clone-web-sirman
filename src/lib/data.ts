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

// Helper function to retrieve spare parts (parts are fetched live from Supabase 'parts' table)
export function getRealPartsForProduct(productId: number | string, productCode?: string): PartData[] {
    return [];
}

// Helper to normalize and deduplicate categories by lowercase name
export function deduplicateCategories(rawCategories: CategoryData[]): CategoryData[] {
    const map = new Map<string, CategoryData>();

    rawCategories.forEach((cat) => {
        const normKey = cat.name.trim().toLowerCase();
        if (map.has(normKey)) {
            const existing = map.get(normKey)!;
            const newName = cat.name[0] === cat.name[0].toUpperCase() ? cat.name : existing.name;
            map.set(normKey, {
                ...existing,
                name: newName,
                count: Math.max(existing.count, cat.count),
                icon: existing.icon && !existing.icon.includes('circle cx="50"') ? existing.icon : (cat.icon || existing.icon),
            });
        } else {
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

export const FALLBACK_CATEGORIES: CategoryData[] = [];
export const FALLBACK_PRODUCTS: ProductData[] = [];
