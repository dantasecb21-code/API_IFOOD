# 🤖 API_IFOOD MCP Server

Este servidor centraliza as integrações do sistema **API_IFOOD**, permitindo que o **Lovable** e outros agentes de IA acessem múltiplos repositórios do GitHub, dados do iFood e análises do Supabase através de uma única interface.

## 🚀 Como Executar

1.  **Instalar dependências**:
    ```bash
    cd mcp-server
    pip install -r requirements.txt
    ```

2.  **Configurar Variáveis**:
    Certifique-se de que seu `.env` na raiz do projeto contenha:
    ```env
    # Múltiplos tokens separados por vírgula
    GITHUB_TOKENS="token_1,token_2,token_3"
    
    # Configurações existentes
    SUPABASE_URL=...
    SUPABASE_KEY=...
    IFOOD_CLIENT_ID=...
    IFOOD_CLIENT_SECRET=...
    ```

3.  **Iniciar o Servidor**:
    ```bash
    python server.py
    ```
    O servidor estará disponível em `http://localhost:8000`.

## 🛠️ Ferramentas Disponíveis (MCP Tools)

*   `get_daily_kpis`: Retorna taxa de conversão e volume de pedidos do dia.
*   `github_global_search`: Pesquisa issues e PRs em todas as contas GitHub configuradas.
*   `sync_ifood_data`: Força a sincronização de métricas da iFood Merchant API.

## 🔗 Integração com Lovable

Para conectar o Lovable, use a URL base `http://localhost:8000/api/v1` ou configure o endpoint MCP no ambiente Lovable apontando para `http://localhost:8000/mcp`.
