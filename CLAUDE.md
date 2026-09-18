# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

Chat de terminal (Python 3.13, `uv`) em que Claude responde perguntas sobre o Plano de Segurança Viária do Estado de São Paulo (PSV-SP) gerando SQL via tool use contra um Postgres no Supabase. Código, comentários, prompts e testes são em português.

## Comandos

- `uv sync` — instala deps (inclui grupo `dev` com pytest).
- `uv run psvsp` — abre o chat (entry point `psvsp.chat:main`). Precisa de `.env` (copiar de `.env.example`); `chat.py` carrega o `.env` sozinho.
- `uv run pytest` — testes unitários (só `tests/test_db.py`, sem rede).
- `uv run pytest tests/test_db.py::test_cte_e_union` — um teste.
- `uv run python tests/eval.py` — eval end-to-end com perguntas reais; chama a API da Anthropic e o banco (custa tokens). Não é coletado pelo pytest.
- `uv run --env-file .env load_data.py` — carrega os CSVs de `data/` no Supabase (upsert por PK, ordem respeita FKs).
- `sql/schema.sql` — roda manualmente no SQL Editor do Supabase; recria tabelas, a role `llm_reader` e a função `run_sql`.

## Arquitetura

Fluxo: `chat.py` (loop de tool use, modelo `claude-haiku-4-5`) → tool `run_query` → `db.py` (valida com sqlglot, envolve em subquery com `LIMIT 200`) → `supabase.py` (`post` via urllib na REST `/rest/v1/`) → RPC `run_sql` no Postgres.

Segurança em duas camadas, ambas obrigatórias:
1. **Cliente** (`psvsp/db.py`): `validar_query` aceita só `exp.Query` (SELECT/CTE/UNION) e tabelas em `ALLOWED_TABLES` (CTEs são descontadas). `query_log` e catálogos `pg_*` ficam de fora.
2. **Banco** (`sql/schema.sql`): `run_sql` é `security definer` de propriedade da role `llm_reader` (só SELECT + insert em `query_log`), `statement_timeout` de 10s, e loga toda query com a pergunta original. Só `service_role` pode executá-la.

O system prompt em `chat.py` embute `schema.md` inteiro (com `cache_control`). `schema.md` é a camada semântica: descreve tabelas, convenção de IDs hierárquicos (`1` → `OE 1.1` → `1.1.1` → `1.1.1.1` → `1.1.1.1.1`) e dicionário de métricas. Ao mudar tabela/coluna, atualizar `sql/schema.sql`, `schema.md`, `ALLOWED_TABLES` em `db.py`, `TABELAS` em `load_data.py` e o CSV correspondente em `data/`.

`responder()` em `chat.py` é a função pura de orquestração (histórico mutável + callback `on_sql`); `main()` só cuida do CLI (rich, comandos `/ajuda /sql /limpar /sair`). `tests/eval.py` usa `responder()` direto.

## Convenções

- Projeto segue o estilo "ponytail": mínimo de código, stdlib antes de dependência (urllib em vez de supabase-py, parser de `.env` manual). Comentários `# ponytail:` marcam atalhos deliberados e o caminho de upgrade — manter esse padrão.
- `plan.md` é o plano original do MVP (FastAPI, rate limiting etc. ainda não existem; o CLI substituiu a API).
