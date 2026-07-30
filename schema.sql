-- ============================================================
-- SIRMAN SERVICE CATALOG - SUPABASE POSTGRESQL SCHEMA
-- ============================================================

-- 1. CATEGORIES TABLE
CREATE TABLE IF NOT EXISTS public.categories (
    id TEXT PRIMARY KEY,
    sirman_id INTEGER,
    name TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    icon TEXT
);

-- 2. PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS public.products (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    model TEXT NOT NULL,
    serial TEXT,
    category_id TEXT REFERENCES public.categories(id) ON DELETE SET NULL,
    category_name TEXT,
    description TEXT,
    pdf_name TEXT,
    exploded_view_id TEXT,
    parts_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. PARTS TABLE
CREATE TABLE IF NOT EXISTS public.parts (
    id BIGSERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES public.products(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(10, 2) DEFAULT 0.00,
    stock INTEGER DEFAULT 0,
    ref TEXT,
    view_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- INDEXES FOR FAST QUERY PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_products_category_id ON public.products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_model ON public.products(model);
CREATE INDEX IF NOT EXISTS idx_products_code ON public.products(code);
CREATE INDEX IF NOT EXISTS idx_parts_product_id ON public.parts(product_id);
CREATE INDEX IF NOT EXISTS idx_parts_code ON public.parts(code);
CREATE INDEX IF NOT EXISTS idx_parts_ref ON public.parts(ref);

-- ENABLE ROW LEVEL SECURITY (RLS) FOR PUBLIC READ ACCESS
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.parts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to categories" ON public.categories FOR SELECT USING (true);
CREATE POLICY "Allow public read access to products" ON public.products FOR SELECT USING (true);
CREATE POLICY "Allow public read access to parts" ON public.parts FOR SELECT USING (true);
