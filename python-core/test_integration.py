"""
test_integration.py — Script de teste para verificar a integração iFood e persistência.
"""

import asyncio
import os
from datetime import date, timedelta
from analytics import atualizar_metricas_semanais
from ifood_api import IFoodClient
import unittest
from unittest.mock import patch, MagicMock

class TestIFoodIntegration(unittest.TestCase):
    @patch('ifood_api.httpx.AsyncClient')
    async def test_populate_metrics(self, mock_client):
        # Mocking the response for authentication and metrics
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"accessToken": "fake_token"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        merchant_id = "test-merchant-uuid"
        print(f"Testing metrics update for {merchant_id}...")
        
        # Test the update function
        # Note: Since atualizar_metricas_semanais depends on Supabase client setup, 
        # we'll mock the supabase client inside analytics if needed, but here 
        # let's just test the logic integration.
        
        with patch('analytics.supabase') as mock_supabase:
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "new-metric-id"}])
            
            result = await atualizar_metricas_semanais(merchant_id)
            print(f"Result: {result}")
            
            self.assertIn("id", result[0])
            self.assertEqual(result[0]["id"], "new-metric-id")

if __name__ == "__main__":
    # For a quick manual run without full unittest overhead
    async def manual_test():
        print("🚀 Iniciando teste manual de integração...")
        merchant_id = "1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p"
        
        try:
            # Tenta rodar a atualização (usando mocks internos ou dados reais se configurado)
            from analytics import atualizar_metricas_semanais
            res = await atualizar_metricas_semanais(merchant_id)
            print(f"✅ Resultado da atualização: {res}")
        except Exception as e:
            print(f"❌ Erro no teste: {e}")

    asyncio.run(manual_test())
