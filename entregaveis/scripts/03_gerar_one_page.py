"""Gera o one-page executivo (PDF, A4 horizontal, 1 página) a partir das saídas da E1.

Todos os números vêm de output/dashboard/*.csv (notebooks 03-06), os mesmos validados
no modelo Power BI (validacao_dax_resultado.txt). Nada é digitado à mão: o script
calcula, formata e confere os valores antes de desenhar.

Uso (na raiz do projeto): python entregaveis/scripts/03_gerar_one_page.py
Saídas: entregaveis/olist_cp5_one_page.pdf e entregaveis/olist_cp5_one_page.png (prévia)
"""
import textwrap
from pathlib import Path

import fitz  # PyMuPDF, só para a prévia PNG e a contagem de páginas
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
E1 = ROOT / "output" / "dashboard"
OUT = ROOT / "entregaveis"
PDF, PNG = OUT / "olist_cp5_one_page.pdf", OUT / "olist_cp5_one_page.png"

# Paleta e tipografia iguais às do dashboard Power BI
AZUL, LARANJA, CRITICO, BOM, ALERTA = "#2a78d6", "#eb6834", "#d03b3b", "#006300", "#9a6700"
TINTA, TINTA2, MUDO, GRADE, NEUTRO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#a8a69d"
FUNDO, CARTAO = "#f9f9f7", "#ffffff"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 8, "axes.edgecolor": GRADE, "axes.linewidth": 0.6,
                     "xtick.color": MUDO, "ytick.color": MUDO, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "pdf.fonttype": 42})


def br(v, casas=1):
    """Número no padrão brasileiro."""
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, casas=1):
    return br(v, casas) + "%"


# ---------------------------------------------------------------------------
# Dados da E1
# ---------------------------------------------------------------------------
resumo = pd.read_csv(E1 / "kpi_resumo_periodo.csv").set_index("ano_original")
mensal = pd.read_csv(E1 / "kpi_mensal.csv")
regiao = pd.read_csv(E1 / "kpi_regiao.csv")
relacao = pd.read_csv(E1 / "relacao_atraso_avaliacao.csv")
uf = pd.read_csv(E1 / "kpi_uf.csv")
seller = pd.read_csv(E1 / "kpi_seller.csv")
origem = pd.read_csv(E1 / "origem_atraso_regiao.csv")

r24, r25 = resumo.loc[2017], resumo.loc[2018]
k1_24, k1_25 = r24.kpi1_pct_avaliacao_ruim, r25.kpi1_pct_avaliacao_ruim
k2_24, k2_25 = r24.kpi2_pct_frete_sobre_produto, r25.kpi2_pct_frete_sobre_produto
k3_24, k3_25 = r24.kpi3_pct_postagem_no_prazo, r25.kpi3_pct_postagem_no_prazo
MARCO_K1, META_K1, LIMITE_K2, MARCO_K3, META_K3 = 12.0, 10.0, 17.1, 95.0, 97.0

m25 = mensal[mensal.ano_original == 2018].sort_values("mes")
pico = m25[m25.mes.isin([2, 3])]
resto = m25[m25.mes >= 4]
ruins_pico, ruins_total = int(pico.pedidos_avaliacao_ruim.sum()), int(m25.pedidos_avaliacao_ruim.sum())
k1_abr_ago = resto.pedidos_avaliacao_ruim.sum() / resto.pedidos_com_avaliacao.sum() * 100
entrega_max = m25.pct_entrega_atrasada.max()

reg25 = regiao[regiao.ano_original == 2018].set_index("regiao_cliente")
share_sudeste = reg25.loc["Sudeste", "pedidos_entregues"] / reg25.pedidos_entregues.sum() * 100

rel = relacao[relacao.periodo_comparativo.str.startswith("2025")].set_index(["situacao_postagem", "situacao_entrega"])
def rr(p, e, c="pct_avaliacao_ruim"):
    return rel.loc[(p, e), c]
