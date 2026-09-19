-- Schema do banco para o app "Ensaio Local"
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

-- Um registro por Ensaio
CREATE TABLE IF NOT EXISTS ensaios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,                  -- formato YYYY-MM-DD
    dia_semana TEXT,                     -- ex: 'Domingo', 'Quinta-feira'
    tipo_ensaio TEXT,                    -- 'Local' ou 'Regional'

    -- Encarregados
    nome_encarregado_1 TEXT,
    localidade_1 TEXT,
    nome_encarregado_2 TEXT,
    localidade_2 TEXT,
    nome_encarregado_3 TEXT,
    localidade_3 TEXT,

    fora_do_padrao INTEGER NOT NULL DEFAULT 0,  -- 1 se foi criado em dia que não é o padrão

    -- Irmandade (sem instrumento)
    irmaos INTEGER NOT NULL DEFAULT 0,
    irmas INTEGER NOT NULL DEFAULT 0,

    -- Cordas
    violino INTEGER NOT NULL DEFAULT 0,
    viola INTEGER NOT NULL DEFAULT 0,
    violoncelo INTEGER NOT NULL DEFAULT 0,

    -- Madeiras
    flauta INTEGER NOT NULL DEFAULT 0,
    clarinete INTEGER NOT NULL DEFAULT 0,
    clarone INTEGER NOT NULL DEFAULT 0,
    sax_soprano INTEGER NOT NULL DEFAULT 0,
    sax_alto INTEGER NOT NULL DEFAULT 0,
    sax_tenor INTEGER NOT NULL DEFAULT 0,
    sax_baritono INTEGER NOT NULL DEFAULT 0,
    oboe INTEGER NOT NULL DEFAULT 0,
    oboe_damore INTEGER NOT NULL DEFAULT 0,
    corne_ingles INTEGER NOT NULL DEFAULT 0,
    clarinete_alto INTEGER NOT NULL DEFAULT 0,

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

    -- Ministério (não entra no total geral, só conferência)
    anciaes INTEGER NOT NULL DEFAULT 0,
    diaconos INTEGER NOT NULL DEFAULT 0,
    coop_of_ministerial INTEGER NOT NULL DEFAULT 0,
    coop_jovens_menores INTEGER NOT NULL DEFAULT 0,
    enc_regionais INTEGER NOT NULL DEFAULT 0,
    enc_locais INTEGER NOT NULL DEFAULT 0,
    examinadoras INTEGER NOT NULL DEFAULT 0,

    -- Visitantes e hinos
    visitantes INTEGER NOT NULL DEFAULT 0,
    hinos_ensaiados TEXT,

    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Presença individual por músico/organista em cada ensaio (para o Relatório Mensal por nome)
CREATE TABLE IF NOT EXISTS presencas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ensaio_id INTEGER NOT NULL REFERENCES ensaios(id) ON DELETE CASCADE,
    musico_id INTEGER NOT NULL REFERENCES musicos(id) ON DELETE CASCADE,
    presente INTEGER NOT NULL DEFAULT 1
);
