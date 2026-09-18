"""Carrega os CSVs de data/ no Supabase via REST. Uso: uv run --env-file .env load_data.py"""
import csv
from pathlib import Path

from psvsp.supabase import post

# ordem respeita as FKs
TABELAS = [
    "eixos", "objetivos_estrategicos", "acoes", "acoes_eixos_transversais",
    "atores", "detalhamento_atores", "produtos", "envolvidos",
    "indicadores_desempenho", "indicadores_produtos", "metas",
]

# ponytail: upsert por PK, sem truncate; linhas removidas do CSV ficam no banco
for t in TABELAS:
    with open(Path("data", f"{t}.csv"), encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    post(t, linhas, prefer="resolution=merge-duplicates,return=minimal")
    print(f"{t}: {len(linhas)}")
