"""
assistant.py — Motor de IA (ChatGPT) para supervisão de estratégia
Sistema: API_IFOOD / LOGIMAX
"""

import os
import json
from datetime import datetime
from typing import Optional
from openai import OpenAI
from supabase import create_client, Client

# ── Configuração ────────────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jynlxtamjknauqhviaaq.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ── Prompt de Sistema (FUNIL de Supervisão) ─────────────────────────

SYSTEM_PROMPT = """
Você é LOGIMAX IA — assistente especializado em supervisão de estratégia operacional 
para delivery e logística (iFood).

🎯 SEU OBJETIVO: Manter o usuário dentro do funil de supervisão.
Você analisa dados operacionais, detecta desvios, emite alertas e gera relatórios.

📋 REGRAS:
1. Responda APENAS sobre: pedidos, KPIs, métricas, alertas, relatórios e estratégia operacional.
2. Nunca saia do contexto de supervisão de delivery/logística.
3. Use dados reais do Supabase quando disponíveis.
4. Para alertas, use o formato PRÉ-ALERTA padrão.
5. Seja assertivo, direto e baseado em dados.

📊 FORMATO PRÉ-ALERTA:
🔴 PRÉ-ALERTA | [NÍVEL: BAIXO/MÉDIO/ALTO/CRÍTICO]
━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Indicador: [nome]
📈 Valor atual: [X]
🎯 Meta: [Y]
⚠️ Desvio: [Z%]
🔍 Análise: [descrição]
💡 Recomendação: [ação]
"""

# ── Contexto de Dados do Supabase ────────────────────────────────────

def buscar_contexto_operacional() -> dict:
    """Busca dados operacionais recentes do Supabase para enriquecer o contexto."""
    contexto = {}

    try:
        # KPIs recentes
        resultado_kpi = supabase.table("kpis").select("*").order("created_at", desc=True).limit(10).execute()
        contexto["kpis"] = resultado_kpi.data if resultado_kpi.data else []

        # Pedidos recentes
        resultado_pedidos = supabase.table("pedidos").select("*").order("created_at", desc=True).limit(20).execute()
        contexto["pedidos_recentes"] = resultado_pedidos.data if resultado_pedidos.data else []

        # Alertas ativos
        resultado_alertas = supabase.table("alertas").select("*").eq("status", "ativo").execute()
        contexto["alertas_ativos"] = resultado_alertas.data if resultado_alertas.data else []

    except Exception as e:
        contexto["erro"] = str(e)

    return contexto


# ── Motor de Chat ────────────────────────────────────────────────────

class AssistenteLOGIMAX:
    def __init__(self):
        self.historico: list[dict] = []
        self.max_historico = 20

    def _preparar_mensagens(self, pergunta: str, contexto: Optional[dict] = None) -> list[dict]:
        """Prepara o histórico de mensagens com contexto de dados."""
        mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Injetar contexto de dados do Supabase
        if contexto:
            contexto_str = json.dumps(contexto, ensure_ascii=False, default=str, indent=2)
            mensagens.append({
                "role": "system",
                "content": f"📊 DADOS OPERACIONAIS ATUAIS DO SUPABASE:\n{contexto_str}"
            })

        # Histórico de conversa (janela deslizante)
        mensagens.extend(self.historico[-self.max_historico:])

        # Pergunta atual
        mensagens.append({"role": "user", "content": pergunta})
        return mensagens

    def responder(self, pergunta: str, usar_contexto: bool = True) -> str:
        """Gera resposta do assistente com base na pergunta e no contexto operacional."""
        contexto = buscar_contexto_operacional() if usar_contexto else None

        mensagens = self._preparar_mensagens(pergunta, contexto)

        try:
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=mensagens,
                max_tokens=1024,
                temperature=0.3,  # Baixo para maior assertividade
            )
            resposta = response.choices[0].message.content

            # Atualizar histórico
            self.historico.append({"role": "user", "content": pergunta})
            self.historico.append({"role": "assistant", "content": resposta})

            # Salvar interação no Supabase
            self._salvar_log(pergunta, resposta)

            return resposta

        except Exception as e:
            return f"❌ Erro ao processar: {str(e)}"

    def _salvar_log(self, pergunta: str, resposta: str):
        """Salva log da interação no Supabase para auditoria."""
        try:
            supabase.table("chat_logs").insert({
                "pergunta": pergunta,
                "resposta": resposta,
                "modelo": OPENAI_MODEL,
                "timestamp": datetime.utcnow().isoformat(),
                "sistema": "LOGIMAX_IA"
            }).execute()
        except Exception:
            pass  # Log é melhor esforço, não crítico


# ── Interface CLI ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🍔 LOGIMAX IA — Assistente de Supervisão Operacional")
    print("=" * 55)
    print("Digite 'sair' para encerrar | 'limpar' para novo contexto")
    print()

    assistente = AssistenteLOGIMAX()

    while True:
        try:
            entrada = input("Você: ").strip()
            if not entrada:
                continue
            if entrada.lower() == "sair":
                print("Encerrando assistente...")
                break
            if entrada.lower() == "limpar":
                assistente.historico = []
                print("✅ Histórico limpo.")
                continue

            print("\nLOGIMAX IA: ", end="", flush=True)
            resposta = assistente.responder(entrada)
            print(resposta)
            print()

        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário.")
            break
