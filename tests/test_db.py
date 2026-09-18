from psvsp.db import limitar, validar_query


def test_select_valido():
    assert validar_query("select * from acoes a join eixos e on true") is None


def test_cte_e_union():
    assert validar_query("with t as (select 1 from acoes) select * from t union select 2 from eixos") is None


def test_tabela_nao_permitida():
    assert "query_log" in validar_query("select * from query_log")
    assert "pg_tables" in validar_query("select * from pg_tables")


def test_apenas_select():
    for sql in ["delete from acoes", "update acoes set id_acao = 1", "drop table acoes", "insert into acoes values (1)"]:
        assert validar_query(sql) == "Apenas SELECT é permitido"


def test_sql_invalido():
    assert validar_query("select * from").startswith("SQL inválido")
    assert validar_query("selec * fro acoes") is not None


def test_limitar_preserva_limit_interno():
    sql = limitar("select * from acoes limit 5")
    assert sql == "SELECT * FROM (SELECT * FROM acoes LIMIT 5) AS q LIMIT 200"
