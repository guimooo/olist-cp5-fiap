"""Gera a ficha técnica do dashboard (PDF separado, A4 horizontal) com autores e RMs.

Conteúdo: (A) tabela atualizada dos três KPIs, (B) uma linha por visual do dashboard dizendo por
que aquele gráfico e o que foi retirado dele, (C) captura do dashboard, contrato DAX e modelo.
Valores dos KPIs lidos de output/dashboard/kpi_resumo_periodo.csv (E1) e conferidos contra os
valores validados no Power BI; textos do registro em conteudo_ficha.py.

Uso (na raiz do projeto): python entregaveis/scripts/05_gerar_ficha_tecnica_pdf.py
Saída: entregaveis/olist_cp5_ficha_tecnica.pdf
"""
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
from conteudo_ficha import FICHA_KPIS, REGISTRO_VISUAIS  # noqa: E402

OUT = ROOT / "entregaveis" / "olist_cp5_ficha_tecnica.pdf"
PREVIEW = ROOT / "entregaveis" / "preview_dashboard.png"
AUTORES = [("Guilherme Moraes de Sousa", "RM563530"), ("Júlia Ferreira França", "RM563445")]

# Paleta do dashboard
AZUL, LARANJA, CRITICO, BOM, ALERTA = map(HexColor, ("#2a78d6", "#eb6834", "#d03b3b", "#006300", "#9a6700"))
TINTA, TINTA2, MUDO, GRADE = map(HexColor, ("#0b0b0b", "#52514e", "#898781", "#e1e0d9"))
NAVY, FUNDO, CARTAO, AZUL_CLARO, BEGE = map(HexColor, ("#12233d", "#f6f5f1", "#ffffff", "#eaf2fc", "#f0efec"))

FONTES = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("Segoe", str(FONTES / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Semi", str(FONTES / "seguisb.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Bold", str(FONTES / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Light", str(FONTES / "segoeuil.ttf")))
pdfmetrics.registerFont(TTFont("Segoe-Symbol", str(FONTES / "seguisym.ttf")))

W, H = landscape(A4)
M = 30  # margem


def estilo(nome, fonte="Segoe", tam=8, cor=TINTA, lead=None, **kw):
    return ParagraphStyle(nome, fontName=fonte, fontSize=tam, textColor=cor, leading=lead or tam * 1.3, alignment=TA_LEFT, **kw)


S_CEL = estilo("cel", tam=7.4, cor=TINTA2, lead=9.6)
S_CEL_FORTE = estilo("celf", "Segoe-Semi", 7.6, TINTA, 9.8)
S_HDR = estilo("hdr", "Segoe-Semi", 7.4, white, 9.4)
S_TXT = estilo("txt", tam=8.6, cor=TINTA2, lead=12)


def br(v, casas=1):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, casas=1):
    return br(v, casas) + "%"


def sinal(v, casas=1):
    return ("+" if v > 0 else "−" if v < 0 else "") + br(abs(v), casas)


# ---------------------------------------------------------------------------
# Valores dos KPIs (E1) conferidos com o Power BI
# ---------------------------------------------------------------------------
r = pd.read_csv(ROOT / "output" / "dashboard" / "kpi_resumo_periodo.csv").set_index("ano_original")
r24, r25 = r.loc[2017], r.loc[2018]
KPIS = {
    "KPI01": dict(v24=r24.kpi1_pct_avaliacao_ruim, v25=r25.kpi1_pct_avaliacao_ruim, ref24=10.6, ref25=13.4,
                  marco="12,0%", meta="10,0% até dez/2027",
                  num=f"{br(r25.pedidos_avaliacao_ruim, 0)} ÷ {br(r25.pedidos_com_avaliacao, 0)} pedidos",
                  status=("✖", "Acima do marco 2026: +1,4 p.p.", CRITICO), casas=1, unidade="pedidos com nota 1–2"),
    "KPI02": dict(v24=r24.kpi2_pct_frete_sobre_produto, v25=r25.kpi2_pct_frete_sobre_produto, ref24=16.0, ref25=17.1,
                  marco="≤ 17,1%", meta="≤ 17,1%",
                  num=f"R$ {br(r25.soma_frete / 1e6, 2)} mi ÷ R$ {br(r25.soma_preco_produtos / 1e6, 2)} mi",
                  status=("✔", "Dentro do limite: folga de 0,01 p.p.", BOM), casas=2, unidade="frete sobre produtos"),
    "KPI03": dict(v24=r24.kpi3_pct_postagem_no_prazo, v25=r25.kpi3_pct_postagem_no_prazo, ref24=91.4, ref25=91.5,
                  marco="95,0%", meta="97,0%",
                  num=f"{br(r25.pedidos_postagem_no_prazo, 0)} ÷ {br(r25.pedidos_postagem_elegiveis, 0)} pedidos",
                  status=("✖", "Abaixo do marco 2026: faltam 3,5 p.p.", CRITICO), casas=1, unidade="pedidos postados no prazo"),
}
# mesmos valores do Power BI (validacao_dax_resultado.txt, consulta V01)
for k, esperado in {"KPI01": (0.105875, 0.13372), "KPI02": (0.160163, 0.170884), "KPI03": (0.913897, 0.914518)}.items():
    assert (round(KPIS[k]["v24"] / 100, 6), round(KPIS[k]["v25"] / 100, 6)) == esperado, k