ea, enp = rr("todos", "entrega atrasada"), rr("todos", "entrega no prazo")
n_ea, n_enp = int(rr("todos", "entrega atrasada", "pedidos_com_avaliacao")), int(rr("todos", "entrega no prazo", "pedidos_com_avaliacao"))
pa, pnp = rr("postagem atrasada", "todos"), rr("postagem no prazo", "todos")
pa_enp = rr("postagem atrasada", "entrega no prazo")
pnp_enp = rr("postagem no prazo", "entrega no prazo")
ea_com_postagem_ok = rr("postagem no prazo", "entrega atrasada", "pedidos_com_avaliacao") / n_ea * 100
# Contrafactual descritivo (E1, seção 1): atrasados com a taxa dos pedidos no prazo
k1_sem_atraso_entrega = (rr("todos", "entrega atrasada", "pedidos_com_avaliacao") * enp / 100 + rr("todos", "entrega no prazo", "pedidos_avaliacao_ruim")) / r25.pedidos_com_avaliacao * 100
k1_sem_atraso_postagem = (rr("postagem atrasada", "todos", "pedidos_com_avaliacao") * pnp / 100 + rr("postagem no prazo", "todos", "pedidos_avaliacao_ruim")) / r25.pedidos_com_avaliacao * 100

org25 = origem[origem.periodo_comparativo.str.startswith("2025")].set_index("regiao_cliente")
ea_ok_ne = org25.loc["Nordeste", "pct_entrega_atrasada_dado_postagem_no_prazo"]
ea_ok_n = org25.loc["Norte", "pct_entrega_atrasada_dado_postagem_no_prazo"]
ea_ok_se = org25.loc["Sudeste", "pct_entrega_atrasada_dado_postagem_no_prazo"]

uf25 = uf[uf.ano_original == 2018].copy()
uf25["excedente"] = (uf25.kpi1_pct_avaliacao_ruim - k1_25) / 100 * uf25.pedidos_com_avaliacao
rj = uf25.set_index("customer_state").loc["RJ"]

s25 = seller[(seller.ano_original == 2018)]
total_atrasadas = s25.pedido_seller_postagem_atrasada.sum()
top10 = (s25[s25.pedido_seller_elegiveis_postagem >= 30]
         .assign(p=lambda d: d.pct_postagem_atrasada)
         .sort_values(["pedido_seller_postagem_atrasada", "p"], ascending=False).head(10))
share_top10 = top10.pedido_seller_postagem_atrasada.sum() / total_atrasadas * 100

# Conferência contra os valores validados no Power BI (validacao_dax_resultado.txt)
checks = {
    "KPI01 2025": (round(k1_25, 2), 13.37), "KPI02 2025": (round(k2_25, 2), 17.09), "KPI03 2025": (round(k3_25, 2), 91.45),
    "ruins fev-mar": (ruins_pico, 2733), "ruins 2025": (ruins_total, 7016), "abr-ago": (round(k1_abr_ago, 1), 10.4),
    "excedente RJ": (round(rj.excedente), 427), "top10 atrasadas": (int(top10.pedido_seller_postagem_atrasada.sum()), 896),
    "atrasadas 2025": (int(total_atrasadas), 4522), "contrafactual entrega": (round(k1_sem_atraso_entrega, 2), 9.29),
    "contrafactual postagem": (round(k1_sem_atraso_postagem, 2), 12.33), "entrega atrasada c/ postagem ok": (round(ea_com_postagem_ok, 1), 75.2),
}
for nome, (obtido, esperado) in checks.items():
    assert obtido == esperado, f"{nome}: {obtido} != {esperado}"

# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
W, H = 11.69, 8.27  # A4 horizontal (pol.)
fig = plt.figure(figsize=(W, H))
fig.patch.set_facecolor(FUNDO)
ML = 0.42 / W  # margem lateral em fração da largura


def txt(x, y, s, size=8, color=TINTA, weight="normal", width=None, ls=1.25, **kw):
    if width:
        s = "\n".join(textwrap.fill(par, width) for par in s.split("\n"))
    return fig.text(x, y, s, fontsize=size, color=color, weight=weight, va="top", linespacing=ls, **kw)


def caixa(x, y, w, h, fc=CARTAO, ec=GRADE, lw=0.6):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc=fc, ec=ec, lw=lw, zorder=-1))


# Cabeçalho: título-conclusão
txt(ML, 0.965, "OLIST · OPERAÇÕES DO MARKETPLACE · CP5 FIAP · ONE-PAGE EXECUTIVO", 7, MUDO, "bold")
txt(1 - ML, 0.965, "Guilherme Moraes de Sousa (RM563530)  ·  Júlia Ferreira França (RM563445)", 7, TINTA2, "bold", ha="right")
txt(ML, 0.945, "A insatisfação segue a entrega atrasada, não a postagem do seller: concentrar o esforço na logística\n"
               "regional (RJ, Nordeste e Norte) é o caminho para 10% em 2027 sem passar de 17,1% de frete", 16.5, TINTA, "bold", ls=1.15)
