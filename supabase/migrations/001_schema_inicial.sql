-- =============================================
-- LOGIMAX / API_IFOOD — Schema Supabase
-- Supabase Project: jynlxtamjknauqhviaaq
-- =============================================

-- Habilitar extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── PEDIDOS ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pedidos (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    ifood_id        TEXT UNIQUE,
    merchant_id     TEXT,
    status          TEXT NOT NULL DEFAULT 'pendente',
                    -- pendente, confirmado, em_preparo, saiu_entrega, entregue, cancelado
    valor_total     NUMERIC(10, 2),
    valor_itens     NUMERIC(10, 2),
    taxa_entrega    NUMERIC(10, 2),
    tempo_preparo_min   INTEGER,
    tempo_entrega_min   INTEGER,
    canal           TEXT DEFAULT 'ifood',
    cliente_nome    TEXT,
    cliente_telefone TEXT,
    endereco_entrega JSONB,
    itens           JSONB,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── KPIs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kpis (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    nome            TEXT NOT NULL,
    valor           NUMERIC,
    unidade         TEXT,
    meta            NUMERIC,
    periodo         TEXT,  -- diario, semanal, mensal
    data_referencia DATE DEFAULT CURRENT_DATE,
    dentro_da_meta  BOOLEAN,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── ALERTAS ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alertas (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tipo            TEXT NOT NULL,
    nivel           TEXT NOT NULL,  -- BAIXO, MÉDIO, ALTO, CRÍTICO
    valor_atual     TEXT,
    meta            TEXT,
    desvio          TEXT,
    status          TEXT DEFAULT 'ativo',  -- ativo, resolvido, ignorado
    sistema         TEXT DEFAULT 'LOGIMAX',
    analise         TEXT,
    recomendacao    TEXT,
    resolved_at     TIMESTAMPTZ,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── RELATÓRIOS KPI ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS relatorios_kpi (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tipo            TEXT NOT NULL,  -- diario, semanal, mensal
    data_referencia DATE,
    dados           JSONB,
    gerado_por      TEXT DEFAULT 'LOGIMAX_ANALYTICS',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── CHAT LOGS (Auditoria ChatGPT) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_logs (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    pergunta        TEXT,
    resposta        TEXT,
    modelo          TEXT,
    sistema         TEXT DEFAULT 'LOGIMAX_IA',
    usuario_id      UUID,
    session_id      TEXT,
    tokens_usados   INTEGER,
    metadata        JSONB,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

-- ── ÍNDICES ───────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pedidos_status      ON pedidos(status);
CREATE INDEX IF NOT EXISTS idx_pedidos_created_at  ON pedidos(created_at);
CREATE INDEX IF NOT EXISTS idx_pedidos_ifood_id    ON pedidos(ifood_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status      ON alertas(status);
CREATE INDEX IF NOT EXISTS idx_alertas_nivel       ON alertas(nivel);
CREATE INDEX IF NOT EXISTS idx_kpis_data           ON kpis(data_referencia);
CREATE INDEX IF NOT EXISTS idx_chat_logs_timestamp ON chat_logs(timestamp);

-- ── ROW-LEVEL SECURITY (RLS) ──────────────────────────────────────────
ALTER TABLE pedidos       ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpis          ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas       ENABLE ROW LEVEL SECURITY;
ALTER TABLE relatorios_kpi ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_logs     ENABLE ROW LEVEL SECURITY;

-- Políticas: serviço interno tem acesso total
CREATE POLICY "service_role_all" ON pedidos        FOR ALL USING (true);
CREATE POLICY "service_role_all" ON kpis           FOR ALL USING (true);
CREATE POLICY "service_role_all" ON alertas        FOR ALL USING (true);
CREATE POLICY "service_role_all" ON relatorios_kpi FOR ALL USING (true);
CREATE POLICY "service_role_all" ON chat_logs      FOR ALL USING (true);

-- ── DADOS DE TESTE ─────────────────────────────────────────────────────
INSERT INTO pedidos (ifood_id, status, valor_total, tempo_preparo_min, tempo_entrega_min, canal)
VALUES
    ('IFOOD-001', 'entregue',    89.90,  15, 32, 'ifood'),
    ('IFOOD-002', 'entregue',   120.50,  20, 28, 'ifood'),
    ('IFOOD-003', 'cancelado',   45.00,   0,  0, 'ifood'),
    ('IFOOD-004', 'em_preparo',  67.80,  10, NULL, 'ifood'),
    ('IFOOD-005', 'entregue',    95.30,  18, 41, 'ifood')
ON CONFLICT DO NOTHING;
