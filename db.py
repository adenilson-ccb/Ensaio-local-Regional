"""
Camada de acesso ao banco de dados (Turso/libsql).

Configuração esperada em .streamlit/secrets.toml:

    TURSO_DATABASE_URL = "libsql://SEU-BANCO-novo.turso.io"
    TURSO_AUTH_TOKEN   = "SEU_TOKEN_AQUI"
    APP_PASSWORD       = "senha-compartilhada-das-6-pessoas"
"""

import streamlit as st
import libsql_client
from datetime import date


def get_client():
    """Cria uma conexão nova com o banco Turso a cada chamada (padrão recomendado
    para apps Streamlit, que reexecutam o script a cada interação)."""
    return libsql_client.create_client_sync(
        url=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"],
    )


def init_db():
    """Cria as tabelas caso ainda não existam. Chamar uma vez no início do app."""
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    client = get_client()
    try:
        for statement in schema.split(";"):
            statement = statement.strip()
            if statement:
                client.execute(statement)
    finally:
        client.close()


# ---------- Músicos ----------

def listar_musicos(apenas_ativos: bool = True):
    client = get_client()
    try:
        query = "SELECT id, nome, instrumento, categoria, nivel, ativo FROM musicos"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome"
        rs = client.execute(query)
        return [dict(zip(rs.columns, row)) for row in rs.rows]
    finally:
        client.close()


def cadastrar_musico(nome, instrumento, categoria, nivel):
    client = get_client()
    try:
        client.execute(
            "INSERT INTO musicos (nome, instrumento, categoria, nivel) VALUES (?, ?, ?, ?)",
            [nome, instrumento, categoria, nivel],
        )
    finally:
        client.close()


# ---------- Cultos ----------

def salvar_culto(dados: dict, presencas_ids: list[int]):
    """Salva um novo registro de culto/ensaio e as presenças individuais marcadas."""
    client = get_client()
    try:
        colunas = ", ".join(dados.keys())
        placeholders = ", ".join(["?"] * len(dados))
        rs = client.execute(
            f"INSERT INTO cultos ({colunas}) VALUES ({placeholders})",
            list(dados.values()),
        )
        culto_id = rs.last_insert_rowid

        for musico_id in presencas_ids:
            client.execute(
                "INSERT INTO presencas (culto_id, musico_id, presente) VALUES (?, ?, 1)",
                [culto_id, musico_id],
            )
        return culto_id
    finally:
        client.close()


def listar_cultos(limite: int = 20):
    client = get_client()
    try:
        rs = client.execute(
            "SELECT * FROM cultos ORDER BY data DESC, id DESC LIMIT ?", [limite]
        )
        return [dict(zip(rs.columns, row)) for row in rs.rows]
    finally:
        client.close()


def culto_existe_no_dia(data_str: str) -> bool:
    client = get_client()
    try:
        rs = client.execute("SELECT COUNT(*) FROM cultos WHERE data = ?", [data_str])
        return rs.rows[0][0] > 0
    finally:
        client.close()


# ---------- Relatório mensal ----------

def relatorio_mensal(ano: int, mes: int):
    client = get_client()
    try:
        mes_str = f"{ano:04d}-{mes:02d}"
        rs_cultos = client.execute(
            "SELECT id, data FROM cultos WHERE data LIKE ? ORDER BY data",
            [f"{mes_str}-%"],
        )
        cultos = [dict(zip(rs_cultos.columns, row)) for row in rs_cultos.rows]
        total_cultos = len(cultos)

        rs = client.execute(
            """
            SELECT m.id, m.nome, m.instrumento, m.categoria, m.nivel,
                   COUNT(p.id) AS presencas
            FROM musicos m
            LEFT JOIN presencas p ON p.musico_id = m.id
                AND p.culto_id IN (
                    SELECT id FROM cultos WHERE data LIKE ?
                )
            WHERE m.ativo = 1
            GROUP BY m.id
            ORDER BY m.nome
            """,
            [f"{mes_str}-%"],
        )
        linhas = [dict(zip(rs.columns, row)) for row in rs.rows]
        for linha in linhas:
            linha["total_cultos"] = total_cultos
            linha["percentual"] = (
                round(100 * linha["presencas"] / total_cultos) if total_cultos else 0
            )
        return total_cultos, linhas
    finally:
        client.close()
