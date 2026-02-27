import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY') ?? ''
        const supabase = createClient(supabaseUrl, supabaseKey, {
            global: { headers: { Authorization: req.headers.get('Authorization')! } }
        })

        const hoje = new Date().toISOString()

        const [
            { data: kpis },
            { data: pedidos_recentes },
            { data: alertas_ativos },
            { data: metricas_semanais },
            { data: tarefas_pendentes },
            { data: checklist },
            { data: proximas_reunioes }
        ] = await Promise.all([
            supabase.table('kpis').select('*').order('created_at', { ascending: false }).limit(10),
            supabase.table('pedidos').select('*').order('created_at', { ascending: false }).limit(20),
            supabase.table('alertas').select('*').eq('status', 'ativo'),
            supabase.table('metricas_semanais_ifood').select('*').order('created_at', { ascending: false }).limit(5),
            supabase.table('tarefas').select('*').eq('status', 'pendente').order('prioridade', { ascending: false }).limit(10),
            supabase.table('checklist_estrategia').select('*'),
            supabase.table('reunioes').select('*').gte('data_hora', hoje).order('data_hora', { ascending: true }).limit(3)
        ])

        const contexto = {
            kpis: kpis || [],
            pedidos_recentes: pedidos_recentes || [],
            alertas_ativos: alertas_ativos || [],
            metricas_semanais: metricas_semanais || [],
            tarefas_pendentes: tarefas_pendentes || [],
            checklist: checklist || [],
            proximas_reunioes: proximas_reunioes || []
        }

        return new Response(JSON.stringify(contexto), {
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
