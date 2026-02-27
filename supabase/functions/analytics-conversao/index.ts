import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const { data_inicio, data_fim } = await req.json()

        // Config Supabase
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey, {
            global: { headers: { Authorization: req.headers.get('Authorization')! } }
        })

        const { data: pedidos, error } = await supabase
            .table('pedidos')
            .select('status')
            .gte('created_at', data_inicio)
            .lte('created_at', data_fim)

        if (error) throw error

        const total = pedidos?.length || 0
        const aprovados = pedidos?.filter(p => ['entregue', 'concluido'].includes(p.status)).length || 0
        const cancelados = pedidos?.filter(p => p.status === 'cancelado').length || 0
        const taxa = total > 0 ? Number((aprovados / total * 100).toFixed(2)) : 0

        return new Response(JSON.stringify({
            periodo: { inicio: data_inicio, fim: data_fim },
            total_pedidos: total,
            aprovados,
            cancelados,
            taxa_conversao: `${taxa}%`,
            taxa_cancelamento: `${total > 0 ? Number((cancelados / total * 100).toFixed(2)) : 0}%`
        }), {
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
