"""Chat no terminal. Uso: uv run psvsp"""
import os
import readline  # noqa: F401  (histórico e setas no input)
import urllib.error
from collections.abc import Callable
from pathlib import Path

import anthropic
from rich.console import Console
from rich.markdown import Markdown

from psvsp.db import MAX_ROWS, run_query

RAIZ = Path(__file__).parent.parent

# ponytail: parser de .env sem aspas nem comentário inline; trocar por python-dotenv se precisar
for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines() if (RAIZ / ".env").exists() else []:
    if linha.strip() and not linha.lstrip().startswith("#"):
        k, _, v = linha.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

SYSTEM = [
    {
        "type": "text",
        "text": (
            "Você é um assistente que responde perguntas sobre o Plano de Segurança Viária "
            "do Estado de São Paulo (PSV-SP) consultando um banco PostgreSQL via a tool run_query. "
            f"Escreva SQL Postgres apenas com SELECT; resultados são limitados a {MAX_ROWS} linhas, "
            "então agregue quando fizer sentido. Responda em português, de forma concisa, e cite "
            "os IDs (eixo, OE, ação, produto) quando relevante. Se a query der erro, corrija e tente de novo.\n\n"
            + (RAIZ / "schema.md").read_text(encoding="utf-8")
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

TOOLS = [
    {
        "name": "run_query",
        "description": "Executa um SELECT no banco do PSV-SP e retorna as linhas em JSON.",
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


def responder(pergunta: str, messages: list | None = None, on_sql: Callable[[str], None] | None = None) -> str:
    """Roda o loop de tool use até a resposta final. `messages` é mutado (histórico)."""
    if messages is None:
        messages = []
    messages.append({"role": "user", "content": pergunta})
    while True:
        resp = client.messages.create(
            model="claude-haiku-4-5", max_tokens=16000, system=SYSTEM, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                if on_sql:
                    on_sql(b.input["sql"])
                out = run_query(pergunta, b.input["sql"])
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out,
                                "is_error": out.startswith('{"erro"')})
        messages.append({"role": "user", "content": results})


AJUDA = "/ajuda  /sql (queries da última pergunta)  /limpar (zera o histórico)  /sair"


def main() -> None:
    console = Console()
    hist: list = []
    sqls: list[str] = []
    console.print("[bold]PSV-SP[/] — pergunte sobre o plano. [dim]/ajuda para comandos[/]")
    while True:
        try:
            q = console.input("\n[bold cyan]> [/]").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q:
            continue
        if q in {"/sair", "sair", "exit"}:
            break
        if q == "/ajuda":
            console.print(AJUDA)
        elif q == "/limpar":
            hist.clear(); sqls.clear()
            console.print("[dim]histórico limpo[/]")
        elif q == "/sql":
            console.print("\n\n".join(sqls) or "[dim]nenhuma query ainda[/]")
        elif q.startswith("/"):
            console.print(f"[red]comando desconhecido[/] — {AJUDA}")
        else:
            sqls.clear()
            n = len(hist)
            try:
                with console.status("Pensando...") as status:
                    def on_sql(sql: str) -> None:
                        status.update("Consultando banco...")
                        sqls.append(sql)
                        console.print(f"[dim]{sql}[/]")
                    resp = responder(q, hist, on_sql)
                console.print(Markdown(resp))
            except (anthropic.APIError, urllib.error.HTTPError, OSError) as e:
                del hist[n:]
                console.print(f"[red]erro:[/] {e}")
    console.print("[dim]tchau[/]")


if __name__ == "__main__":
    main()
