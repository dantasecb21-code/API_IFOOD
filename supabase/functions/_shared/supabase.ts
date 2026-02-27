import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

export const getSupabaseClient = (req: Request) => {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
    const authHeader = req.headers.get('Authorization');

    return createClient(supabaseUrl, supabaseAnonKey, {
        global: {
            headers: {
                Authorization: authHeader || '',
            }
        }
    });
};

export const getServiceRoleClient = () => {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? Deno.env.get('SUPABASE_ANON_KEY') ?? ''; // Fallback to anon key in dev if undefined

    return createClient(supabaseUrl, serviceRoleKey);
};
