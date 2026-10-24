"""Funções reutilizáveis do projeto Olist (CP5 FIAP).

Centraliza caminhos, leitura dos CSVs, mapeamentos e o cálculo dos KPIs para
que os notebooks não dupliquem lógica. Todos os notebooks importam daqui.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT                       # CSVs originais ficam na raiz do projeto
PROCESSED_DIR = ROOT / "data_processed"
DASHBOARD_DIR = ROOT / "output" / "dashboard"
FIG_DIR = ROOT / "output" / "figuras"
for _d in (PROCESSED_DIR, DASHBOARD_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

RAW_FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

DATE_COLS = {
    "orders": ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date"],
    "items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# ---------------------------------------------------------------------------
# Premissa temporal (proxy acadêmica) e metas da proposta
# ---------------------------------------------------------------------------
MESES_RECORTE = list(range(1, 9))  # janeiro a agosto
PERIODOS = {
    2017: "2024 (proxy jan-ago/2017)",
    2018: "2025 (proxy jan-ago/2018)",
}
CHECK_PEDIDOS_PROPOSTA = {2017: 21998, 2018: 52783}

# Valores de referência da proposta (NÃO são resultados calculados)
REFERENCIAS = {
    "kpi1_pct_avaliacao_ruim": {"ref_2024": 10.6, "ref_2025": 13.4, "meta_2026": 12.0, "meta_2027": 10.0},
    "kpi2_pct_frete_sobre_produto": {"ref_2024": 16.0, "ref_2025": 17.1, "meta_2026": 17.1, "meta_2027": 17.1},
    "kpi3_pct_postagem_no_prazo": {"ref_2024": 91.4, "ref_2025": 91.5, "meta_2026": 95.0, "meta_2027": 97.0},
}
REF_FRETE_REGIAO_2025 = {"Norte": 23.9, "Nordeste": 22.7, "Sudeste": 15.5}

MIN_AMOSTRA = 30  # grupos com denominador menor que isso recebem flag amostra_pequena

# ---------------------------------------------------------------------------
# Mapa UF -> região (27 UFs, explícito)
# ---------------------------------------------------------------------------
UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}
assert len(UF_REGIAO) == 27


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def load_raw(name: str, parse_dates: bool = True) -> pd.DataFrame:
    """Lê um CSV original. IDs e CEPs como texto para não perder zeros à esquerda."""
    path = RAW_DIR / RAW_FILES[name]
    dtype = {c: "string" for c in ("customer_zip_code_prefix", "seller_zip_code_prefix",
                                   "geolocation_zip_code_prefix")}
    df = pd.read_csv(path, dtype=dtype, encoding="utf-8-sig")
    if parse_dates:
        for c in DATE_COLS.get(name, []):
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def save_processed(df: pd.DataFrame, name: str) -> Path:
    path = PROCESSED_DIR / f"{name}.pkl"
    df.to_pickle(path)
    return path


def load_processed(name: str) -> pd.DataFrame:
    return pd.read_pickle(PROCESSED_DIR / f"{name}.pkl")


def export_csv(df: pd.DataFrame, name: str) -> Path:
    """Exporta CSV para o dashboard: separador vírgula, ponto decimal, UTF-8."""
    path = DASHBOARD_DIR / f"{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------------------
def latest_review_per_order(reviews: pd.DataFrame) -> pd.DataFrame:
    """Uma avaliação por pedido: a mais recente por review_creation_date.

    Desempate determinístico: review_answer_timestamp mais recente e, se ainda
    empatar, maior review_id (ordem lexicográfica).
    """
    r = reviews.sort_values(
        ["order_id", "review_creation_date", "review_answer_timestamp", "review_id"],
        ascending=[True, False, False, False],
        na_position="last",
    )
    return r.drop_duplicates("order_id", keep="first")


def pct(num, den):
    """Percentual seguro (0-100). Retorna NaN quando o denominador é 0."""
    num = np.asarray(num, dtype="float64")
    den = np.asarray(den, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den > 0, num / den * 100, np.nan)
    return out if out.ndim else float(out)


def _flag(s: pd.Series) -> pd.Series:
    """Booleano anulável -> 0/1, tratando ausente como 0 (o denominador é contado à parte)."""
    return s.astype("boolean").fillna(False).astype(int)


def kpi_pedidos(pedidos: pd.DataFrame, by=None) -> pd.DataFrame:
    """KPI1, KPI3 e métricas de entrega a partir da tabela de PEDIDOS (1 linha/pedido).

    Espera as colunas: order_id, tem_avaliacao, avaliacao_ruim, postagem_elegivel,
    postagem_no_prazo, entrega_atrasada (bool/NaN), dias_atraso_entrega.
    """
    by = [by] if isinstance(by, str) else (by or [])
    df = pedidos.copy()
    df["_one"] = 1
    df["_ruim"] = _flag(df["avaliacao_ruim"])
    df["_aval"] = df["tem_avaliacao"].astype(int)
    df["_eleg"] = df["postagem_elegivel"].astype(int)
    df["_prazo"] = _flag(df["postagem_no_prazo"])
    df["_entrega_valida"] = df["entrega_atrasada"].notna().astype(int)
    df["_entrega_atrasada"] = _flag(df["entrega_atrasada"])
    agg = {
        "pedidos_entregues": ("_one", "sum"),
        "pedidos_com_avaliacao": ("_aval", "sum"),
        "pedidos_avaliacao_ruim": ("_ruim", "sum"),
        "pedidos_postagem_elegiveis": ("_eleg", "sum"),
        "pedidos_postagem_no_prazo": ("_prazo", "sum"),
        "pedidos_entrega_avaliavel": ("_entrega_valida", "sum"),
        "pedidos_entrega_atrasada": ("_entrega_atrasada", "sum"),
    }
    if by:
        out = df.groupby(by, observed=True, dropna=False).agg(**agg).reset_index()
    else:
        out = pd.DataFrame({k: [df[c].sum()] for k, (c, _) in agg.items()})
    out["pedidos_sem_avaliacao"] = out["pedidos_entregues"] - out["pedidos_com_avaliacao"]
    out["pct_sem_avaliacao"] = pct(out["pedidos_sem_avaliacao"], out["pedidos_entregues"])
    out["kpi1_pct_avaliacao_ruim"] = pct(out["pedidos_avaliacao_ruim"], out["pedidos_com_avaliacao"])
    out["kpi3_pct_postagem_no_prazo"] = pct(out["pedidos_postagem_no_prazo"], out["pedidos_postagem_elegiveis"])
    out["pct_entrega_atrasada"] = pct(out["pedidos_entrega_atrasada"], out["pedidos_entrega_avaliavel"])
    return out


def kpi_frete(itens: pd.DataFrame, by=None) -> pd.DataFrame:
    """KPI2 a partir da tabela de ITENS (1 linha por item): soma frete / soma preço."""
    by = [by] if isinstance(by, str) else (by or [])
    agg = {
        "itens": ("order_item_id", "size"),
        "soma_frete": ("freight_value", "sum"),
        "soma_preco_produtos": ("price", "sum"),
    }
    if by:
        out = itens.groupby(by, observed=True, dropna=False).agg(**agg).reset_index()
    else:
        out = pd.DataFrame({"itens": [len(itens)], "soma_frete": [itens["freight_value"].sum()],
                            "soma_preco_produtos": [itens["price"].sum()]})
    out["kpi2_pct_frete_sobre_produto"] = pct(out["soma_frete"], out["soma_preco_produtos"])
    return out


def flag_amostra(df: pd.DataFrame, den_col: str, minimo: int = MIN_AMOSTRA) -> pd.DataFrame:
    df = df.copy()
    df["amostra_pequena"] = df[den_col] < minimo
    return df
