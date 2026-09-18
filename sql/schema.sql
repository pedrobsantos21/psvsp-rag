-- Rodar no SQL Editor do Supabase. Trocar a senha do llm_reader antes.

create table eixos (
  id_eixo text primary key,
  nome_eixo text not null,
  tipo_eixo text not null  -- 'Eixo estrutural' | 'Eixo temático' | 'Eixo transversal'
);

create table objetivos_estrategicos (
  id_oe text primary key,
  descricao_oe text not null,
  id_eixo text not null references eixos
);

create table acoes (
  id_acao text primary key,
  descricao_acao text not null,
  id_oe text not null references objetivos_estrategicos
);

create table acoes_eixos_transversais (
  id_acao text not null references acoes,
  id_eixo text not null references eixos,
  primary key (id_acao, id_eixo)
);

create table atores (
  id_ator text primary key,
  nome_ator text not null,
  presente_matriz_acoes boolean not null
);

create table detalhamento_atores (
  id_detalhamento text primary key,
  id_ator text not null references atores,
  nome_detalhamento text not null
);

create table produtos (
  id_produto text primary key,
  id_acao text not null references acoes,
  nome_produto text not null,
  id_ator_responsavel text references atores,
  id_detalhamento text references detalhamento_atores
);

create table envolvidos (
  id_produto text not null references produtos,
  id_ator text not null references atores,
  primary key (id_produto, id_ator)
);

create table indicadores_desempenho (
  id_indicador text primary key,
  id_oe text not null references objetivos_estrategicos,
  nome_indicador text not null,
  descricao_indicador text,
  formula text,
  fonte text,
  periodicidade text
);

create table indicadores_produtos (
  id_indicador text primary key,
  descricao_indicador text not null,
  id_produto text not null references produtos
);

create table metas (
  id_indicador text not null references indicadores_produtos,
  horizonte text not null,  -- '2027' | '2030' | '2035' | 'final'
  valor numeric not null,
  primary key (id_indicador, horizonte)
);

create table query_log (
  id serial primary key,
  ts timestamptz not null default now(),
  pergunta text,
  sql text not null,
  linhas int,
  erro text
);

-- Zera role e função, se existirem (permite rodar este bloco de novo)
drop function if exists run_sql(text, text);
do $$ begin
  if exists (select from pg_roles where rolname = 'llm_reader') then
    grant llm_reader to postgres;
    drop owned by llm_reader;
    drop role llm_reader;
  end if;
end $$;

-- Role read-only (sem login): dona da função run_sql, que roda com os privilégios dela
create role llm_reader nologin;
grant llm_reader to postgres;
grant usage, create on schema public to llm_reader;
grant select on all tables in schema public to llm_reader;
grant insert on query_log to llm_reader;
grant usage on sequence query_log_id_seq to llm_reader;

-- Executa um SELECT e loga em query_log. Chamada via REST: POST /rest/v1/rpc/run_sql
create function run_sql(pergunta text, query text) returns json
language plpgsql security definer set search_path = public as $$
declare
  result json;
  erro text;
begin
  set local statement_timeout = '10s';
  begin
    execute format('select json_agg(q) from (%s) q', query) into result;
  exception when others then
    erro := sqlerrm;
  end;
  insert into query_log (pergunta, sql, linhas, erro)
    values (pergunta, query, json_array_length(coalesce(result, '[]')), erro);
  if erro is not null then
    return json_build_object('erro', erro);
  end if;
  return json_build_object('linhas', coalesce(result, '[]'::json));
end $$;

alter function run_sql(text, text) owner to llm_reader;
revoke all on function run_sql(text, text) from public, anon, authenticated;
grant execute on function run_sql(text, text) to service_role;
