"""
analytics.py — Cálculo de KPIs e métricas operacionais
Sistema: API_IFOOD / LOGIMAX
"""

import os
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jynlxtamjknauqhviaaq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def calcular_taxa_conversao(data_inicio: str, data_fim: str) -> dict:
    """
    Calcula a taxa de conversão de pedidos no período informado.
    
    Retorna: { total, aprovados, cancelados, taxa_conversao }
    """
    resultado = supabase.table("pedidos").select("status").gte(
        "created_at", data_inicio
    ).lte("created_at", data_fim).execute()

    pedidos = resultado.data or []
    total = len(pedidos)
    aprovados = sum(1 for p in pedidos if p.get("status") in ["entregue", "concluido"])
    cancelados = sum(1 for p in pedidos if p.get("status") == "cancelado")
    taxa = round((aprovados / total * 100), 2) if total > 0 else 0

    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "total_pedidos": total,
        "aprovados": aprovados,
        "cancelados": cancelados,
        "taxa_conversao": f"{taxa}%",
        "taxa_cancelamento": f"{round(cancelados / total * 100, 2) if total > 0 else 0}%"
    }


def calcular_tempo_medio_entrega(data_inicio: str, data_fim: str) -> dict:
    """
    Calcula o tempo médio de entrega no período.
    """
    resultado = supabase.table("pedidos").select(
        "tempo_preparo_min, tempo_entrega_min, status"
    ).gte("created_at", data_inicio).lte(
        "created_at", data_fim
    ).eq("status", "entregue").execute()

    pedidos = resultado.data or []

    if not pedidos:
        return {"erro": "Nenhum pedido entregue no período"}

    tempos = [
        (p.get("tempo_preparo_min", 0) or 0) + (p.get("tempo_entrega_min", 0) or 0)
        for p in pedidos
    ]
    media = round(sum(tempos) / len(tempos), 1) if tempos else 0

    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "pedidos_entregues": len(pedidos),
        "tempo_medio_min": media,
        "meta_min": 45,  # Meta padrão: 45 minutos
        "dentro_da_meta": media <= 45
    }


def gerar_relatorio_kpis_diario() -> dict:
    """
    Gera relatório de KPIs do dia atual automaticamente.
    """
    hoje = datetime.utcnow().date()
    inicio = f"{hoje}T00:00:00"
    fim = f"{hoje}T23:59:59"

    conversao = calcular_taxa_conversao(inicio, fim)
    tempo_medio = calcular_tempo_medio_entrega(inicio, fim)

    relatorio = {
        "data": str(hoje),
        "gerado_em": datetime.utcnow().isoformat(),
        "taxa_conversao": conversao,
        "tempo_medio_entrega": tempo_medio,
    }

    # Salvar no Supabase
    try:
        supabase.table("relatorios_kpi").insert({
            "data_referencia": str(hoje),
            "dados": relatorio,
            "tipo": "diario",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        relatorio["aviso_salvar"] = str(e)

    return relatorio


def verificar_alertas_automaticos() -> list[dict]:
    """
    Verifica automaticamente se algum KPI está fora dos limites e emite alertas.
    """
    alertas = []
    hoje = datetime.utcnow().date()
    inicio = f"{hoje}T00:00:00"
    fim = datetime.utcnow().isoformat()

    conversao = calcular_taxa_conversao(inicio, fim)
    taxa_str = conversao.get("taxa_conversao", "0%").replace("%", "")
    taxa = float(taxa_str) if taxa_str else 0

    # Alerta: taxa de conversão abaixo de 80%
    if taxa < 80:
        nivel = "CRÍTICO" if taxa < 60 else "ALTO" if taxa < 70 else "MÉDIO"
        alertas.append({
            "tipo": "TAXA_CONVERSAO_BAIXA",
            "nivel": nivel,
            "valor_atual": f"{taxa}%",
            "meta": "80%",
            "desvio": f"{round(80 - taxa, 1)}%",
            "timestamp": datetime.utcnow().isoformat()
        })

    # Salvar alertas no Supabase
    for alerta in alertas:
        try:
            supabase.table("alertas").insert({
                **alerta,
                "status": "ativo",
                "sistema": "LOGIMAX_ANALYTICS"
            }).execute()
        except Exception:
            pass

    return alertas


if __name__ == "__main__":
    print("📊 Gerando relatório KPI diário...")
    relatorio = gerar_relatorio_kpis_diario()
    print(relatorio)

    print("\n🔍 Verificando alertas automáticos...")
    alertas = verificar_alertas_automaticos()
    if alertas:
        for a in alertas:
            print(f"⚠️  [{a['nivel']}] {a['tipo']}: {a['valor_atual']} (meta: {a['meta']})")
    else:
        print("✅ Todos os KPIs dentro dos limites.")
