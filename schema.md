# Schema — Plano de Segurança Viária do Estado de São Paulo (PSV-SP)

Banco PostgreSQL. Todos os IDs são `text`. Hierarquia principal:

```
eixos → objetivos_estrategicos → acoes → produtos → indicadores_produtos → metas
                               ↘ indicadores_desempenho
```

Convenção de IDs: `1` = eixo, `OE 1.1` = objetivo estratégico, `1.1.1` = ação, `1.1.1.1` = produto, `1.1.1.1.1` = indicador de produto. O prefixo numérico revela a hierarquia (ação `1.1.1` pertence ao eixo `1`).

## Tabelas

### eixos
Os 11 eixos do plano.
- `id_eixo` (pk): `1`..`8` para eixos estruturais/temáticos, `t1`..`t3` para transversais.
- `nome_eixo`
- `tipo_eixo`: `Eixo estrutural` (1, 2), `Eixo temático` (3–8), `Eixo transversal` (t1–t3).

Eixos transversais NÃO têm OEs próprios; ligam-se a ações via `acoes_eixos_transversais`.

### objetivos_estrategicos
- `id_oe` (pk): formato `OE 1.1` (com espaço).
- `descricao_oe`
- `id_eixo` → eixos

### acoes
- `id_acao` (pk): ex. `1.1.1`
- `descricao_acao`
- `id_oe` → objetivos_estrategicos

### acoes_eixos_transversais
Relação n:n entre ações e eixos transversais (t1, t2, t3).
- `id_acao` → acoes
- `id_eixo` → eixos

### atores
Órgãos/instituições (ALESP, ANTT, DETRAN-SP, ARTESP, etc).
- `id_ator` (pk): `A001`...
- `nome_ator`: sigla/nome.
- `presente_matriz_acoes` (bool): se aparece na matriz de ações (responsável ou envolvido).

### detalhamento_atores
Subunidades de um ator (ex.: superintendências da ARTESP).
- `id_detalhamento` (pk): `D001`...
- `id_ator` → atores
- `nome_detalhamento`

### produtos
Entregas concretas de cada ação.
- `id_produto` (pk): ex. `1.1.1.1`
- `id_acao` → acoes
- `nome_produto`
- `id_ator_responsavel` → atores (responsável principal)
- `id_detalhamento` → detalhamento_atores (subunidade responsável)

### envolvidos
Atores envolvidos (além do responsável) em cada produto. n:n.
- `id_produto` → produtos
- `id_ator` → atores

### indicadores_desempenho
Indicadores de resultado por objetivo estratégico.
- `id_indicador` (pk): ex. `1.1A`
- `id_oe` → objetivos_estrategicos
- `nome_indicador`, `descricao_indicador`, `formula`, `fonte`, `periodicidade`

### indicadores_produtos
Indicadores de entrega de cada produto (o que mede se o produto foi feito).
- `id_indicador` (pk): ex. `1.1.1.1.1`
- `descricao_indicador`
- `id_produto` → produtos

### metas
Valores-alvo dos indicadores de produto por horizonte.
- `id_indicador` → indicadores_produtos
- `horizonte`: `2027`, `2030`, `2035` ou `final` (meta ao fim do plano). Nem todo indicador tem todos os horizontes.
- `valor` (numeric): meta. Valores entre 0 e 1 geralmente são proporções.

## Dicionário de métricas
- **Nº de ações por eixo**: `acoes` → `objetivos_estrategicos` → `eixos`.
- **Nº de produtos por eixo/OE/ação**: `produtos` → `acoes` (→ OE → eixo).
- **Produtos de um ator**: como responsável (`produtos.id_ator_responsavel`) ou como envolvido (`envolvidos`). Diferencie os dois quando perguntarem.
- **Metas de um produto**: `metas` → `indicadores_produtos` → `produtos`.
- Buscas por nome de ator: use `ilike '%texto%'` em `nome_ator`; siglas são comuns (DETRAN-SP, ARTESP, DER).

## Exemplos

```sql
-- ações por eixo
select e.nome_eixo, count(*) as n_acoes
from acoes a join objetivos_estrategicos oe on oe.id_oe = a.id_oe
join eixos e on e.id_eixo = oe.id_eixo
group by e.id_eixo, e.nome_eixo order by e.id_eixo;

-- produtos sob responsabilidade do DETRAN-SP
select p.id_produto, p.nome_produto
from produtos p join atores at on at.id_ator = p.id_ator_responsavel
where at.nome_ator ilike '%detran%';

-- metas de um produto
select ip.id_indicador, ip.descricao_indicador, m.horizonte, m.valor
from metas m join indicadores_produtos ip on ip.id_indicador = m.id_indicador
where ip.id_produto = '1.1.1.1' order by m.horizonte;

-- ações ligadas ao eixo transversal t3
select a.id_acao, a.descricao_acao
from acoes_eixos_transversais x join acoes a on a.id_acao = x.id_acao
where x.id_eixo = 't3';
```
