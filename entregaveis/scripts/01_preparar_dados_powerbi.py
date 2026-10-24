"""Exporta as tabelas do modelo Power BI a partir das tabelas processadas da E1.

Não recalcula regras de negócio: reaproveita data_processed/*.pkl (gerados pelos
notebooks 02-06), que já aplicam o filtro delivered + jan-ago, a avaliação mais
recente por pedido e o menor shipping_limit_date por pedido.

Saída: entregaveis/powerbi/dados/*.csv (UTF-8, vírgula, ponto decimal, datas ISO).
Uso (na raiz do projeto): python entregaveis/scripts/01_preparar_dados_powerbi.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from olist_utils import UF_REGIAO, load_processed  # noqa: E402

OUT = ROOT / "entregaveis" / "powerbi" / "dados"
OUT.mkdir(parents=True, exist_ok=True)

ORDEM_REGIAO = {"Norte": 1, "Nordeste": 2, "Centro-Oeste": 3, "Sudeste": 4, "Sul": 5}


def _bool(s: pd.Series) -> pd.Series:
    """Booleano anulável -> 'true'/'false'/'' (vazio vira null no Power Query)."""
    return s.astype("boolean").map({True: "true", False: "false"}).fillna("")


def _save(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8")
    print(f"{name:<14} {len(df):>7} linhas")


pedidos = load_processed("pedidos")
itens = load_processed("itens")
pedido_seller = load_processed("pedido_seller")

# Fato Pedidos: 1 linha por pedido entregue (KPI01, entrega atrasada, KPI03)
fp = pd.DataFrame({
    "id_pedido": pedidos["order_id"],
    "data_compra": pedidos["order_purchase_timestamp"].dt.strftime("%Y-%m-%d"),
    "uf_cliente": pedidos["customer_state"],
    "nota_avaliacao": pedidos["review_score"].astype("Int64"),
    "postagem_elegivel": _bool(pedidos["postagem_elegivel"]),
    "postagem_no_prazo": _bool(pedidos["postagem_no_prazo"]),
    "entrega_atrasada": _bool(pedidos["entrega_atrasada"]),
    "situacao_postagem": pedidos["situacao_postagem"].str.capitalize(),
    "situacao_entrega": pedidos["situacao_entrega"].str.capitalize(),
    "dias_postagem_entrega": pedidos["dias_postagem_entrega"].round(3),
    "qtd_sellers": pedidos["qtd_sellers"],
})
_save(fp, "pedidos")

# Fato Itens: 1 linha por item (KPI02 = soma frete / soma preço)
fi = pd.DataFrame({
    "id_pedido": itens["order_id"],
    "id_item": itens["order_item_id"],
    "data_compra": itens["order_id"].map(pedidos.set_index("order_id")["order_purchase_timestamp"]).dt.strftime("%Y-%m-%d"),
    "uf_cliente": itens["customer_state"],
    "id_seller": itens["seller_id"],
    "categoria": itens["categoria_en"],
    "preco": itens["price"].round(2),
    "frete": itens["freight_value"].round(2),
})
assert fi["data_compra"].notna().all()
_save(fi, "itens")

# Fato Pedido-Seller: 1 linha por par pedido x seller (ranking de sellers)
fs = pd.DataFrame({
    "id_pedido": pedido_seller["order_id"],
    "id_seller": pedido_seller["seller_id"],
    "data_compra": pedido_seller["order_id"].map(pedidos.set_index("order_id")["order_purchase_timestamp"]).dt.strftime("%Y-%m-%d"),
    "uf_cliente": pedido_seller["customer_state"],
    "postagem_elegivel": _bool(pedido_seller["postagem_elegivel"]),
    "postagem_atrasada": _bool(pedido_seller["postagem_atrasada"]),
    "avaliacao_ruim": _bool(pedido_seller["avaliacao_ruim"]),
})
assert fs["data_compra"].notna().all()
_save(fs, "pedido_seller")

# Dimensão Sellers (apenas sellers presentes no recorte)
ds = (pd.concat([itens[["seller_id", "seller_state", "seller_regiao"]],
                 pedido_seller[["seller_id", "seller_state", "seller_regiao"]]])
      .drop_duplicates("seller_id").sort_values("seller_id"))
ds = pd.DataFrame({
    "id_seller": ds["seller_id"],
    "seller": "Seller " + ds["seller_id"].str[:8],
    "uf_seller": ds["seller_state"],
    "regiao_seller": ds["seller_regiao"],
})
assert ds["seller"].is_unique
_save(ds, "sellers")

# Dimensão UF do cliente (27 UFs)
du = pd.DataFrame({"uf": list(UF_REGIAO), "regiao": list(UF_REGIAO.values())})
du["ordem_regiao"] = du["regiao"].map(ORDEM_REGIAO)
_save(du.sort_values(["ordem_regiao", "uf"]), "uf")

assert len(fp) == 74781 and fp["id_pedido"].is_unique
