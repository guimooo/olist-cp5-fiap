"""Testes das regras críticas de olist_utils com dados sintéticos pequenos.

Rodar na raiz do projeto:  python tests/test_regras.py   (ou python -m pytest tests -q, se tiver pytest)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import olist_utils as U  # noqa: E402


def test_avaliacao_mais_recente_com_desempate():
    r = pd.DataFrame({
        "review_id": ["a", "b", "c", "d", "e"],
        "order_id": ["o1", "o1", "o2", "o2", "o3"],
        "review_score": [5, 1, 4, 2, 3],
        "review_creation_date": pd.to_datetime(["2018-01-01", "2018-02-01", "2018-03-01", "2018-03-01", "2018-01-01"]),
        "review_answer_timestamp": pd.to_datetime(["2018-01-02", "2018-02-02", "2018-03-02", "2018-03-05", "2018-01-02"]),
    })
    out = U.latest_review_per_order(r).set_index("order_id")["review_id"]
    assert out["o1"] == "b"          # data de criação mais recente
    assert out["o2"] == "d"          # empate na criação -> resposta mais recente
    assert out["o3"] == "e"
    assert out.index.is_unique


def test_pct_denominador_zero_e_limites():
    assert U.pct(1, 4) == 25.0
    assert np.isnan(U.pct(0, 0))
    v = U.pct(pd.Series([0, 5]), pd.Series([10, 5]))
    assert list(v) == [0.0, 100.0]


def test_kpi_frete_soma_no_nivel_item():
    itens = pd.DataFrame({"order_id": ["o1", "o1", "o2"], "order_item_id": [1, 2, 1],
                          "price": [100.0, 100.0, 50.0], "freight_value": [10.0, 10.0, 30.0], "g": ["x", "x", "y"]})
    tot = U.kpi_frete(itens)
    assert tot.loc[0, "kpi2_pct_frete_sobre_produto"] == 50 / 250 * 100
    por = U.kpi_frete(itens, "g").set_index("g")["kpi2_pct_frete_sobre_produto"]
    assert por["x"] == 10.0 and por["y"] == 60.0


def test_kpi_pedidos_numeradores_e_denominadores():
    ped = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4"],
        "tem_avaliacao": [True, True, True, False],
        "avaliacao_ruim": pd.array([True, False, False, pd.NA], dtype="boolean"),
        "postagem_elegivel": [True, True, False, True],
        "postagem_no_prazo": pd.array([True, False, pd.NA, True], dtype="boolean"),
        "entrega_atrasada": pd.array([True, False, False, pd.NA], dtype="boolean"),
    })
    k = U.kpi_pedidos(ped).iloc[0]
    assert k["pedidos_com_avaliacao"] == 3 and k["pedidos_avaliacao_ruim"] == 1   # sem avaliação fora do denominador
    assert k["pedidos_postagem_elegiveis"] == 3 and k["pedidos_postagem_no_prazo"] == 2
    assert k["pedidos_entrega_avaliavel"] == 3 and k["pedidos_entrega_atrasada"] == 1
    assert k["pedidos_sem_avaliacao"] == 1


def test_mapa_uf_regiao_completo():
    assert len(U.UF_REGIAO) == 27
    assert set(U.UF_REGIAO.values()) == {"Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"}


def test_fronteira_postagem_no_limite_conta_no_prazo():
    limite = pd.Timestamp("2018-01-10 12:00:00")
    assert pd.Timestamp("2018-01-10 12:00:00") <= limite         # exatamente no limite: no prazo
    assert not (pd.Timestamp("2018-01-10 12:00:01") <= limite)   # 1 segundo depois: atrasada


if __name__ == "__main__":  # permite rodar sem pytest: python tests/test_regras.py
    testes = [f for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for f in testes:
        f()
        print("ok", f.__name__)
    print(f"{len(testes)} testes passaram")
