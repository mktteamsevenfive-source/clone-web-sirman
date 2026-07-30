import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://ofrerwyoasklgsejlbzr.supabase.co";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9mcmVyd3lvYXNrbGdzZWpsYnpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY2NTUsImV4cCI6MjEwMDk0MjY1NX0.LksXP_vyz_vPJthhX2T6Nyto1xPsfacvqtXW-s2ClTU";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export const SUPABASE_CDN_BASE = `${SUPABASE_URL}/storage/v1/object/public/diagram_images`;
