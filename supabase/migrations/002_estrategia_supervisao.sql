-- =============================================
-- API_IFOOD — Estratégia e Supervisão
-- =============================================

-- ── 1. MÉTRICAS SEMANAIS (iFood) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS metricas_semanais_ifood (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    merchant_id     UUID NOT NULL, -- Loja (seleção)
    mes             INTEGER NOT NULL,
    ano             INTEGER NOT NULL,
    data_inicio     DATE NOT NULL,
    data_fim        DATE NOT NULL,
    
    -- Vendas
    vendas_total    INTEGER DEFAULT 0,
    clientes_novos  INTEGER DEFAULT 0,
    faturamento_total NUMERIC(12, 2) DEFAULT 0,
    ticket_medio    NUMERIC(10, 2) DEFAULT 0,
    conversao_pct   NUMERIC(5, 2) DEFAULT 0,
    margem_pct      NUMERIC(5, 2) DEFAULT 0,
    
    -- Funil
    visitas         INTEGER DEFAULT 0,
    visualizacoes   INTEGER DEFAULT 0,
    sacola          INTEGER DEFAULT 0,
    revisao         INTEGER DEFAULT 0,
    concluidos      INTEGER DEFAULT 0,
    
    -- Operação
    tempo_aberto_pct NUMERIC(5, 2) DEFAULT 0,
    pedidos_chamado_pct NUMERIC(5, 2) DEFAULT 0,
    pedidos_cancelados_pct NUMERIC(5, 2) DEFAULT 0,
    nota_loja       NUMERIC(3, 1) DEFAULT 0,
    
    valor_devido_ifood NUMERIC(12, 2) DEFAULT 0,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. TAREFAS ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tarefas (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    titulo          TEXT NOT NULL,
    descricao       TEXT,
    status          TEXT NOT NULL DEFAULT 'pendente', -- pendente, em_andamento, concluída
    prioridade      TEXT NOT NULL DEFAULT 'baixa',    -- baixa, média, alta
    importancia     TEXT NOT NULL DEFAULT 'planejada',-- planejada, importante, urgente
    data_vencimento DATE,
    data_hora_inicio TIMESTAMPTZ,
    data_hora_conclusao_planejada TIMESTAMPTZ,
    observacoes     TEXT,
    merchant_id     UUID,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 3. MÉTRICAS MENSAIS DO GESTOR ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS metricas_mensais_gestor (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    merchant_id     UUID NOT NULL,
    mes             INTEGER NOT NULL,
    ano             INTEGER NOT NULL,
    faturamento_7d  NUMERIC(12, 2) DEFAULT 0,
    faturamento_30d NUMERIC(12, 2) DEFAULT 0,
    screenshots     TEXT[], -- Array de URLs de arquivos
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 4. CHECKLIST DE ESTRATÉGIA ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS checklist_estrategia (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    titulo          TEXT NOT NULL,
    concluido       BOOLEAN DEFAULT FALSE,
    data_conclusao  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 6. PERFIL ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS perfis (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    nome            TEXT,
    telefone        TEXT,
    foto_url        TEXT,
    bio             TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 7. REUNIÕES ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reunioes (
    id              UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    titulo          TEXT NOT NULL,
    data_hora       TIMESTAMPTZ NOT NULL,
    participantes   TEXT[],
    ata             TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── ÍNDICES ───────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_metricas_semanais_loja ON metricas_semanais_ifood(merchant_id);
CREATE INDEX IF NOT EXISTS idx_tarefas_status        ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_vencimento    ON tarefas(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_metricas_mensais_loja ON metricas_mensais_gestor(merchant_id);

-- ── RLS ──────────────────────────────────────────────────────────────
ALTER TABLE metricas_semanais_ifood ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarefas                ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_mensais_gestor ENABLE ROW LEVEL SECURITY;
ALTER TABLE checklist_estrategia    ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfis                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE reunioes               ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON metricas_semanais_ifood FOR ALL USING (true);
CREATE POLICY "service_role_all" ON tarefas                FOR ALL USING (true);
CREATE POLICY "service_role_all" ON metricas_mensais_gestor FOR ALL USING (true);
CREATE POLICY "service_role_all" ON checklist_estrategia    FOR ALL USING (true);
CREATE POLICY "service_role_all" ON perfis                 FOR ALL USING (true);
CREATE POLICY "service_role_all" ON reunioes               FOR ALL USING (true);
