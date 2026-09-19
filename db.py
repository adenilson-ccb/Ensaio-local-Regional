"""
Camada de acesso ao banco de dados (Turso), usando a API HTTP oficial
diretamente (endpoint /v2/pipeline), em vez da biblioteca libsql_client
que estava causando um KeyError confuso ao esconder o erro real do SQL.

Configuração esperada em .streamlit/secrets.toml:

    TURSO_DATABASE_URL = "libsql://SEU-BANCO.turso.io"
    TURSO_AUTH_TOKEN   = "SEU_TOKEN_AQUI"
    APP_PASSWORD       = "senha-compartilhada-das-6-pessoas"
"""

import streamlit as st
import requests


# ---------- Infraestrutura HTTP ----------

def _base_url() -> str:
    url = st.secrets["TURSO_DATABASE_URL"]
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    return url.rstrip("/")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {st.secrets['TURSO_AUTH_TOKEN']}",
        "Content-Type": "application/json",
    }


def _to_arg(value):
    """Converte um valor Python para o formato de argumento tipado que a API do Turso espera."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "text", "value": str(value)}


def _from_cell(cell: dict):
    """Converte uma célula retornada pela API do Turso de volta para um valor Python simples."""
    if cell is None or cell.get("type") == "null":
        return None
    valor = cell.get("value")
    if cell.get("type") == "integer":
        try:
            return int(valor)
        except (TypeError, ValueError):
            return valor
    if cell.get("type") == "float":
        try:
            return float(valor)
        except (TypeError, ValueError):
            return valor
    return valor


def _rows_to_dicts(result: dict) -> list[dict]:
    cols = [c["name"] for c in result.get("cols", [])]
    return [
        {cols[i]: _from_cell(cell) for i, cell in enumerate(row)}
        for row in result.get("rows", [])
    ]


def _execute(sql: str, args: list | None = None) -> dict:
    """Executa uma única instrução SQL via API HTTP do Turso.

    Levanta um RuntimeError com a mensagem de erro REAL vinda do Turso
    caso o SQL falhe, em vez de um KeyError confuso.
    """
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {"sql": sql, "args": [_to_arg(a) for a in (args or [])]},
            },
            {"type": "close"},
        ]
    }

    resp = requests.post(
        f"{_base_url()}/v2/pipeline",
        headers=_headers(),
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Turso respondeu HTTP {resp.status_code} ao executar SQL.\n"
            f"SQL: {sql}\n"
            f"Resposta: {resp.text[:2000]}"
        )

    data = resp.json()
    primeiro_resultado = data["results"][0]

    if primeiro_resultado.get("type") == "error":
        erro = primeiro_resultado.get("error", {})
        mensagem = erro.get("message", str(erro)) if isinstance(erro, dict) else str(erro)
        raise RuntimeError(f"Erro do Turso ao executar SQL:\n{mensagem}\n\nSQL: {sql}")

    return primeiro_resultado["response"]["result"]


def init_db():
    """Cria as tabelas caso ainda não existam. Chamar uma vez no início do app."""
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    for statement in schema.split(";"):
        statement = statement.strip()
        if statement:
            _execute(statement)


# ---------- Músicos ----------

def listar_musicos(apenas_ativos: bool = True):
    query = "SELECT id, nome, instrumento, categoria, nivel, ativo FROM musicos"
    if apenas_ativos:
        query += " WHERE ativo = 1"
    query += " ORDER BY nome"
    result = _execute(query)
    return _rows_to_dicts(result)


def cadastrar_musico(nome, instrumento, categoria, nivel):
    _execute(
        "INSERT INTO musicos (nome, instrumento, categoria, nivel) VALUES (?, ?, ?, ?)",
        [nome, instrumento, categoria, nivel],
    )


# ---------- Cultos ----------

def salvar_culto(dados: dict, presencas_ids: list[int]):
    """Salva um novo registro de culto/ensaio e as presenças individuais marcadas."""
    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?"] * len(dados))

    result = _execute(
        f"INSERT INTO cultos ({colunas}) VALUES ({placeholders})",
        list(dados.values()),
    )
    culto_id = result.get("last_insert_rowid")
    if culto_id is not None:
        culto_id = int(culto_id)

    for musico_id in presencas_ids:
        _execute(
            "INSERT INTO presencas (culto_id, musico_id, presente) VALUES (?, ?, 1)",
            [culto_id, musico_id],
        )

    return culto_id


def listar_cultos(limite: int = 20):
    result = _execute(
        "SELECT * FROM cultos ORDER BY data DESC, id DESC LIMIT ?", [limite]
    )
    return _rows_to_dicts(result)


def culto_existe_no_dia(data_str: str) -> bool:
    result = _execute("SELECT COUNT(*) AS total FROM cultos WHERE data = ?", [data_str])
    linhas = _rows_to_dicts(result)
    return bool(linhas and linhas[0].get("total"))


# ---------- Relatório mensal ----------

def relatorio_mensal(ano: int, mes: int):
    mes_str = f"{ano:04d}-{mes:02d}"

    result_cultos = _execute(
        "SELECT id, data FROM cultos WHERE data LIKE ? ORDER BY data",
        [f"{mes_str}-%"],
    )
    cultos = _rows_to_dicts(result_cultos)
    total_cultos = len(cultos)

    result = _execute(
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
    linhas = _rows_to_dicts(result)
    for linha in linhas:
        presencas = linha.get("presencas") or 0
        linha["presencas"] = presencas
        linha["total_cultos"] = total_cultos
        linha["percentual"] = round(100 * presencas / total_cultos) if total_cultos else 0

    return total_cultos, linhas