txt(ML, 0.862, f"Pedidos entregues com compra em jan–ago. 2024 = proxy jan–ago/2017 ({br(r24.pedidos_entregues, 0)} pedidos) e "
               f"2025 = proxy jan–ago/2018 ({br(r25.pedidos_entregues, 0)} pedidos); não são dados reais de 2024/2025 e não há "
               "dado observado de 2026.", 8, TINTA2)

# Três evidências
COLW, GAP = (1 - 2 * ML - 2 * 0.014) / 3, 0.014
TOP, BOT = 0.835, 0.335
evid = [
    ("ALVO", "KPI01 · % de pedidos com avaliação ruim (nota 1–2)",
     f"{pct(k1_25)}", f"2024: {pct(k1_24)}  ·  marco 2026: {pct(MARCO_K1)}  ·  meta 2027: {pct(META_K1)}",
     f"A alta para {pct(k1_25)} veio de fev–mar/2018, quando a entrega atrasada chegou a {pct(entrega_max, 0)}; "
     f"de abr a ago a taxa foi {pct(k1_abr_ago)}",
     f"Fev–mar concentram {br(ruins_pico, 0)} dos {br(ruins_total, 0)} pedidos ruins de 2025 ({pct(ruins_pico / ruins_total * 100, 0)}). "
     f"RJ é a UF com mais pedidos ruins acima da média (~{br(rj.excedente, 0)}; {pct(rj.kpi1_pct_avaliacao_ruim)} de "
     f"{br(rj.pedidos_com_avaliacao, 0)} avaliados)."),
    ("RESTRIÇÃO", "KPI02 · Frete ÷ valor dos produtos",
     f"{pct(k2_25, 2)}", f"2024: {pct(k2_24, 2)}  ·  limite 2026 e 2027: ≤ {pct(LIMITE_K2)} (agregado)",
     f"O frete já está no teto ({pct(k2_25, 2)}). Só o Sudeste fica abaixo de {pct(LIMITE_K2)}, e Norte e Nordeste pagam 23–24%",
     f"O limite vale para o KPI geral; o corte regional é diagnóstico. O Sudeste ({pct(share_sudeste, 0)} dos pedidos) sustenta "
     "o agregado. Na E1, itens entregues no prazo pagaram 17,08% de frete contra 17,23% dos atrasados: pagar mais frete não "
     "garante prazo."),
    ("ALAVANCA", "KPI03 · % de pedidos postados no prazo pelo seller",
     f"{pct(k3_25)}", f"2024: {pct(k3_24)}  ·  marco 2026: {pct(MARCO_K3)}  ·  meta 2027: {pct(META_K3)}",
     f"Postar no prazo não evita a insatisfação: {pct(ea_com_postagem_ok, 0)} das entregas atrasadas saíram do seller no prazo, "
     f"e ~{pct(round(ea), 0)} delas viraram avaliação ruim",
     f"Com a entrega no prazo, a postagem atrasada eleva a taxa só de {pct(pnp_enp)} para {pct(pa_enp)}. A alavanca é focada: "
     f"10 sellers somam {pct(share_top10)} das postagens atrasadas. Associação, não causalidade."),
]
for i, (papel, nome, valor, ref, titulo, nota) in enumerate(evid):
    x = ML + i * (COLW + GAP)
    caixa(x, BOT, COLW, TOP - BOT)
    px = x + 0.012
    cw = int(COLW * W * 72 / 4.6)  # caracteres por linha para ~8 pt
    txt(px, TOP - 0.014, f"{papel}  ·  {nome}", 7, TINTA2, "bold")
    txt(px, TOP - 0.038, valor, 19, TINTA, "bold")
    txt(px + 0.093 if len(valor) > 5 else px + 0.08, TOP - 0.046, ref, 6.8, TINTA2, width=int(cw * 0.75))
    txt(px, TOP - 0.093, titulo, 9.6, TINTA, "bold", width=int(cw * 0.86), ls=1.18)
    txt(px, BOT + 0.080, nota, 7, TINTA2, width=int(cw * 1.12), ls=1.22)

