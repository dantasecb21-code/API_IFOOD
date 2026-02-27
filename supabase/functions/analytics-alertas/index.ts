import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        // Cron jobs use Service Role bypass RLS for internal tasks
        const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey)

        // Using current date range for "today"
        const hoje = new Date()
        const inicio = `${hoje.toISOString().split('T')[0]}T00:00:00.000Z`
        const fim = hoje.toISOString()

        const { data: pedidos, error } = await supabase
            .table('pedidos')
            .select('status, tempo_preparo_min, tempo_entrega_min')
            .gte('created_at', inicio)
            .lte('created_at', fim)

        if (error) throw error

        const total = pedidos?.length || 0
        const aprovados = pedidos?.filter(p => ['entregue', 'concluido'].includes(p.status)).length || 0
        const taxaConversao = total > 0 ? (aprovados / total * 100) : 0

        // Time average
        const pedidosEntregues = pedidos?.filter(p => p.status === 'entregue') || []
        const tempos = pedidosEntregues.map(p => (Number(p.tempo_preparo_min) || 0) + (Number(p.tempo_entrega_min) || 0))
        const tempoMedio = tempos.length > 0 ? tempos.reduce((a, b) => a + b, 0) / tempos.length : 0

        const alertas = []

        if (taxaConversao < 80 && total > 0) {
            const nivel = taxaConversao < 60 ? 'CRÍTICO' : taxaConversao < 70 ? 'ALTO' : 'MÉDIO'
            alertas.push({
                tipo: 'TAXA_CONVERSAO_BAIXA',
                nivel,
                valor_atual: `${taxaConversao.toFixed(1)}%`,
                meta: '80%',
                desvio: `${(80 - taxaConversao).toFixed(1)}%`,
                timestamp: fim,
                status: 'ativo',
                sistema: 'API_IFOOD_ANALYTICS'
            })
        }

        if (tempoMedio > 45) {
            const nivel = tempoMedio > 60 ? 'CRÍTICO' : 'ALTO'
            alertas.push({
                tipo: 'TEMPO_ENTREGA_ALTO',
                nivel,
                valor_atual: `${tempoMedio.toFixed(1)} min`,
                meta: '45 min',
                desvio: `${(tempoMedio - 45).toFixed(1)} min acima`,
                timestamp: fim,
                status: 'ativo',
                sistema: 'API_IFOOD_ANALYTICS'
            })
        }

        for (const alerta of alertas) {
            await supabase.table('alertas').insert(alerta)
        }

        return new Response(JSON.stringify({ alertas_gerados: alertas }), {
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
