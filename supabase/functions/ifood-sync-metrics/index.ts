import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const { merchant_id, access_token, data_inicio, data_fim } = await req.json()

        if (!merchant_id || !data_inicio || !data_fim) {
            throw new Error('merchant_id, data_inicio e data_fim são obrigatórios')
        }

        // This would ideally make a real request if access_token is valid, but here we mock based on the python code intent.
        // Replace the URL with actual ones for a real setup e.g., `${Deno.env.get('IFOOD_API_BASE_URL')}/financial/v1.0/merchants/${merchant_id}/sales`

        const vendas = {
            vendas_total: 150,
            clientes_novos: 45,
            faturamento_total: 4500.50,
            ticket_medio: 30.00,
            conversao_pct: 12.5,
        }

        // According to strategy: ONLY fetch Financials / Orders from API.
        // Note: Funnel, Margins, and Operation metrics are manual, so they are not fetched.

        // We will save this snippet to metricas_semanais_ifood but leave the rest null or default
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey, {
            global: { headers: { Authorization: req.headers.get('Authorization')! } }
        })

        const payload = {
            merchant_id,
            mes: new Date(data_inicio).getMonth() + 1,
            ano: new Date(data_inicio).getFullYear(),
            data_inicio,
            data_fim,
            ...vendas
        }

        const { data, error } = await supabase
            .table('metricas_semanais_ifood')
            .insert(payload)
            .select()

        if (error) throw error

        return new Response(JSON.stringify(data), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
        })
    } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400,
        })
    }
})
