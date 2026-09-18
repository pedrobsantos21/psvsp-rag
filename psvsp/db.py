import json

import sqlglot
from sqlglot import exp

from psvsp.supabase import post

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
    """Valida e executa via rpc run_sql (que roda como llm_reader e loga). Retorna JSON."""
    if erro := validar_query(sql):
        return json.dumps({"erro": erro}, ensure_ascii=False)
    return json.dumps(post("rpc/run_sql", {"pergunta": pergunta, "query": limitar(sql)}), ensure_ascii=False)