# status coerentes com os marcos
assert KPIS["KPI01"]["v25"] > 12 and KPIS["KPI02"]["v25"] <= 17.1 and KPIS["KPI03"]["v25"] < 95

c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle("Olist CP5 · Ficha técnica do dashboard")
c.setAuthor("Guilherme Moraes de Sousa (RM563530) e Júlia Ferreira França (RM563445)")
c.setSubject("Ficha técnica do dashboard Power BI olist_cp5.pbix")
TOTAL_PAG = 3


def fundo():
    c.setFillColor(FUNDO)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def rodape(n):
    c.setStrokeColor(GRADE)
    c.setLineWidth(0.6)
    c.line(M, 24, W - M, 24)
    c.setFont("Segoe-Semi", 7)
    c.setFillColor(TINTA2)
    c.drawString(M, 13, "Olist CP5 · Ficha técnica do dashboard  ·  " +
                 "  ·  ".join(f"{n_} ({rm})" for n_, rm in AUTORES))
    c.setFont("Segoe", 7)
    c.setFillColor(MUDO)
    c.drawRightString(W - M, 13, f"{n} / {TOTAL_PAG}")


def cabecalho_secao(y, letra, titulo, sub=None):
    c.setFillColor(AZUL)
    c.roundRect(M, y - 15, 18, 18, 4, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Segoe-Bold", 10)
    c.drawCentredString(M + 9, y - 10.5, letra)
    c.setFillColor(TINTA)
    c.setFont("Segoe-Bold", 13)
    c.drawString(M + 26, y - 11, titulo)
    if sub:
        c.setFont("Segoe", 8)
        c.setFillColor(MUDO)
        c.drawString(M + 26 + pdfmetrics.stringWidth(titulo, "Segoe-Bold", 13) + 10, y - 10.5, sub)


def para(texto, est, x, y_topo, largura):
    p = Paragraph(texto, est)
    _, h = p.wrap(largura, 1000)
    p.drawOn(c, x, y_topo - h)
    return h


def cartao(x, y, w, h, fc=CARTAO, ec=GRADE, raio=6):
    c.setFillColor(fc)
    c.setStrokeColor(ec)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, raio, stroke=1, fill=1)


def tabela(dados, larguras, x, y_topo, zebra=True):
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo_t = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRADE),
        ("BOX", (0, 0), (-1, -1), 0.6, GRADE),
    ]
    if zebra:
        estilo_t += [("BACKGROUND", (0, i), (-1, i), CARTAO if i % 2 else HexColor("#fbfaf8")) for i in range(1, len(dados))]
    t.setStyle(TableStyle(estilo_t))
    _, h = t.wrap(sum(larguras), 1000)
    t.drawOn(c, x, y_topo - h)
    return h


