"""Carrega os CSVs de data/ no Postgres. Uso: uv run --env-file .env load_data.py"""
import os
from pathlib import Path

import psycopg

# ordem respeita as FKs
TABELAS = [
    "eixos", "objetivos_estrategicos", "acoes", "acoes_eixos_transversais",
    "atores", "detalhamento_atores", "produtos", "envolvidos",
    "indicadores_desempenho", "indicadores_produtos", "metas",
]

with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    cur.execute("truncate " + ", ".join(TABELAS) + " cascade")
    for t in TABELAS:
        with cur.copy(f"copy {t} from stdin with (format csv, header)") as copy:
            copy.write(Path("data", f"{t}.csv").read_bytes())
        cur.execute(f"select count(*) from {t}")
        print(f"{t}: {cur.fetchone()[0]}")
