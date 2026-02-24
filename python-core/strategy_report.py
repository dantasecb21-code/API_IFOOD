"""
strategy_report.py — Gerador de Relatórios Estratégicos de Delivery
Sistema: API_IFOOD
"""

import os
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_overview_estrategico(merchant_id: str):
    """
    Compila dados de métricas semanais e tarefas para gerar um relatório estruturado.
    """
    try:
        # 1. Buscar métricas mais recentes
        res_metrics = supabase.table("metricas_semanais_ifood")\
            .select("*")\
            .eq("merchant_id", merchant_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        metrics = res_metrics.data[0] if res_metrics.data else None
        
        # 2. Buscar tarefas prioritárias
        res_tasks = supabase.table("tarefas")\
            .select("*")\
            .eq("status", "pendente")\
            .order("prioridade", desc=True)\
            .limit(5)\
            .execute()
        
        tasks = res_tasks.data if res_tasks.data else []

        if not metrics:
            return "⚠️ Nenhuma métrica encontrada para gerar o relatório estratégico."

        # Construção do Relatório
        report = []
        report.append(f"📊 RELATÓRIO ESTRATÉGICO DE SUPERVISÃO")
        report.append(f"📅 Referência: {metrics['data_inicio']} a {metrics['data_fim']}")
        report.append("="*40)
        
        report.append("\n💰 PERFORMANCE FINANCEIRA")
        report.append(f"- Faturamento Total: {formatar_moeda(metrics['faturamento_total'])}")
        report.append(f"- Ticket Médio: {formatar_moeda(metrics['ticket_medio'])}")
        report.append(f"- Conversão: {metrics['conversao_pct']}%")
        
        report.append("\n🌪️ FUNIL DE VENDAS (Conversão)")
        report.append(f"- Visitas: {metrics['visitas']}")
        report.append(f"- Sacola (Add): {metrics['sacola']}")
        report.append(f"- Concluídos: {metrics['concluidos']}")
        taxa_funil = round((metrics['concluidos'] / metrics['visitas'] * 100), 2) if metrics['visitas'] > 0 else 0
        report.append(f"💡 Eficiência Geral do Funil: {taxa_funil}%")
        
        report.append("\n⚙️ OPERAÇÃO E QUALIDADE")
        report.append(f"- Nota da Loja: {metrics['nota_loja']} / 5.0")
        report.append(f"- Tempo Aberto: {metrics['tempo_aberto_pct']}%")
        report.append(f"- Taxa de Cancelamento: {metrics['pedidos_cancelados_pct']}%")
        
        report.append("\n🚀 TAREFAS PRIORITÁRIAS (Próximos Passos)")
        if tasks:
            for t in tasks:
                report.append(f"[{t['prioridade'].upper()}] {t['titulo']}")
        else:
            report.append("- Nenhuma tarefa pendente.")
            
        report.append("\n" + "="*40)
        report.append("🎯 FOCO ESTRATÉGICO: Manter o funil estável e reduzir cancelamentos.")

        return "\n".join(report)

    except Exception as e:
        return f"❌ Erro ao gerar relatório: {str(e)}"

if __name__ == "__main__":
    m_id = os.getenv("IFOOD_MERCHANT_ID", "1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p")
    print(gerar_overview_estrategico(m_id))
