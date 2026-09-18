import json
import os

import psycopg
import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {
    "eixos", "objetivos_estrategicos", "acoes", "acoes_eixos_transversais",
    "atores", "detalhamento_atores", "produtos", "envolvidos",
    "indicadores_desempenho", "indicadores_produtos", "metas",
}
MAX_ROWS = 200


def validar_query(sql: str) -> str | None:
    """Retorna None se a query é um SELECT sobre tabelas permitidas, senão o motivo."""
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except Exception as e:
        return f"SQL inválido: {e}"
    if not isinstance(parsed, exp.Query):
        return "Apenas SELECT é permitido"
    ctes = {c.alias for c in parsed.find_all(exp.CTE)}
    tabelas = {t.name for t in parsed.find_all(exp.Table)} - ctes
    if extra := tabelas - ALLOWED_TABLES:
        return f"Tabelas não permitidas: {sorted(extra)}"
    return None


def limitar(sql: str) -> str:
    parsed = sqlglot.parse_one(sql, dialect="postgres")
    return exp.select("*").from_(parsed.subquery("q")).limit(MAX_ROWS).sql(dialect="postgres")


def run_query(pergunta: str, sql: str) -> str:
    """Valida, executa e loga. Retorna JSON com colunas/linhas ou erro."""
    erro = validar_query(sql)
    colunas, linhas = [], []
    if not erro:
        # ponytail: conexão nova por query; pool quando houver concorrência
        try:
            with psycopg.connect(os.environ["LLM_DATABASE_URL"]) as conn, conn.cursor() as cur:
                cur.execute(limitar(sql))
                colunas = [d.name for d in cur.description]
                linhas = cur.fetchall()
        except psycopg.Error as e:
            erro = str(e).strip()
    with psycopg.connect(os.environ["LLM_DATABASE_URL"]) as conn:
        conn.execute(
            "insert into query_log (pergunta, sql, linhas, erro) values (%s, %s, %s, %s)",
            (pergunta, sql, len(linhas) if not erro else None, erro),
        )
    if erro:
        return json.dumps({"erro": erro}, ensure_ascii=False)
    return json.dumps({"colunas": colunas, "linhas": linhas}, ensure_ascii=False, default=str)
