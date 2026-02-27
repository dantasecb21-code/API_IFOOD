import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey)

        const hoje = new Date()
        const inicio = `${hoje.toISOString().split('T')[0]}T00:00:00.000Z`
        const fim = hoje.toISOString()

        const { data: pedidos, error } = await supabase
            .table('pedidos')
            .select('*')
            .gte('created_at', inicio)
            .lte('created_at', fim)

        if (error) throw error

        const total = pedidos?.length || 0
        const aprovados = pedidos?.filter(p => ['entregue', 'concluido'].includes(p.status)).length || 0
        const cancelados = pedidos?.filter(p => p.status === 'cancelado').length || 0
        const taxaConversao = total > 0 ? (aprovados / total * 100) : 0

        const pedidosEntregues = pedidos?.filter(p => p.status === 'entregue') || []
        const tempos = pedidosEntregues.map(p => (Number(p.tempo_preparo_min) || 0) + (Number(p.tempo_entrega_min) || 0))
        const tempoMedio = tempos.length > 0 ? tempos.reduce((a, b) => a + b, 0) / tempos.length : 0

        const valores = pedidos?.map(p => Number(p.valor_total) || 0) || []
        const faturamento_total = valores.reduce((a, b) => a + b, 0)
        const ticketMedia = total > 0 ? (faturamento_total / total) : 0

        const relatorio = {
            data: hoje.toISOString().split('T')[0],
            gerado_em: hoje.toISOString(),
            sistema: 'API_IFOOD',
            taxa_conversao: {
                total_pedidos: total,
                aprovados,
                cancelados,
                taxa_conversao: `${taxaConversao.toFixed(2)}%`
            },
            tempo_medio_entrega: {
                pedidos_entregues: pedidosEntregues.length,
                tempo_medio_min: Number(tempoMedio.toFixed(1))
            },
            ticket_medio: {
                faturamento_total: `R$ ${faturamento_total.toFixed(2)}`,
                ticket_medio: `R$ ${ticketMedia.toFixed(2)}`
            }
        }

        const { data, error: insertError } = await supabase
            .table('relatorios_kpi')
            .insert({
                data_referencia: relatorio.data,
                dados: relatorio,
                tipo: 'diario',
                gerado_por: 'API_IFOOD_ANALYTICS'
            })
            .select()

        if (insertError) throw insertError

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
