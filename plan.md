## Visão geral

Infraestrutura em que um LLM se conecta a um banco de dados relacional (PostgreSQL via Supabase) para responder perguntas, gerar pesquisas e criar relatórios com base nos dados armazenados. A abordagem segue o padrão de tool use / function calling: o LLM não gera SQL livre contra o schema bruto, ele chama funções pré-validadas que executam queries controladas.

## Arquitetura

```
Usuário → API (FastAPI) → LLM (Anthropic SDK, tool use)
                              ↓
                        Tool: run_query
                              ↓
                   Validador de SQL (sqlglot)
                              ↓
                   Supabase Postgres (usuário read-only)
                              ↓
                   Resultado → LLM → Resposta formatada
```

### Camadas

1. **Banco de dados**: PostgreSQL no Supabase, com usuário dedicado somente leitura e views limpas expondo os dados já filtrados.
2. **Camada semântica**: documentação do schema (tabelas, colunas, relações) e dicionário de métricas, usada no system prompt do LLM.
3. **Orquestração**: LLM com tool use, validação de SQL antes da execução, limite de linhas e timeout.
4. **Governança**: logging de queries geradas e executadas, rate limiting.
5. **Avaliação**: conjunto de perguntas de teste com resposta esperada conhecida.

## Passos do MVP

- [ ]  **Preparar o banco no Supabase**: criar usuário Postgres com permissão apenas de SELECT, restrito às tabelas/views necessárias. Criar views limpas em vez de expor tabelas de produção diretamente.
- [ ]  **Documentar o schema**: arquivo Markdown/YAML/JSON descrevendo tabelas, colunas, relações e um dicionário de métricas.
- [ ]  **Criar a função de execução segura de SQL**: validação via `sqlglot` (apenas SELECT, apenas tabelas permitidas), limite de linhas e timeout.
- [ ]  **Configurar tool use no LLM**: definir a tool `run_query` com schema JSON, incluir a documentação do schema no system prompt.
- [ ]  **Montar o loop de orquestração**: API recebe a pergunta, chama o LLM, executa a tool call, devolve o resultado pro LLM, que formata a resposta final.
- [ ]  **Montar um conjunto de testes**: 10 a 20 perguntas reais com resposta correta conhecida, pra medir taxa de acerto.
- [ ]  **Adicionar logging básico**: registrar pergunta, SQL gerado e resultado numa tabela própria no Supabase.
- [ ]  **Montar uma interface mínima**: Streamlit, chat via terminal, ou página HTML simples.

## Stack técnica (Python)

| Etapa | Biblioteca |
| --- | --- |
| Conexão com o banco | `psycopg` (v3) ou `asyncpg`; alternativa: `supabase-py` |
| Validação de SQL | `sqlglot` |
| Chamada ao LLM / tool use | `anthropic` (SDK oficial) |
| API / orquestração | `FastAPI` |
| Testes | `pytest` |
| Logging | insert via `psycopg`/`asyncpg` ou `supabase-py` |
| Interface mínima | `Streamlit` |

## Exemplo: validação de SQL

```python
import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"sinistros", "vw_sinistros_resumo"}

def validar_query(sql: str) -> bool:
    """
    Valida se uma query SQL é segura para execução em modo somente leitura.

    Verifica que o comando é um SELECT e que todas as tabelas referenciadas
    estão na lista de tabelas/views permitidas.

    Args:
        sql: string contendo a query gerada pelo LLM.

    Returns:
        True se a query for válida, False caso contrário.
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
    except Exception:
        return False

    if not isinstance(parsed, exp.Select):
        return False

    tabelas = {t.name for t in parsed.find_all(exp.Table)}
    return tabelas.issubset(ALLOWED_TABLES)
```

## Próximos passos (pós-MVP)

- Row-level security no Supabase, se diferentes usuários precisarem ver subconjuntos diferentes dos dados.
- Cache de queries e respostas frequentes.
- Camada semântica mais robusta (ex: dbt) se o schema crescer em complexidade.
- Revisão periódica de queries que falharam, pra refinar a documentação do schema.
