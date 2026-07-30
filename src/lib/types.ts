export type UserRole = 'guest' | 'technician' | 'dealer' | 'admin';

export interface UserProfile {
    id: string;
    email: string;
    role: UserRole;
    full_name?: string;
    company?: string;
    created_at: string;
}

export interface Category {
    id: string;
    sirman_id?: number;
    name: string;
    count: number;
    icon: string;
}

export interface Part {
    id: number | string;
    product_id?: number;
    code: string;
    name: string;
    price: number;
    stock: number;
    ref?: string;
    view_name?: string;
}

export interface Product {
    id: number | string;
    code: string;
    model: string;
    serial: string;
    category_id: string;
    category_name: string;
    category?: string;
    description: string;
    pdf_name?: string;
    pdfName?: string;
    exploded_view_id?: string;
    explodedViewId?: string;
    parts_count?: number;
    partsCount?: number;
    parts?: Part[];
}
