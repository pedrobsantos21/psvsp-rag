# psvsp

Chat de terminal que responde perguntas sobre o Plano de Segurança Viária do Estado de São Paulo (PSV-SP). O Claude gera SQL via tool use contra um Postgres no Supabase; cada query é validada no cliente (só SELECT, só tabelas permitidas) e executada no banco por uma função read-only com timeout e log.

## Setup

1. Crie um projeto no Supabase e rode `sql/schema.sql` no SQL Editor.
2. Copie `.env.example` para `.env` e preencha `SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `ANTHROPIC_API_KEY`.
3. `uv sync`
4. `uv run --env-file .env load_data.py` — carrega os CSVs de `data/`.

## Uso

```
uv run psvsp
```

Comandos no chat: `/ajuda`, `/sql` (queries da última pergunta), `/limpar` (zera o histórico), `/sair`.

## Testes

- `uv run pytest` — testes unitários da validação de SQL.
- `uv run python tests/eval.py` — eval end-to-end com perguntas reais (custa tokens).

## Estrutura

- `psvsp/chat.py` — loop de tool use e CLI.
- `psvsp/db.py` — validação (sqlglot) e limite de linhas.
- `psvsp/supabase.py` — cliente REST mínimo.
- `schema.md` — documentação do schema, embutida no system prompt.
- `sql/schema.sql` — tabelas, role `llm_reader` e RPC `run_sql`.
- `data/` — CSVs fonte.

## Interface web (Streamlit)

- Local: copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`, preencha (inclui `SENHA`, compartilhada com quem for usar) e rode `uv run streamlit run app.py`.
- Deploy: [share.streamlit.io](https://share.streamlit.io) → New app → repo/branch, main file `app.py`; cole o conteúdo do `secrets.toml` em Settings → Secrets.
