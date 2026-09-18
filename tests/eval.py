"""Eval manual (custa tokens): uv run python tests/eval.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from psvsp.chat import responder  # noqa: E402

# (pergunta, trecho que deve aparecer na resposta) — valores conferidos nos CSVs
CASOS = [
    ("Quantos eixos temáticos existem?", "6"),
    ("Quantos objetivos estratégicos o plano tem?", "25"),
    ("Quantas ações o plano tem no total?", "98"),
    ("Quantos produtos existem no total?", "308"),
    ("Quantas ações tem o OE 1.1?", "6"),
    ("Qual eixo tem mais ações e quantas?", "Fiscalização"),
    ("Quantos produtos tem o eixo 4 (Educação)?", "30"),
    ("Qual ator é responsável por mais produtos e por quantos?", "165"),
    ("Quantos produtos o DER-SP é responsável?", "34"),
    ("Quais atores não estão presentes na matriz de ações?", "Prodesp"),
    ("Quantas ações estão ligadas ao eixo transversal t3?", "64"),
    ("Quantas metas existem para o horizonte 2035?", "122"),
    ("Quais os indicadores de desempenho do OE 1.1?", "maturidade da governança"),
    ("Quais os OEs do eixo Atendimento às vítimas?", "OE 8.4"),
    ("Quais os produtos da ação 3.1.1?", "3.1.1.3"),
    ("Quais as subunidades (detalhamentos) da ARTESP?", "SUCOL"),
    ("Qual indicador de produto tem a maior meta final?", "1.2.3.4.2"),
]

acertos = 0
for pergunta, esperado in CASOS:
    resposta = responder(pergunta)
    ok = esperado.lower() in resposta.lower()
    acertos += ok
    print(f"[{'OK' if ok else 'XX'}] {pergunta}\n    -> {resposta[:200]!r}\n")
print(f"{acertos}/{len(CASOS)} ({100 * acertos // len(CASOS)}%)")