# =============================================================================
# Página 1 — capa + KPIs
# =============================================================================
fundo()
BAND = 132
c.setFillColor(NAVY)
c.rect(0, H - BAND, W, BAND, stroke=0, fill=1)
c.setFillColor(AZUL)
c.rect(0, H - BAND, W, 3, stroke=0, fill=1)
c.setFillColor(HexColor("#8fb4e6"))
c.setFont("Segoe-Semi", 8)
c.drawString(M, H - 34, "FICHA TÉCNICA  ·  CP5 FIAP  ·  CIÊNCIA DE DADOS → POWER BI")
c.setFillColor(white)
c.setFont("Segoe-Bold", 24)
c.drawString(M, H - 64, "Dashboard executivo Olist")
c.setFont("Segoe-Light", 13)
c.drawString(M, H - 84, "Onde concentrar esforço para reduzir a insatisfação: pontualidade dos sellers,")
c.drawString(M, H - 101, "logística regional ou as duas, sem passar de 17,1% de frete")
# bloco de autores
bx, bw = W - M - 236, 236
c.setFillColor(HexColor("#1b3253"))
c.roundRect(bx, H - BAND + 22, bw, 84, 8, stroke=0, fill=1)
c.setFillColor(HexColor("#8fb4e6"))
c.setFont("Segoe-Semi", 7.5)
c.drawString(bx + 14, H - 44, "AUTORES")
for i, (nome, rm) in enumerate(AUTORES):
    yy = H - 63 - i * 20
    c.setFillColor(white)
    c.setFont("Segoe-Semi", 10.5)
    c.drawString(bx + 14, yy, nome)
    c.setFillColor(HexColor("#c9d8ee"))
    c.setFont("Segoe", 9)
    c.drawRightString(bx + bw - 14, yy, rm)
c.setFillColor(HexColor("#8fb4e6"))
c.setFont("Segoe", 7.5)
c.drawString(bx + 14, H - 104, "Outubro de 2026  ·  arquivo: olist_cp5.pbix")

# premissa temporal
y = H - BAND - 14
cartao(M, y - 30, W - 2 * M, 30, fc=AZUL_CLARO, ec=HexColor("#c3d8f3"))
para("<font name='Segoe-Semi' color='#1c5cab'>Premissa temporal.</font> “2024” = pedidos entregues com compra em "
     "jan–ago/<b>2017</b> (21.998 pedidos) e “2025” = jan–ago/<b>2018</b> (52.783 pedidos): proxies acadêmicas, não dados reais "
     "de 2024/2025. Não há dado observado de 2026: os marcos de 2026 são planejamento. Fonte: Olist, Brazilian E-Commerce Public "
     "Dataset (Kaggle), saídas da E1 de 19/10/2026.", estilo("prem", tam=7.8, cor=HexColor("#1f3a5f"), lead=10.4),
     M + 10, y - 5, W - 2 * M - 20)

