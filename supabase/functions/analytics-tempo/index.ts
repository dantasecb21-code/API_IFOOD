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
            .select('tempo_preparo_min, tempo_entrega_min, status')
            .gte('created_at', data_inicio)
            .lte('created_at', data_fim)
            .eq('status', 'entregue')

        if (error) throw error

        if (!pedidos || pedidos.length === 0) {
            return new Response(JSON.stringify({ erro: "Nenhum pedido entregue no período" }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            })
        }

        const tempos = pedidos.map(p => (Number(p.tempo_preparo_min) || 0) + (Number(p.tempo_entrega_min) || 0))
        const sum = tempos.reduce((a, b) => a + b, 0)
        const media = tempos.length > 0 ? Number((sum / tempos.length).toFixed(1)) : 0

        return new Response(JSON.stringify({
            periodo: { inicio: data_inicio, fim: data_fim },
            pedidos_entregues: pedidos.length,
            tempo_medio_min: media,
            meta_min: 45,
            dentro_da_meta: media <= 45
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
