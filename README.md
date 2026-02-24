# 🍔 API_IFOOD — Supervisão de Estratégia de Delivery

Sistema de supervisão de estratégia com foco em **automação**, **assertividade de dados** e **integração entre sistemas** para operações de delivery iFood.

## 🏗️ Arquitetura

```
API_IFOOD/
├── backend/              # NestJS API REST
│   └── src/
│       └── modules/
│           ├── assistant/    # Integração ChatGPT
│           ├── pedidos/      # Gestão de pedidos iFood
│           ├── analytics/    # KPIs e métricas
│           └── auth/         # Autenticação JWT
├── python-core/          # Scripts Python (análise e automação)
│   ├── assistant.py      # Motor do ChatGPT
│   ├── analytics.py      # Cálculo de KPIs
│   └── sync.py           # Sincronização Supabase
├── frontend/             # React Dashboard
├── supabase/             # Migrations e configuração DB
│   └── migrations/
├── .env.example
└── docker-compose.yml
```

## 🔌 Integrações

| Sistema     | Finalidade                            |
|-------------|---------------------------------------|
| Supabase    | Banco de dados principal (PostgreSQL) |
| ChatGPT API | Assistente virtual e análise de dados |
| iFood API   | Recepção de pedidos e eventos         |

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/dantasecb21-code/API_IFOOD.git
cd API_IFOOD

# Configurar variáveis de ambiente
cp .env.example .env

# Instalar dependências
cd backend && npm install
cd ../python-core && pip install -r requirements.txt

# Iniciar serviços
docker-compose up -d
```

## 📊 Funcionalidades Principais

- ✅ Supervisão em tempo real de pedidos iFood
- ✅ Assistente inteligente (ChatGPT) para análise de delivery
- ✅ KPIs automáticos (taxa de conversão, tempo médio, cancelamentos)
- ✅ Alertas e pré-alertas automáticos
- ✅ Dashboard de métricas e relatórios
- ✅ Integração Supabase (PostgreSQL) como fonte única de verdade

## 🛡️ Supabase

- **Project ID:** `jynlxtamjknauqhviaaq`
- **URL:** `https://jynlxtamjknauqhviaaq.supabase.co`
