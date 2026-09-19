-- Schema do banco para o app "Ensaio Local / Culto de Jovens"
-- Compatível com Turso (libsql) e SQLite local

-- Cadastro de músicos e organistas (usado no Relatório Mensal por pessoa)
CREATE TABLE IF NOT EXISTS musicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    instrumento TEXT NOT NULL,           -- ex: Flauta, Trompete, Organista, etc
    categoria TEXT NOT NULL,             -- 'Músico' ou 'Organista'
    nivel TEXT,                          -- RJM, Casado(a), etc
    ativo INTEGER NOT NULL DEFAULT 1
);

-- Um registro por culto/ensaio
CREATE TABLE IF NOT EXISTS cultos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,                  -- formato YYYY-MM-DD
    dia_semana TEXT,                     -- ex: 'Domingo', 'Quinta-feira'
    tipo_ensaio TEXT,                    -- 'Local' ou 'Regional'
    fora_do_padrao INTEGER NOT NULL DEFAULT 0,  -- 1 se foi criado em dia que não é o padrão

    -- Irmandade (sem instrumento)
    irmaos INTEGER NOT NULL DEFAULT 0,
    irmas INTEGER NOT NULL DEFAULT 0,

    -- Cordas
    violino INTEGER NOT NULL DEFAULT 0,
    viola INTEGER NOT NULL DEFAULT 0,
    violoncelo INTEGER NOT NULL DEFAULT 0,
    contrabaixo INTEGER NOT NULL DEFAULT 0,

    -- Madeiras
    flauta INTEGER NOT NULL DEFAULT 0,
    clarinete INTEGER NOT NULL DEFAULT 0,
    sax_soprano INTEGER NOT NULL DEFAULT 0,
    sax_alto INTEGER NOT NULL DEFAULT 0,
    sax_tenor INTEGER NOT NULL DEFAULT 0,
    fagote INTEGER NOT NULL DEFAULT 0,
    oboe INTEGER NOT NULL DEFAULT 0,

    -- Metais
    trompete INTEGER NOT NULL DEFAULT 0,
    trombone INTEGER NOT NULL DEFAULT 0,
    flugelhorn INTEGER NOT NULL DEFAULT 0,
    euphonium INTEGER NOT NULL DEFAULT 0,
    tuba INTEGER NOT NULL DEFAULT 0,
    trompete_cornet INTEGER NOT NULL DEFAULT 0,
    trompa INTEGER NOT NULL DEFAULT 0,
    trombonito INTEGER NOT NULL DEFAULT 0,
    baritono_pisto INTEGER NOT NULL DEFAULT 0,
    sax_horn INTEGER NOT NULL DEFAULT 0,

    -- Harmônico
    acordeon INTEGER NOT NULL DEFAULT 0,

    -- Organistas
    organistas INTEGER NOT NULL DEFAULT 0,

    -- Visitantes e hinos
    visitantes INTEGER NOT NULL DEFAULT 0,
    hinos_ensaiados TEXT,

    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Presença individual por músico/organista em cada culto (para o Relatório Mensal por nome)
CREATE TABLE IF NOT EXISTS presencas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    culto_id INTEGER NOT NULL REFERENCES cultos(id) ON DELETE CASCADE,
    musico_id INTEGER NOT NULL REFERENCES musicos(id) ON DELETE CASCADE,
    presente INTEGER NOT NULL DEFAULT 1
);
