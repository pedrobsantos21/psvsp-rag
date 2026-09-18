"""Chat no terminal. Uso: uv run --env-file .env python -m psvsp.chat"""
from pathlib import Path

import anthropic

from psvsp.db import MAX_ROWS, run_query

SYSTEM = [
    {
        "type": "text",
        "text": (
            "Você é um assistente que responde perguntas sobre o Plano de Segurança Viária "
            "do Estado de São Paulo (PSV-SP) consultando um banco PostgreSQL via a tool run_query. "
            f"Escreva SQL Postgres apenas com SELECT; resultados são limitados a {MAX_ROWS} linhas, "
            "então agregue quando fizer sentido. Responda em português, de forma concisa, e cite "
            "os IDs (eixo, OE, ação, produto) quando relevante. Se a query der erro, corrija e tente de novo.\n\n"
            + (Path(__file__).parent.parent / "schema.md").read_text(encoding="utf-8")
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

TOOLS = [
    {
        "name": "run_query",
        "description": "Executa um SELECT no banco do PSV-SP e retorna colunas e linhas em JSON.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "Query SQL (Postgres), apenas SELECT."}},
            "required": ["sql"],
            "additionalProperties": False,
        },
    }
]

client = anthropic.Anthropic()


def responder(pergunta: str, messages: list | None = None) -> str:
    """Roda o loop de tool use até a resposta final. `messages` é mutado (histórico)."""
    if messages is None:
        messages = []
    messages.append({"role": "user", "content": pergunta})
    while True:
        resp = client.messages.create(
            model="claude-opus-5", max_tokens=16000, system=SYSTEM, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = run_query(pergunta, b.input["sql"])
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out,
                                "is_error": out.startswith('{"erro"')})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    hist: list = []
    while (q := input("> ").strip()) not in {"sair", "exit", ""}:
        print(responder(q, hist), "\n")
