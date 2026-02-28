import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def test_db():
    url = "https://jynlxtamjknauqhviaaq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp5bmx4dGFtamtuYXVxaHZpYWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4MTM3NTQsImV4cCI6MjA3NDM4OTc1NH0.-fq6drimelIm95UXk_rKpyv68cZggJY1_4R2BaLmVmY"
    
    print("--- DIAGNOSTICO BANCO ---")
    try:
        sb = create_client(url, key)
        # Testar se a tabela de métricas existe
        res = sb.table("metricas_semanais").select("count").limit(1).execute()
        print("SUCCESS: Conexao com Supabase OK!")
        print(f"Tabela metricas_semanais existe e respondeu.")
    except Exception as e:
        print(f"ERROR: Falha no banco: {str(e)}")

if __name__ == "__main__":
    test_db()