# Gráficos (um por evidência)
ax_h, ax_y = 0.19, BOT + 0.122
# E1 — mensal 2025: avaliação ruim × entrega atrasada
ax = fig.add_axes([ML + 0.032, ax_y, COLW - 0.045, ax_h])
meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago"]
xs = range(len(m25))
ax.plot(xs, m25.kpi1_pct_avaliacao_ruim, color=AZUL, lw=2, marker="o", ms=3.5, label="Avaliação ruim (%)", zorder=3)
ax.plot(xs, m25.pct_entrega_atrasada, color=LARANJA, lw=2, marker="o", ms=3.5, label="Entrega atrasada (%)", zorder=3)
ax.axhline(MARCO_K1, color=MUDO, lw=0.8, ls=(0, (3, 2)), zorder=1)
ax.axhline(META_K1, color=TINTA, lw=0.8, ls=(0, (3, 2)), zorder=1)
ax.text(5.0, MARCO_K1 + 0.5, "marco 2026 · 12%", fontsize=6, color=MUDO, va="bottom", ha="center")
ax.text(5.0, META_K1 - 0.6, "meta 2027 · 10%", fontsize=6, color=TINTA, va="top", ha="center")
for xi, v in zip(xs, m25.kpi1_pct_avaliacao_ruim):
    if xi in (1, 2, 7):
        ax.annotate(pct(v), (xi, v), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=6.5, color=TINTA)
ax.set_xticks(list(xs), meses)
ax.set_ylim(0, 25)
ax.set_xlim(-0.3, 7.3)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
ax.legend(loc="upper right", fontsize=6.3, frameon=False, handlelength=1.4, borderaxespad=0.1)
ax.set_title("Proxy 2025 (jan–ago/2018), por mês da compra", fontsize=6.8, color=MUDO, loc="left", pad=3)

# E2 — frete por região com o limite
ax = fig.add_axes([ML + COLW + GAP + 0.082, ax_y, COLW - 0.098, ax_h])
ordem = reg25.sort_values("kpi2_pct_frete_sobre_produto")
cores = [CRITICO if v > LIMITE_K2 else NEUTRO for v in ordem.kpi2_pct_frete_sobre_produto]
ys = range(len(ordem))
ax.barh(ys, ordem.kpi2_pct_frete_sobre_produto, color=cores, height=0.62, zorder=2)
ax.axvline(LIMITE_K2, color=TINTA, lw=1, ls=(0, (3, 2)), zorder=3)
ax.text(LIMITE_K2 + 0.4, len(ordem) - 0.35, f"limite do KPI geral: {pct(LIMITE_K2)}", fontsize=6.3, color=TINTA, ha="left", va="center")
for yi, (reg, row) in zip(ys, ordem.iterrows()):
    v = row.kpi2_pct_frete_sobre_produto
    if v > LIMITE_K2:
        ax.text(v + 0.4, yi, pct(v), va="center", fontsize=6.5, color=TINTA)
    else:  # rótulo dentro da barra para não cruzar a linha do limite
        ax.text(v - 0.4, yi, pct(v), va="center", ha="right", fontsize=6.5, color=TINTA)
ax.set_yticks(list(ys), [f"{r}  ({br(n, 0)})" for r, n in zip(ordem.index, ordem.pedidos_entregues)], fontsize=6.8, color=TINTA2)
ax.set_xlim(0, 28)
ax.set_ylim(-0.55, len(ordem) - 0.05)
ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
ax.set_title("Frete ÷ produtos por região do cliente, 2025 (pedidos)", fontsize=6.8, color=MUDO, loc="left", pad=3)

# E3 — avaliação ruim por postagem × entrega
ax = fig.add_axes([ML + 2 * (COLW + GAP) + 0.032, ax_y, COLW - 0.045, ax_h])
grupos = ["entrega no prazo", "entrega atrasada"]
w = 0.36
for j, (post, cor, rot) in enumerate([("postagem no prazo", AZUL, "Postagem no prazo"), ("postagem atrasada", LARANJA, "Postagem atrasada")]):
    vals = [rr(post, g) for g in grupos]
    ns = [int(rr(post, g, "pedidos_com_avaliacao")) for g in grupos]
    xsb = [k + (j - 0.5) * (w + 0.03) for k in range(2)]
    ax.bar(xsb, vals, width=w, color=cor, label=rot, zorder=2)
    for xb, v, n in zip(xsb, vals, ns):
        ax.text(xb, v + 1.2, f"{pct(v)}\nn={br(n, 0)}", ha="center", va="bottom", fontsize=6, color=TINTA, linespacing=1.1)
ax.set_xticks([0, 1], ["Entrega no prazo", "Entrega atrasada"], fontsize=7, color=TINTA2)
ax.set_ylim(0, 85)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
ax.legend(loc="upper left", fontsize=6.3, frameon=False, handlelength=1.2, borderaxespad=0.1)
ax.set_title("% avaliação ruim, 2025 (n = pedidos avaliados)", fontsize=6.8, color=MUDO, loc="left", pad=3)

