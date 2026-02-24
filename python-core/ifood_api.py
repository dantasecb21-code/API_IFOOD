"""
ifood_api.py — Integração com a API de Parceiros do iFood (Merchant API)
Sistema: API_IFOOD
"""

import os
import httpx
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações da API iFood
IFOOD_CLIENT_ID = os.getenv("IFOOD_CLIENT_ID")
IFOOD_CLIENT_SECRET = os.getenv("IFOOD_CLIENT_SECRET")
IFOOD_BASE_URL = os.getenv("IFOOD_API_BASE_URL", "https://merchant-api.ifood.com.br")

class IFoodClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def _authenticate(self):
        """Realiza a autenticação OAuth2 com o iFood."""
        url = f"{IFOOD_BASE_URL}/authentication/v1.0/oauth/token"
        data = {
            "grantType": "client_credentials",
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["accessToken"]
                # Em ambiente real, tratar expiração (expiresIn)
                logger.info("Autenticação iFood realizada com sucesso.")
            else:
                logger.error(f"Erro na autenticação iFood: {response.text}")
                raise Exception("Falha na autenticação iFood")

    async def get_headers(self) -> Dict[str, str]:
        if not self.access_token:
            await self._authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    async def get_sales_metrics(self, merchant_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Busca métricas de vendas: Total, Clientes novos, Faturamento, Ticket Médio.
        Note: Use os endpoints reais do Merchant API (ex: /financial/v1.0/merchants/{id}/sales)
        """
        # Placeholder para implementação baseada na documentação da iFood
        # Exemplo de retorno simulado baseado no pedido do usuário
        logger.info(f"Buscando métricas de vendas para {merchant_id} de {start_date} a {end_date}")
        
        # Simulação de chamada real
        return {
            "vendas_total": 150,
            "clientes_novos": 45,
            "faturamento_total": 4500.50,
            "ticket_medio": 30.00,
            "conversao_pct": 12.5,
            "margem_pct": 22.0
        }

    async def get_funnel_metrics(self, merchant_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Busca métricas do funil: Visitas, Visualizações, Sacola, Revisão, Concluídos.
        """
        logger.info(f"Buscando métricas de funil para {merchant_id}")
        return {
            "visitas": 1200,
            "visualizacoes": 800,
            "sacola": 250,
            "revisao": 180,
            "concluidos": 150
        }

    async def get_operational_metrics(self, merchant_id: str) -> Dict[str, Any]:
        """
        Busca métricas de operação: Tempo aberto, Chamados, Cancelados, Nota.
        """
        logger.info(f"Buscando métricas operacionais para {merchant_id}")
        return {
            "tempo_aberto_pct": 98.5,
            "pedidos_chamado_pct": 2.1,
            "pedidos_cancelados_pct": 1.5,
            "nota_loja": 4.8,
            "valor_devido_ifood": 350.20
        }

async def fetch_and_populate_metrics(merchant_id: str, month: int, year: int, start_date: date, end_date: date):
    """
    Função principal para orquestrar a busca e retorno dos dados para salvar no Supabase.
    """
    client = IFoodClient(IFOOD_CLIENT_ID, IFOOD_CLIENT_SECRET)
    
    sales = await client.get_sales_metrics(merchant_id, start_date, end_date)
    funnel = await client.get_funnel_metrics(merchant_id, start_date, end_date)
    operational = await client.get_operational_metrics(merchant_id)
    
    return {
        "merchant_id": merchant_id,
        "mes": month,
        "ano": year,
        "data_inicio": start_date.isoformat(),
        "data_fim": end_date.isoformat(),
        **sales,
        **funnel,
        **operational
    }
