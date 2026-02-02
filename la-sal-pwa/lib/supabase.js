import { createClient } from '@supabase/supabase-js';

// Reemplaza estas credenciales con las reales de tu proyecto Supabase
// Replace these with your actual Supabase project credentials
const SUPABASE_URL = 'https://xyzcompany.supabase.co';
const SUPABASE_ANON_KEY = 'public-anon-key';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