for a in fig.axes:
    a.set_facecolor(CARTAO)
    a.spines[["top", "right"]].set_visible(False)
    a.grid(axis="x" if a.get_yticks().size and a.get_title().startswith("Frete") else "y", color=GRADE, lw=0.5, zorder=0)
    a.set_axisbelow(True)

# Pedido executivo
PY, PH = 0.205, 0.115
caixa(ML, PY, 1 - 2 * ML, PH, fc="#eef4fc", ec=AZUL, lw=0.9)
txt(ML + 0.012, PY + PH - 0.014, "PEDIDO EXECUTIVO", 7, AZUL, "bold")
txt(ML + 0.012, PY + PH - 0.034,
    "Aprovar o programa de SLA logístico por rota para RJ, Nordeste e Norte (prazo de entrega da transportadora + revisão do prazo "
    "prometido), com teto de frete agregado de 17,1%", 10, TINTA, "bold", width=150, ls=1.18)
txt(ML + 0.012, PY + 0.040,
    "Responsável: Gerência de Logística do Marketplace (patrocínio: Diretoria de Operações), com Gestão de Sellers conduzindo o "
    "programa de pontualidade dos 10 sellers reincidentes.\n"
    "Prazo: aprovação na reunião de Operações de nov/2026; SLAs vigentes "
    "até 31/01/2027; plano de capacidade para o pico de fev–mar/2027 antes de 31/01/2027; revisão trimestral de KPI01 e KPI02 até dez/2027.",
    7.6, TINTA2, width=205, ls=1.25)

# Parágrafo final obrigatório
txt(ML, 0.188,
    f"2026 → 2027: não há medição real de 2026 na base, então não é possível confirmar progresso, e a "
    f"leitura é condicional. O marco de {pct(MARCO_K1, 0)} e a meta de {pct(META_K1, 0)} são alcançáveis se o plano atacar a "
    f"entrega: fora do pico de fev–mar a taxa já foi {pct(k1_abr_ago)}, e se os pedidos com entrega atrasada tivessem a taxa dos "
    f"entregues no prazo o KPI01 de 2025 seria {pct(k1_sem_atraso_entrega)}. O plano original, centrado em levar a postagem a "
    f"{pct(MARCO_K3, 0)}/{pct(META_K3, 0)}, não basta sozinho: se as postagens atrasadas tivessem a taxa das postadas no prazo, o KPI01 cairia só a {pct(k1_sem_atraso_postagem)} "
    f"(exercício descritivo). E não há folga para comprar prazo com frete ({pct(k2_25, 2)} vs teto de {pct(LIMITE_K2)}). "
    f"O que mudou: os KPIs recalculados batem com a proposta (diferenças ≤ 0,05 p.p., só arredondamento), mas a prioridade passou "
    f"de cobrar sellers para a logística regional com sellers como alavanca focada, e surgiram dois recortes novos: o pico sazonal "
    f"de fev–mar e o RJ como maior excedente. Hipótese: parcialmente confirmada. O atraso na entrega está fortemente associado à "
    f"avaliação ruim ({pct(ea)} vs {pct(enp)}; {br(n_ea, 0)} vs {br(n_enp, 0)} pedidos), e a lentidão logística regional tem apoio "
    f"(com a postagem no prazo, a entrega atrasa em {pct(ea_ok_ne)} dos pedidos do Nordeste e {pct(ea_ok_n)} do Norte, contra "
    f"{pct(ea_ok_se)} no Sudeste). A postagem tardia do seller tem apoio fraco "
    f"({pct(pa)} vs {pct(pnp)}, mas {pct(pa_enp)} quando a entrega chega no prazo). Associação não prova causalidade.",
    7.9, TINTA, width=214, ls=1.3)

# Rodapé
txt(ML, 0.045, "Fonte: Olist, Brazilian E-Commerce Public Dataset (Kaggle); outputs da E1 (output/dashboard, 19/10/2026), os mesmos "
               "valores do dashboard olist_cp5.pbix. Pedidos entregues; avaliação = a mais recente por pedido; frete somado no nível "
               "item; postagem comparada ao menor shipping_limit_date do pedido. Rankings de seller com mínimo de 30 pares pedido–seller.",
    6.2, MUDO, width=260)

fig.savefig(PDF, facecolor=FUNDO)
plt.close(fig)

doc = fitz.open(PDF)
assert doc.page_count == 1, f"PDF com {doc.page_count} páginas"
doc[0].get_pixmap(dpi=150).save(PNG)
print(f"{PDF} ({doc.page_count} página, {doc[0].rect.width:.0f}x{doc[0].rect.height:.0f} pt)")
