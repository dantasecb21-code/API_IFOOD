-- CRIAÇÃO DAS TABELAS PARA O FUNIL IFOOD
CREATE TABLE IF NOT EXISTS lojas (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    nome TEXT,
    merchant_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS metricas_semanais (
    id BIGSERIAL PRIMARY KEY,
    loja_id TEXT REFERENCES lojas(merchant_id),
    vendas_valor DECIMAL,
    pedidos_total INTEGER,
    ticket_medio DECIMAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    fonte_dados TEXT DEFAULT 'api_ifood'
);

CREATE TABLE IF NOT EXISTS ifood_tokens (
    id SERIAL PRIMARY KEY,
    access_token TEXT,
    expires_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