# A. KPIs
y -= 46
cabecalho_secao(y, "A", "KPIs oficiais: valores recalculados × proposta", "valores fixos por período, iguais aos do dashboard")
y -= 26
CW, GAP, CH = (W - 2 * M - 2 * 12) / 3, 12, 196
for i, ficha in enumerate(FICHA_KPIS):
    k = KPIS[ficha["codigo"]]
    x = M + i * (CW + GAP)
    cartao(x, y - CH, CW, CH)
    # faixa de papel
    c.setFillColor(NAVY)
    c.roundRect(x + 12, y - 24, pdfmetrics.stringWidth(ficha["papel"].upper(), "Segoe-Bold", 7.5) + 16, 15, 7.5, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Segoe-Bold", 7.5)
    c.drawString(x + 20, y - 19.5, ficha["papel"].upper())
    c.setFillColor(MUDO)
    c.setFont("Segoe-Semi", 7.5)
    c.drawRightString(x + CW - 12, y - 19.5, ficha["codigo"])
    para(ficha["kpi"].replace("entregues ", "").replace("(nota 1 ou 2)", "(nota 1–2)"), estilo("kn", "Segoe-Semi", 9.2, TINTA, 11.5), x + 12, y - 32, CW - 24)
    # valor 2025 e trajetória
    c.setFillColor(TINTA)
    c.setFont("Segoe-Bold", 26)
    v = pct(k["v25"], k["casas"])
    c.drawString(x + 12, y - 86, v)
    vx = x + 18 + pdfmetrics.stringWidth(v, "Segoe-Bold", 26)
    c.setFont("Segoe", 7.6)
    c.setFillColor(TINTA2)
    c.drawString(vx, y - 72, f"2025 (proxy 2018)  ·  2024: {pct(k['v24'], k['casas'])}")
    c.setFont("Segoe-Semi", 7.6)
    c.drawString(vx, y - 84, f"{sinal(k['v25'] - k['v24'])} p.p. vs 2024")
    # linhas de detalhe
    linhas = [
        ("Numerador ÷ denominador (2025)", k["num"]),
        ("Referência da proposta (2024 → 2025)", f"{br(k['ref24'])}% → {br(k['ref25'])}%"),
        ("Recalculado − proposta (2025)", f"{sinal(round(k['v25'] - k['ref25'], 2), 2)} p.p.  (arredondamento)"),
        ("Marco 2026", k["marco"]),
        ("Meta / limite 2027", k["meta"]),
    ]
    yy = y - 104
    for rot, val in linhas:
        c.setStrokeColor(GRADE)
        c.setLineWidth(0.4)
        c.line(x + 12, yy + 9, x + CW - 12, yy + 9)
        c.setFont("Segoe", 7.3)
        c.setFillColor(MUDO)
        c.drawString(x + 12, yy, rot)
        c.setFont("Segoe-Semi", 7.6)
        c.setFillColor(TINTA)
        c.drawRightString(x + CW - 12, yy, val)
        yy -= 14
    simbolo, texto_st, cor_st = k["status"]
    c.setFillColor(HexColor("#fbeaea") if cor_st == CRITICO else HexColor("#e8f3e8"))
    c.roundRect(x + 12, y - CH + 10, CW - 24, 20, 5, stroke=0, fill=1)
    c.setFillColor(cor_st)
    c.setFont("Segoe-Symbol", 9)
    c.drawString(x + 20, y - CH + 16.5, simbolo)
    c.setFont("Segoe-Bold", 8.4)
    c.drawString(x + 33, y - CH + 16.5, f"Status 2025: {texto_st}")

# definições e qualidade
y -= CH + 12
cab = [Paragraph(h, S_HDR) for h in ("KPI", "Definição / fórmula operacional", "Qualidade e limitações")]
linhas = [cab] + [[Paragraph(f"<font name='Segoe-Semi' color='#0b0b0b'>{f['codigo']} · {f['papel']}</font>", S_CEL),
                   Paragraph(f["formula"], S_CEL), Paragraph(f["observacao"], S_CEL)] for f in FICHA_KPIS]
tabela(linhas, [92, (W - 2 * M - 92) * 0.52, (W - 2 * M - 92) * 0.48], M, y)
rodape(1)
c.showPage()

# =============================================================================
# Página 2 — registro dos visuais
# =============================================================================
fundo()
y = H - 30
cabecalho_secao(y, "B", "Registro dos visuais do dashboard", "uma linha por visual: por que aquele gráfico e o que foi retirado dele")
y -= 24
para("O dashboard tem <b>uma página</b>: três cartões de KPI (C1–C3) e cinco gráficos de evidência (G1–G5), com filtros de "
     "período (padrão: 2025 proxy) e região. Cabeçalho, filtros e rodapé são navegação. As conclusões abaixo valem para o recorte "
     "padrão, 2025 (proxy jan–ago/2018) e todas as regiões.", S_TXT, M, y, W - 2 * M)
y -= 32
cab = [Paragraph(h, S_HDR) for h in ("ID", "Visual", "Pergunta de negócio", "Por que este gráfico",
                                     "Evidência / conclusão retirada", "Decisão que pode apoiar")]
linhas = [cab]
for vid, vis, perg, porq, evid, dec in REGISTRO_VISUAIS:
    linhas.append([Paragraph(f"<font name='Segoe-Bold' color='#2a78d6'>{vid}</font>", S_CEL_FORTE),
                   Paragraph(vis, S_CEL_FORTE), Paragraph(perg, S_CEL), Paragraph(porq, S_CEL),
                   Paragraph(evid, estilo("ev", tam=7.4, cor=TINTA, lead=9.6)), Paragraph(dec, S_CEL)])
larg = [26, 112, 120, 160, 196, W - 2 * M - (26 + 112 + 120 + 160 + 196)]
h_tab = tabela(linhas, larg, M, y)
assert y - h_tab > 34, "registro não coube na página 2"
rodape(2)
c.showPage()

# =============================================================================
# Página 3 — captura do dashboard, contrato DAX e modelo
# =============================================================================
fundo()
y = H - 30
cabecalho_secao(y, "C", "Dashboard, contrato DAX e modelo", "olist_cp5.pbix · Power BI Desktop 2.159")
y -= 26
img = ImageReader(str(PREVIEW))
iw, ih = img.getSize()
IW = 470
IH = IW * ih / iw
cartao(M, y - IH - 34, IW + 16, IH + 34)
c.drawImage(img, M + 8, y - IH - 8, IW, IH)
c.setFont("Segoe", 7)
c.setFillColor(MUDO)
c.drawString(M + 8, y - IH - 24, "Captura do dashboard aberto no Power BI Desktop (recorte padrão: 2025 proxy, todas as regiões).")

# contrato DAX
xr = M + IW + 30
wr = W - M - xr
c.setFont("Segoe-Bold", 10)
c.setFillColor(TINTA)
c.drawString(xr, y - 8, "Contrato DAX: uma medida por família")
contrato = [
    ("F1 Razão", "DIVIDE", "KPI01, KPI02, KPI03, % Entrega Atrasada"),
    ("F2 Contagem", "CALCULATE + filtro, COUNTROWS, DISTINCTCOUNT, IN", "Pedidos com Avaliação Ruim (IN {1, 2}), Pedidos Avaliados"),
    ("F3 Contexto", "ALL · REMOVEFILTERS · ALLSELECTED", "KPI01 Todas as Regiões · Pedidos Ruins acima da Média · Ranking Seller"),
    ("F4 Iteradoras", "SUMX · AVERAGEX · RANKX", "Valor Pago Produtos mais Frete · Nota Média · Ranking Seller"),
    ("F5 Tempo", "TOTALYTD · SAMEPERIODLASTYEAR · DATEADD", "KPI01 Acumulado no Ano · KPI01/02/03 Período Anterior"),
    ("F6 Lógica", "VAR/RETURN + SWITCH(TRUE())", "KPI01/02/03 Status e Cor Status"),
]
cab = [Paragraph(h, S_HDR) for h in ("Família", "Funções", "Onde aparece")]
dados = [cab] + [[Paragraph(f"<font name='Segoe-Semi' color='#0b0b0b'>{a}</font>", S_CEL), Paragraph(b, S_CEL), Paragraph(cc, S_CEL)]
                 for a, b, cc in contrato]
h1 = tabela(dados, [62, wr * 0.40, wr - 62 - wr * 0.40], xr, y - 16)
yy = y - 16 - h1 - 10
cartao(xr, yy - 46, wr, 46, fc=AZUL_CLARO, ec=HexColor("#c3d8f3"))
para("<font name='Segoe-Semi' color='#1c5cab'>Validação executada.</font> 13 consultas DAX rodadas no modelo do próprio "
     ".pbix (ADOMD.NET), com 0 erros e valores idênticos aos da E1. Higiene: tabela Medidas dedicada, nenhuma coluna calculada, "
     "nenhum “/” cru e formato definido em todas as medidas numéricas.", estilo("val", tam=7.4, cor=HexColor("#1f3a5f"), lead=9.8),
     xr + 8, yy - 6, wr - 16)

# modelo
y2 = y - IH - 52
c.setFont("Segoe-Bold", 10)
c.setFillColor(TINTA)
c.drawString(M, y2, "Modelo de dados e regras herdadas da E1")
modelo = [
    ("Pedidos", "1 linha por pedido entregue", "KPI01, KPI03, entrega atrasada · avaliação mais recente por pedido"),
    ("Itens", "1 linha por item", "KPI02 = Σ frete ÷ Σ preço, sem join que duplique frete"),
    ("Pedido Seller", "1 linha por par pedido × seller", "ranking de sellers (não conta pedidos únicos)"),
    ("Calendário", "dia, 2017–2018 (tabela de datas)", "TOTALYTD, SAMEPERIODLASTYEAR, DATEADD na janela jan–ago"),
    ("Local Cliente · Sellers", "dimensões", "UF → região (27 UFs); UF e região do seller"),
]
cab = [Paragraph(h, S_HDR) for h in ("Tabela", "Granularidade", "Uso")]
dados = [cab] + [[Paragraph(f"<font name='Segoe-Semi' color='#0b0b0b'>{a}</font>", S_CEL), Paragraph(b, S_CEL), Paragraph(cc, S_CEL)]
                 for a, b, cc in modelo]
h2 = tabela(dados, [100, 150, IW + 16 - 250], M, y2 - 8)
c.setFont("Segoe", 7)
c.setFillColor(MUDO)
c.drawString(M, y2 - 8 - h2 - 11, "Relacionamentos muitos-para-um com filtro em direção única, sem relação fato-fato. "
                                  "Postagem comparada ao menor shipping_limit_date do pedido.")
assert y2 - 8 - h2 - 11 > 32, "modelo não coube na página 3"
rodape(3)
c.showPage()
c.save()
print(OUT)
