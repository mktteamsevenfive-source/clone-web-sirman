import fallbackCatalog from '../../sirman_catalog_data.json';
import sirmanPartsRaw from '../../sirman_parts.json';

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

// Build map of suggested parts from sirman_parts.json
export const SUGGESTED_PARTS_MAP = new Set<string>();
const rawAllPartsList = (sirmanPartsRaw as any).all_parts || [];

rawAllPartsList.forEach((pt: any) => {
    if (pt.suggested) {
        const key = `${pt._product_id}_${pt.id}`;
        SUGGESTED_PARTS_MAP.add(key);
        if (pt.code) SUGGESTED_PARTS_MAP.add(pt.code);
    }
});

// Helper function to retrieve 100% exact real spare parts for ANY given machine model ID
export function getRealPartsForProduct(productId: number | string, productCode?: string): PartData[] {
    const pIdNum = Number(productId);

    // 1. Search in sirman_parts.json by _product_id
    const matchedRaw = rawAllPartsList.filter((pt: any) => Number(pt._product_id) === pIdNum);
    if (matchedRaw && matchedRaw.length > 0) {
        return matchedRaw.map((pt: any) => ({
            id: pt.id,
            code: pt.id || pt.code,
            name: pt.name,
            price: typeof pt.price === 'string' ? parseFloat(pt.price) : (pt.price || 0),
            stock: pt.dispTot !== undefined ? pt.dispTot : (pt.stock || 10),
            ref: pt.explodedViewRef || pt.ref,
            view_name: pt._view_name || pt.view_name,
            suggested: Boolean(pt.suggested)
        }));
    }

    // 2. Search in sirman_catalog_data.json fallback
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

export const FALLBACK_CATEGORIES: CategoryData[] = (
    Array.isArray(fallbackCatalog.categories)
        ? (fallbackCatalog.categories as any[]).map((c: any) => typeof c === 'string' ? { id: c.toLowerCase().replace(/ /g, '-'), name: c, count: 20, icon: '<svg viewBox="0 0 100 100" fill="currentColor"><circle cx="50" cy="50" r="30"/></svg>' } : c)
        : []
) as CategoryData[];


export const FALLBACK_PRODUCTS: ProductData[] = (fallbackCatalog.products || []).map((p: any) => ({
    ...p,
    category_id: p.category_id || p.categoryId,
    category_name: p.category_name || p.categoryName || p.category,
    pdf_name: p.pdf_name || p.pdfName,
    exploded_view_id: p.exploded_view_id || p.explodedViewId,
    parts_count: p.parts_count !== undefined ? p.parts_count : (p.partsCount || 0),
    status: p.discontinued ? 'out_of_production' : 'in_production',
    parts: getRealPartsForProduct(p.id, p.code)
}));
