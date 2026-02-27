import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const { data_inicio, data_fim } = await req.json()

        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey, {
            global: { headers: { Authorization: req.headers.get('Authorization')! } }
        })

        const { data: pedidos, error } = await supabase
            .table('pedidos')
            .select('valor_total')
            .gte('created_at', data_inicio)
            .lte('created_at', data_fim)

        if (error) throw error

        const valores = (pedidos || []).map(p => Number(p.valor_total) || 0)
        const total = valores.length
        const soma = valores.reduce((a, b) => a + b, 0)
        const media = total > 0 ? Number((soma / total).toFixed(2)) : 0

        return new Response(JSON.stringify({
            periodo: { inicio: data_inicio, fim: data_fim },
            total_pedidos: total,
            faturamento_total: `R$ ${soma.toFixed(2)}`,
            ticket_medio: `R$ ${media.toFixed(2)}`
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
