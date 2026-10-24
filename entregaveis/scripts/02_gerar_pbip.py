"""Gera o projeto Power BI (PBIP = modelo TMDL + relatório PBIR) do CP5 Olist.

O projeto lê os CSVs de entregaveis/powerbi/dados (gerados por 01_preparar_dados_powerbi.py).
Depois de aberto e atualizado no Power BI Desktop, é salvo como olist_cp5.pbix.

Uso (na raiz do projeto): python entregaveis/scripts/02_gerar_pbip.py
"""
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PBI = ROOT / "entregaveis" / "powerbi"
DADOS = PBI / "dados"
NOME = "olist_cp5"
SM = PBI / f"{NOME}.SemanticModel"
RP = PBI / f"{NOME}.Report"

PBI_BIN = Path(r"C:\Program Files\WindowsApps")  # tema base copiado da instalação do Desktop
BASE_THEME = "CY24SU10"

# Paleta (mesma do one-page): série 1 azul, série 2 laranja, status crítico, tinta e grade neutras
AZUL, LARANJA, CRITICO, BOM, ALERTA = "#2a78d6", "#eb6834", "#d03b3b", "#006300", "#9a6700"
TINTA, TINTA2, MUDO, GRADE, NEUTRO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#a8a69d"
FUNDO_PAGINA, FUNDO_CARTAO = "#f3f3f0", "#ffffff"

AUTORES = "CP5 FIAP  ·  Guilherme Moraes de Sousa (RM563530)  ·  Júlia Ferreira França (RM563445)"

PERIODO_2024 = "2024 (proxy jan–ago/2017)"
PERIODO_2025 = "2025 (proxy jan–ago/2018)"


def tag(*parts) -> str:
    """lineageTag determinístico (regerar o projeto não muda as tags)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "olist-cp5/" + "/".join(parts)))


def q(name: str) -> str:
    """Nome TMDL entre aspas simples quando tiver espaço, acento ou símbolo."""
    if name.replace("_", "").isascii() and name.replace("_", "").isalnum():
        return name
    return "'" + name.replace("'", "''") + "'"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# =============================================================================
# 1. Modelo semântico (TMDL)
# =============================================================================
# Cada coluna: (coluna_csv, nome_no_modelo, tipo_m, dataType_tmdl, opções)
M_CONV = {
    "text": ('each if _ = "" then null else _', "type text"),
    "date": ('each Date.FromText(_, [Format = "yyyy-MM-dd", Culture = "en-US"])', "type date"),
    "int": ('each if _ = "" then null else Int64.From(_)', "Int64.Type"),
    "num": ('each if _ = "" then null else Number.FromText(_, "en-US")', "type number"),
    "bool": ('each if _ = "" then null else _ = "true"', "type logical"),
}
TMDL_TYPE = {"text": "string", "date": "dateTime", "int": "int64", "num": "double", "bool": "boolean"}

TABELAS_CSV = {
    "Pedidos": ("pedidos.csv", "Fato: 1 linha por pedido entregue (jan–ago 2017/2018). Base do KPI01 e do KPI03.", [
        ("id_pedido", "ID Pedido", "text", {"hidden": True}),
        ("data_compra", "Data Compra", "date", {"hidden": True, "format": "dd/mm/yyyy"}),
        ("uf_cliente", "UF Cliente", "text", {"hidden": True}),
        ("nota_avaliacao", "Nota Avaliação", "int", {"format": "0", "desc": "Nota da avaliação mais recente do pedido (1–5); vazio = sem avaliação."}),
        ("postagem_elegivel", "Postagem Elegível", "bool", {}),
        ("postagem_no_prazo", "Postagem no Prazo", "bool", {}),
        ("entrega_atrasada", "Entrega Atrasada", "bool", {}),
        ("situacao_postagem", "Situação Postagem", "text", {}),
        ("situacao_entrega", "Situação Entrega", "text", {}),
        ("dias_postagem_entrega", "Dias Postagem até Entrega", "num", {"format": "0.0", "hidden": True}),
        ("qtd_sellers", "Qtd Sellers no Pedido", "int", {"format": "0", "hidden": True}),
    ]),
    "Itens": ("itens.csv", "Fato: 1 linha por item de pedido entregue. Base do KPI02 (soma frete ÷ soma preço).", [
        ("id_pedido", "ID Pedido", "text", {"hidden": True}),
        ("id_item", "Item", "int", {"hidden": True, "format": "0"}),
        ("data_compra", "Data Compra", "date", {"hidden": True, "format": "dd/mm/yyyy"}),
        ("uf_cliente", "UF Cliente", "text", {"hidden": True}),
        ("id_seller", "ID Seller", "text", {"hidden": True}),
        ("categoria", "Categoria", "text", {}),
        ("preco", "Preço", "num", {"format": "R$ #,0.00", "hidden": True}),
        ("frete", "Frete", "num", {"format": "R$ #,0.00", "hidden": True}),
    ]),
    "Pedido Seller": ("pedido_seller.csv", "Fato: 1 linha por par pedido × seller. Não é pedido único: usar só para ranking de sellers.", [
        ("id_pedido", "ID Pedido", "text", {"hidden": True}),
        ("id_seller", "ID Seller", "text", {"hidden": True}),
        ("data_compra", "Data Compra", "date", {"hidden": True, "format": "dd/mm/yyyy"}),
        ("uf_cliente", "UF Cliente", "text", {"hidden": True}),
        ("postagem_elegivel", "Postagem Elegível", "bool", {}),
        ("postagem_atrasada", "Postagem Atrasada", "bool", {}),
        ("avaliacao_ruim", "Avaliação Ruim", "bool", {}),
    ]),
    "Sellers": ("sellers.csv", "Dimensão de sellers presentes no recorte.", [
        ("id_seller", "ID Seller", "text", {"hidden": True}),
        ("seller", "Seller", "text", {"desc": "Rótulo curto: 'Seller' + 8 primeiros caracteres do seller_id."}),
        ("uf_seller", "UF Seller", "text", {}),
        ("regiao_seller", "Região Seller", "text", {}),
    ]),
    "Local Cliente": ("uf.csv", "Dimensão UF/região do cliente (27 UFs, mapa explícito da E1).", [
        ("uf", "UF", "text", {}),
        ("regiao", "Região", "text", {"sortBy": "Ordem Região"}),
        ("ordem_regiao", "Ordem Região", "int", {"hidden": True, "format": "0"}),
    ]),
}


def m_csv(arquivo: str, cols) -> str:
    conv = ",\n".join(f'        {{"{c}", {M_CONV[t][0]}, {M_CONV[t][1]}}}' for c, _, t, _ in cols)
    ren = ", ".join(f'{{"{c}", "{n}"}}' for c, n, _, _ in cols)
    return (
        "let\n"
        f'    Fonte = Csv.Document(File.Contents(PastaDados & "{arquivo}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),\n'
        "    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),\n"
        "    Tipos = Table.TransformColumns(Cabecalhos, {\n"
        f"{conv}\n"
        "    }),\n"
        f"    Nomes = Table.RenameColumns(Tipos, {{{ren}}})\n"
        "in\n"
        "    Nomes"
    )


M_CALENDARIO = f"""let
    Inicio = #date(2017, 1, 1),
    Fim = #date(2018, 12, 31),
    Datas = List.Dates(Inicio, Duration.Days(Fim - Inicio) + 1, #duration(1, 0, 0, 0)),
    Tabela = Table.FromList(Datas, Splitter.SplitByNothing(), type table [Data = date]),
    Ano = Table.AddColumn(Tabela, "Ano Original", each Date.Year([Data]), Int64.Type),
    Periodo = Table.AddColumn(Ano, "Período", each if [Ano Original] = 2017 then "{PERIODO_2024}" else "{PERIODO_2025}", type text),
    MesNumero = Table.AddColumn(Periodo, "Mês Número", each Date.Month([Data]), Int64.Type),
    Mes = Table.AddColumn(MesNumero, "Mês", each {{"jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"}}{{[Mês Número] - 1}}, type text),
    AnoMes = Table.AddColumn(Mes, "Ano-Mês Original", each Date.ToText([Data], [Format = "yyyy-MM", Culture = "en-US"]), type text),
    Janela = Table.AddColumn(AnoMes, "Janela Jan-Ago", each [Mês Número] <= 8, type logical)
in
    Janela"""

M_MEDIDAS = "let\n    Fonte = #table(type table [Auxiliar = text], {})\nin\n    Fonte"

CALENDARIO_COLS = [
    ("Data", "date", {"format": "dd/mm/yyyy", "key": True}),
    ("Ano Original", "int", {"format": "0", "desc": "Ano real no dataset (2017 = proxy 2024; 2018 = proxy 2025)."}),
    ("Período", "text", {"sortBy": "Ano Original", "desc": "Rótulo da proxy acadêmica; não são dados reais de 2024/2025."}),
    ("Mês Número", "int", {"format": "0", "hidden": True}),
    ("Mês", "text", {"sortBy": "Mês Número"}),
    ("Ano-Mês Original", "text", {}),
    ("Janela Jan-Ago", "bool", {}),
]


def tmdl_col(table: str, name: str, kind: str, opt: dict) -> str:
    lines = []
    if opt.get("desc"):
        lines.append(f"\t/// {opt['desc']}")
    lines.append(f"\tcolumn {q(name)}")
    lines.append(f"\t\tdataType: {TMDL_TYPE[kind]}")
    if opt.get("key"):
        lines.append("\t\tisKey")
    if opt.get("format"):
        lines.append(f"\t\tformatString: {opt['format']}")
    if opt.get("hidden"):
        lines.append("\t\tisHidden")
    lines.append(f"\t\tlineageTag: {tag(table, name)}")
    lines.append("\t\tsummarizeBy: none")
    lines.append(f"\t\tsourceColumn: {name}")
    if opt.get("sortBy"):
        lines.append(f"\t\tsortByColumn: {q(opt['sortBy'])}")
    return "\n".join(lines) + "\n"


def tmdl_partition(table: str, m: str) -> str:
    body = "\n".join("\t\t\t\t" + ln if ln else "" for ln in m.splitlines())
    return f"\tpartition {q(table)} = m\n\t\tmode: import\n\t\tsource =\n{body}\n"


def tmdl_table(name: str, desc: str, cols_tmdl: str, m: str, extra: str = "") -> str:
    return (f"/// {desc}\ntable {q(name)}\n{extra}\tlineageTag: {tag(name)}\n\n"
            f"{cols_tmdl}\n{tmdl_partition(name, m)}\n\tannotation PBI_ResultType = Table\n")


# ---------------------------------------------------------------------------
# Medidas: (pasta, nome, formato, família, descrição, DAX)
# ---------------------------------------------------------------------------
P = "Medidas"
MEDIDAS = [
    # 0. Metas e limites — centralizados aqui e reutilizados por status e cartões
    ("0. Metas e limites", "Referência Proposta 2024 KPI01", "0.0%", "-", "Proxy 2024 informada na proposta E1.", "0.106"),
    ("0. Metas e limites", "Referência Proposta 2025 KPI01", "0.0%", "-", "Proxy 2025 informada na proposta E1.", "0.134"),
    ("0. Metas e limites", "Marco 2026 KPI01", "0.0%", "-", "Passo intermediário de 2026 (planejamento, não observado).", "0.12"),
    ("0. Metas e limites", "Meta 2027 KPI01", "0.0%", "-", "Alvo até dez/2027.", "0.10"),
    ("0. Metas e limites", "Referência Proposta 2024 KPI02", "0.0%", "-", "Proxy 2024 informada na proposta E1.", "0.160"),
    ("0. Metas e limites", "Referência Proposta 2025 KPI02", "0.0%", "-", "Proxy 2025 informada na proposta E1.", "0.171"),
    ("0. Metas e limites", "Limite Frete KPI02", "0.0%", "-", "Teto do frete sobre produtos em 2026 e 2027 (KPI geral).", "0.171"),
    ("0. Metas e limites", "Referência Proposta 2024 KPI03", "0.0%", "-", "Proxy 2024 informada na proposta E1.", "0.914"),
    ("0. Metas e limites", "Referência Proposta 2025 KPI03", "0.0%", "-", "Proxy 2025 informada na proposta E1.", "0.915"),
    ("0. Metas e limites", "Marco 2026 KPI03", "0.0%", "-", "Passo intermediário de 2026 (planejamento, não observado).", "0.95"),
    ("0. Metas e limites", "Meta 2027 KPI03", "0.0%", "-", "Alvo de 2027.", "0.97"),

    # 2. Contagens (F2)
    ("2. Contagens", "Pedidos Entregues", "#,0", "F2", "Pedidos únicos entregues no recorte.",
     "DISTINCTCOUNT ( Pedidos[ID Pedido] )"),
    ("2. Contagens", "Pedidos Avaliados", "#,0", "F2", "Denominador do KPI01: pedidos com avaliação válida (nota 1–5).",
     "CALCULATE (\n    COUNTROWS ( Pedidos ),\n    KEEPFILTERS ( Pedidos[Nota Avaliação] IN { 1, 2, 3, 4, 5 } )\n)"),
    ("2. Contagens", "Pedidos com Avaliação Ruim", "#,0", "F2", "Numerador do KPI01: pedidos únicos com nota 1 ou 2.",
     "CALCULATE (\n    DISTINCTCOUNT ( Pedidos[ID Pedido] ),\n    KEEPFILTERS ( Pedidos[Nota Avaliação] IN { 1, 2 } )\n)"),
    ("2. Contagens", "Pedidos Elegíveis para Postagem", "#,0", "F2", "Denominador do KPI03: pedidos com data de postagem e prazo limite.",
     "CALCULATE (\n    COUNTROWS ( Pedidos ),\n    KEEPFILTERS ( Pedidos[Postagem Elegível] = TRUE () )\n)"),
    ("2. Contagens", "Pedidos Postados no Prazo", "#,0", "F2", "Numerador do KPI03: postagem até o menor shipping_limit_date do pedido.",
     "CALCULATE (\n    COUNTROWS ( Pedidos ),\n    KEEPFILTERS ( Pedidos[Postagem Elegível] = TRUE () ),\n    KEEPFILTERS ( Pedidos[Postagem no Prazo] = TRUE () )\n)"),
    ("2. Contagens", "Pedidos com Entrega Avaliável", "#,0", "F2", "Pedidos com data de entrega e data estimada.",
     "CALCULATE (\n    COUNTROWS ( Pedidos ),\n    KEEPFILTERS ( Pedidos[Entrega Atrasada] IN { TRUE (), FALSE () } )\n)"),
    ("2. Contagens", "Pedidos com Entrega Atrasada", "#,0", "F2", "Entrega ao cliente depois do dia estimado.",
     "CALCULATE (\n    COUNTROWS ( Pedidos ),\n    KEEPFILTERS ( Pedidos[Entrega Atrasada] = TRUE () )\n)"),

    # 3. Valores (R$)
    ("3. Valores (R$)", "Frete Total", "R$ #,0.00", "-", "Numerador do KPI02: soma do frete dos itens.", "SUM ( Itens[Frete] )"),
    ("3. Valores (R$)", "Valor dos Produtos", "R$ #,0.00", "-", "Denominador do KPI02: soma do preço dos itens.", "SUM ( Itens[Preço] )"),
    ("3. Valores (R$)", "Valor Pago Produtos mais Frete", "R$ #,0.00", "F4",
     "Soma linha a linha de preço + frete do item (expressão por linha, por isso SUMX).",
     "SUMX ( Itens, Itens[Preço] + Itens[Frete] )"),

    # 1. KPIs oficiais (F1)
    ("1. KPIs oficiais", "KPI01 % Avaliações Ruins", "0.0%", "F1", "Alvo: pedidos com nota 1–2 ÷ pedidos avaliados.",
     "DIVIDE ( [Pedidos com Avaliação Ruim], [Pedidos Avaliados] )"),
    ("1. KPIs oficiais", "KPI02 % Frete sobre Produtos", "0.0%", "F1", "Restrição: frete ÷ valor dos produtos (itens dos pedidos entregues).",
     "DIVIDE ( [Frete Total], [Valor dos Produtos] )"),
    ("1. KPIs oficiais", "KPI03 % Postagem no Prazo", "0.0%", "F1", "Alavanca: pedidos postados no prazo ÷ pedidos elegíveis.",
     "DIVIDE ( [Pedidos Postados no Prazo], [Pedidos Elegíveis para Postagem] )"),

    # 4. Apoio ao diagnóstico
    ("4. Diagnóstico", "% Entrega Atrasada", "0.0%", "F1", "Pedidos com entrega atrasada ÷ pedidos com entrega avaliável.",
     "DIVIDE ( [Pedidos com Entrega Atrasada], [Pedidos com Entrega Avaliável] )"),
    ("4. Diagnóstico", "Nota Média de Avaliação", "0.00", "F4", "Média da nota por pedido avaliado (pedidos sem avaliação não entram).",
     "AVERAGEX (\n    FILTER ( Pedidos, NOT ISBLANK ( Pedidos[Nota Avaliação] ) ),\n    Pedidos[Nota Avaliação]\n)"),
    ("4. Diagnóstico", "Média de Dias Postagem até Entrega", "0.0", "F4", "Média por pedido do trecho postagem → cliente.",
     "AVERAGEX (\n    FILTER ( Pedidos, NOT ISBLANK ( Pedidos[Dias Postagem até Entrega] ) ),\n    Pedidos[Dias Postagem até Entrega]\n)"),
    ("4. Diagnóstico", "KPI01 Todas as Regiões", "0.0%", "F3",
     "KPI01 sem filtros de UF/região (ALL), mantendo período e demais filtros. Referência nacional para comparar cortes.",
     "CALCULATE ( [KPI01 % Avaliações Ruins], ALL ( 'Local Cliente' ) )"),
    ("4. Diagnóstico", "KPI01 Desvio vs Todas as Regiões (p.p.)", "+0.0;-0.0;0.0", "F1",
     "Diferença em pontos percentuais entre o corte atual e a referência nacional.",
     "VAR Atual = [KPI01 % Avaliações Ruins]\nVAR Nacional = [KPI01 Todas as Regiões]\nRETURN\n    IF ( NOT ISBLANK ( Atual ), ( Atual - Nacional ) * 100 )"),
    ("4. Diagnóstico", "Pedidos Ruins acima da Média", "#,0", "F3",
     "(Taxa do corte − taxa nacional) × avaliados do corte. REMOVEFILTERS tira UF/região para obter a taxa nacional. Vazio quando o corte está na média ou abaixo.",
     "VAR TaxaNacional =\n    CALCULATE ( [KPI01 % Avaliações Ruins], REMOVEFILTERS ( 'Local Cliente' ) )\nVAR Excedente =\n    ( [KPI01 % Avaliações Ruins] - TaxaNacional ) * [Pedidos Avaliados]\nRETURN\n    IF ( Excedente > 0, Excedente )"),
    ("4. Diagnóstico", "Cor Frete Região", "", "F6", "Cor da coluna: crítico quando o frete do corte passa do limite do KPI geral.",
     f"VAR Frete = [KPI02 % Frete sobre Produtos]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( Frete ), \"{NEUTRO}\", Frete > [Limite Frete KPI02], \"{CRITICO}\", \"{NEUTRO}\" )"),

    # 5. Sellers (granularidade pedido × seller)
    ("5. Sellers", "Pares Pedido-Seller Elegíveis", "#,0", "F2", "Pares pedido × seller com data de postagem e prazo (não são pedidos únicos).",
     "CALCULATE (\n    COUNTROWS ( 'Pedido Seller' ),\n    KEEPFILTERS ( 'Pedido Seller'[Postagem Elegível] = TRUE () )\n)"),
    ("5. Sellers", "Postagens Atrasadas", "#,0", "F2", "Pares pedido × seller com postagem depois do prazo limite.",
     "CALCULATE (\n    COUNTROWS ( 'Pedido Seller' ),\n    KEEPFILTERS ( 'Pedido Seller'[Postagem Elegível] = TRUE () ),\n    KEEPFILTERS ( 'Pedido Seller'[Postagem Atrasada] = TRUE () )\n)"),
    ("5. Sellers", "% Postagem no Prazo do Seller", "0.0%", "F1", "1 − postagens atrasadas ÷ pares elegíveis do seller.",
     "VAR Elegiveis = [Pares Pedido-Seller Elegíveis]\nRETURN\n    IF ( Elegiveis > 0, 1 - DIVIDE ( [Postagens Atrasadas], Elegiveis, 0 ) )"),
    ("5. Sellers", "% Participação nas Postagens Atrasadas", "0.0%", "F3",
     "Postagens atrasadas do seller ÷ todas as postagens atrasadas do período e da região selecionados. REMOVEFILTERS ( Sellers ) tira o seller da linha e o filtro top 10 do visual (ALLSELECTED manteria o top 10 no denominador).",
     "DIVIDE (\n    [Postagens Atrasadas],\n    CALCULATE ( [Postagens Atrasadas], REMOVEFILTERS ( Sellers ) )\n)"),
    ("5. Sellers", "Ranking Seller por Postagens Atrasadas", "0", "F4",
     "Posição do seller por postagens atrasadas entre os sellers da seleção (ALLSELECTED de Sellers: respeita slicers, ignora a UF da linha) com pelo menos 30 pares elegíveis; desempate pela % atrasada.",
     "VAR MinimoPares = 30\nVAR Candidatos =\n    CALCULATETABLE (\n        FILTER (\n            ADDCOLUMNS (\n                VALUES ( Sellers[Seller] ),\n                \"@Pares\", [Pares Pedido-Seller Elegíveis],\n                \"@Pontuacao\", [Postagens Atrasadas] + DIVIDE ( [Postagens Atrasadas], [Pares Pedido-Seller Elegíveis], 0 ) / 10\n            ),\n            [@Pares] >= MinimoPares\n        ),\n        ALLSELECTED ( Sellers )\n    )\nVAR PontuacaoAtual =\n    [Postagens Atrasadas] + DIVIDE ( [Postagens Atrasadas], [Pares Pedido-Seller Elegíveis], 0 ) / 10\nRETURN\n    IF (\n        ISINSCOPE ( Sellers[Seller] ) && [Pares Pedido-Seller Elegíveis] >= MinimoPares,\n        RANKX ( Candidatos, [@Pontuacao], PontuacaoAtual, DESC, DENSE )\n    )"),

    # 6. Inteligência de tempo (F5) — janela observada jan–ago; ano anterior = mesma janela
    ("6. Tempo", "KPI01 Acumulado no Ano", "0.0%", "F5",
     "KPI01 acumulado de janeiro até o mês do contexto (TOTALYTD no numerador e no denominador).",
     "DIVIDE (\n    TOTALYTD ( [Pedidos com Avaliação Ruim], 'Calendário'[Data] ),\n    TOTALYTD ( [Pedidos Avaliados], 'Calendário'[Data] )\n)"),
    ("6. Tempo", "KPI01 Período Anterior", "0.0%", "F5",
     "KPI01 no mesmo período do ano anterior (2025 proxy → 2024 proxy; ambos só têm jan–ago).",
     "CALCULATE ( [KPI01 % Avaliações Ruins], SAMEPERIODLASTYEAR ( 'Calendário'[Data] ) )"),
    ("6. Tempo", "KPI01 Variação vs Período Anterior (p.p.)", "+0.0;-0.0;0.0", "F5",
     "Diferença em p.p. contra o mesmo período do ano anterior.",
     "VAR Atual = [KPI01 % Avaliações Ruins]\nVAR Anterior = [KPI01 Período Anterior]\nRETURN\n    IF ( NOT ISBLANK ( Atual ) && NOT ISBLANK ( Anterior ), ( Atual - Anterior ) * 100 )"),
    ("6. Tempo", "KPI02 Período Anterior", "0.0%", "F5", "KPI02 deslocado 1 ano (DATEADD).",
     "CALCULATE ( [KPI02 % Frete sobre Produtos], DATEADD ( 'Calendário'[Data], -1, YEAR ) )"),
    ("6. Tempo", "KPI02 Variação vs Período Anterior (p.p.)", "+0.0;-0.0;0.0", "F5", "Diferença em p.p. contra o ano anterior.",
     "VAR Atual = [KPI02 % Frete sobre Produtos]\nVAR Anterior = [KPI02 Período Anterior]\nRETURN\n    IF ( NOT ISBLANK ( Atual ) && NOT ISBLANK ( Anterior ), ( Atual - Anterior ) * 100 )"),
    ("6. Tempo", "KPI03 Período Anterior", "0.0%", "F5", "KPI03 deslocado 1 ano (DATEADD).",
     "CALCULATE ( [KPI03 % Postagem no Prazo], DATEADD ( 'Calendário'[Data], -1, YEAR ) )"),
    ("6. Tempo", "KPI03 Variação vs Período Anterior (p.p.)", "+0.0;-0.0;0.0", "F5", "Diferença em p.p. contra o ano anterior.",
     "VAR Atual = [KPI03 % Postagem no Prazo]\nVAR Anterior = [KPI03 Período Anterior]\nRETURN\n    IF ( NOT ISBLANK ( Atual ) && NOT ISBLANK ( Anterior ), ( Atual - Anterior ) * 100 )"),

    # 7. Status (F6) — mensagens em texto para não depender só de cor
    ("7. Status", "KPI01 Status", "", "F6", "Situação do KPI01 frente ao marco de 2026 e à meta de 2027.",
     "VAR Valor = [KPI01 % Avaliações Ruins]\nVAR Marco = [Marco 2026 KPI01]\nVAR Meta = [Meta 2027 KPI01]\nRETURN\n    SWITCH (\n        TRUE (),\n        ISBLANK ( Valor ), \"Sem dados no recorte\",\n        Valor <= Meta, \"✔ Já atinge a meta 2027 (≤ 10%)\",\n        Valor <= Marco, \"● Dentro do marco 2026; faltam \" & FORMAT ( ( Valor - Meta ) * 100, \"0.0\", \"pt-BR\" ) & \" p.p. para 2027\",\n        \"✖ Acima do marco 2026: +\" & FORMAT ( ( Valor - Marco ) * 100, \"0.0\", \"pt-BR\" ) & \" p.p.\"\n    )"),
    ("7. Status", "KPI02 Status", "", "F6", "Situação do KPI02 frente ao limite de 17,1%.",
     "VAR Valor = [KPI02 % Frete sobre Produtos]\nVAR Limite = [Limite Frete KPI02]\nRETURN\n    SWITCH (\n        TRUE (),\n        ISBLANK ( Valor ), \"Sem dados no recorte\",\n        Valor <= Limite, \"✔ Dentro do limite: folga de \" & FORMAT ( ( Limite - Valor ) * 100, \"0.00\", \"pt-BR\" ) & \" p.p.\",\n        \"✖ Acima do limite: +\" & FORMAT ( ( Valor - Limite ) * 100, \"0.00\", \"pt-BR\" ) & \" p.p.\"\n    )"),
    ("7. Status", "KPI03 Status", "", "F6", "Situação do KPI03 frente aos marcos de 95% (2026) e 97% (2027).",
     "VAR Valor = [KPI03 % Postagem no Prazo]\nVAR Marco = [Marco 2026 KPI03]\nVAR Meta = [Meta 2027 KPI03]\nRETURN\n    SWITCH (\n        TRUE (),\n        ISBLANK ( Valor ), \"Sem dados no recorte\",\n        Valor >= Meta, \"✔ Já atinge a meta 2027 (≥ 97%)\",\n        Valor >= Marco, \"● Atinge o marco 2026; faltam \" & FORMAT ( ( Meta - Valor ) * 100, \"0.0\", \"pt-BR\" ) & \" p.p. para 2027\",\n        \"✖ Abaixo do marco 2026: faltam \" & FORMAT ( ( Marco - Valor ) * 100, \"0.0\", \"pt-BR\" ) & \" p.p.\"\n    )"),
    ("7. Status", "KPI01 Cor Status", "", "F6", "Cor semântica do status do KPI01 (acompanha o texto do status).",
     f"VAR Valor = [KPI01 % Avaliações Ruins]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( Valor ), \"{MUDO}\", Valor <= [Meta 2027 KPI01], \"{BOM}\", Valor <= [Marco 2026 KPI01], \"{ALERTA}\", \"{CRITICO}\" )"),
    ("7. Status", "KPI02 Cor Status", "", "F6", "Cor semântica do status do KPI02.",
     f"VAR Valor = [KPI02 % Frete sobre Produtos]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( Valor ), \"{MUDO}\", Valor <= [Limite Frete KPI02], \"{BOM}\", \"{CRITICO}\" )"),
    ("7. Status", "KPI03 Cor Status", "", "F6", "Cor semântica do status do KPI03.",
     f"VAR Valor = [KPI03 % Postagem no Prazo]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( Valor ), \"{MUDO}\", Valor >= [Meta 2027 KPI03], \"{BOM}\", Valor >= [Marco 2026 KPI03], \"{ALERTA}\", \"{CRITICO}\" )"),
    ("7. Status", "KPI01 Contexto", "", "F6", "Linha de contexto do cartão: variação vs período anterior e referência da proposta.",
     "VAR Variacao = [KPI01 Variação vs Período Anterior (p.p.)]\nRETURN\n    \"vs ano anterior: \"\n        & IF ( ISBLANK ( Variacao ), \"n/d\", FORMAT ( Variacao, \"+0.0;-0.0;0.0\", \"pt-BR\" ) & \" p.p.\" )\n        & \"  ·  proposta 2025: \" & FORMAT ( [Referência Proposta 2025 KPI01], \"0.0%\", \"pt-BR\" )"),
    ("7. Status", "KPI02 Contexto", "", "F6", "Linha de contexto do cartão: variação vs período anterior e referência da proposta.",
     "VAR Variacao = [KPI02 Variação vs Período Anterior (p.p.)]\nRETURN\n    \"vs ano anterior: \"\n        & IF ( ISBLANK ( Variacao ), \"n/d\", FORMAT ( Variacao, \"+0.0;-0.0;0.0\", \"pt-BR\" ) & \" p.p.\" )\n        & \"  ·  proposta 2025: \" & FORMAT ( [Referência Proposta 2025 KPI02], \"0.0%\", \"pt-BR\" )"),
    ("7. Status", "KPI03 Contexto", "", "F6", "Linha de contexto do cartão: variação vs período anterior e referência da proposta.",
     "VAR Variacao = [KPI03 Variação vs Período Anterior (p.p.)]\nRETURN\n    \"vs ano anterior: \"\n        & IF ( ISBLANK ( Variacao ), \"n/d\", FORMAT ( Variacao, \"+0.0;-0.0;0.0\", \"pt-BR\" ) & \" p.p.\" )\n        & \"  ·  proposta 2025: \" & FORMAT ( [Referência Proposta 2025 KPI03], \"0.0%\", \"pt-BR\" )"),
    ("7. Status", "KPI01 Metas", "", "F6", "Marco 2026 e meta 2027 do KPI01 em texto.",
     "\"Marco 2026: \" & FORMAT ( [Marco 2026 KPI01], \"0.0%\", \"pt-BR\" ) & \"  ·  Meta 2027: \" & FORMAT ( [Meta 2027 KPI01], \"0.0%\", \"pt-BR\" )"),
    ("7. Status", "KPI02 Metas", "", "F6", "Limite do KPI02 em texto.",
     "\"Limite 2026 e 2027: ≤ \" & FORMAT ( [Limite Frete KPI02], \"0.0%\", \"pt-BR\" ) & \" (KPI geral)\""),
    ("7. Status", "KPI03 Metas", "", "F6", "Marco 2026 e meta 2027 do KPI03 em texto.",
     "\"Marco 2026: \" & FORMAT ( [Marco 2026 KPI03], \"0.0%\", \"pt-BR\" ) & \"  ·  Meta 2027: \" & FORMAT ( [Meta 2027 KPI03], \"0.0%\", \"pt-BR\" )"),
]

def tmdl_measure(pasta, nome, fmt, familia, desc, dax) -> str:
    lines = [f"\t/// {desc}" + (f" [{familia}]" if familia != "-" else "")]
    expr = dax.splitlines()
    if len(expr) == 1:
        lines.append(f"\tmeasure {q(nome)} = {expr[0]}")
    else:
        lines.append(f"\tmeasure {q(nome)} =")
        lines += ["\t\t\t" + ln for ln in expr]
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tdisplayFolder: {pasta}")
    lines.append(f"\t\tlineageTag: {tag(P, nome)}")
    return "\n".join(lines) + "\n"


RELACOES = [
    ("Pedidos", "Data Compra", "Calendário", "Data"),
    ("Itens", "Data Compra", "Calendário", "Data"),
    ("Pedido Seller", "Data Compra", "Calendário", "Data"),
    ("Pedidos", "UF Cliente", "Local Cliente", "UF"),
    ("Itens", "UF Cliente", "Local Cliente", "UF"),
    ("Pedido Seller", "UF Cliente", "Local Cliente", "UF"),
    ("Itens", "ID Seller", "Sellers", "ID Seller"),
    ("Pedido Seller", "ID Seller", "Sellers", "ID Seller"),
]


def gerar_modelo() -> None:
    d = SM / "definition"
    if SM.exists():
        shutil.rmtree(SM)
    write_json(SM / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    ordem = ["PastaDados", "Calendário", *TABELAS_CSV, "Medidas"]
    write(d / "model.tmdl",
          "model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: pt-BR\n"
          "\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
          "annotation __PBI_TimeIntelligenceEnabled = 0\n\n"
          f"annotation PBI_QueryOrder = {json.dumps(ordem, ensure_ascii=False)}\n")
    pasta = str(DADOS) + "\\"
    write(d / "expressions.tmdl",
          "/// Pasta com os CSVs do modelo (termina com barra invertida). Altere em Transformar dados > Parâmetros.\n"
          f'expression PastaDados = "{pasta}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
          f"\tlineageTag: {tag('PastaDados')}\n\n\tannotation PBI_ResultType = Text\n")

    for nome, (arquivo, desc, cols) in TABELAS_CSV.items():
        cols_tmdl = "\n".join(tmdl_col(nome, n, t, o) for _, n, t, o in cols)
        write(d / "tables" / f"{nome}.tmdl", tmdl_table(nome, desc, cols_tmdl, m_csv(arquivo, cols)))

    cal_cols = "\n".join(tmdl_col("Calendário", n, t, o) for n, t, o in CALENDARIO_COLS)
    write(d / "tables" / "Calendário.tmdl",
          tmdl_table("Calendário", "Dimensão de datas contínua 2017–2018, marcada como tabela de datas (dataCategory Time + chave Data).",
                     cal_cols, M_CALENDARIO, extra="\tdataCategory: Time\n"))

    med = "\n".join(tmdl_measure(*m) for m in MEDIDAS)
    aux = ("\tcolumn Auxiliar\n\t\tdataType: string\n\t\tisHidden\n"
           f"\t\tlineageTag: {tag(P, 'Auxiliar')}\n\t\tsummarizeBy: none\n\t\tsourceColumn: Auxiliar\n")
    write(d / "tables" / "Medidas.tmdl",
          f"/// Tabela dedicada a todas as medidas DAX do relatório.\ntable Medidas\n\tlineageTag: {tag(P)}\n\n"
          f"{med}\n{aux}\n{tmdl_partition(P, M_MEDIDAS)}\n"
          "\tannotation PBI_ResultType = Table\n")

    rel = ""
    for ft, fc, tt, tc in RELACOES:
        rel += (f"relationship {tag('rel', ft, fc, tt)}\n\tfromColumn: {q(ft)}.{q(fc)}\n\ttoColumn: {q(tt)}.{q(tc)}\n\n")
    write(d / "relationships.tmdl", rel)


# =============================================================================
# 2. Relatório (PBIR)
# =============================================================================
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_VISUAL, V_PAGE, V_REPORT = "2.4.0", "2.0.0", "3.0.0"


def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def num(v):  # números de formatação (tamanho de fonte, posição) usam sufixo D
    return {"expr": {"Literal": {"Value": f"{v}D"}}}


def cor(hexa):
    return {"solid": {"color": lit(hexa)}}


def col(entidade, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entidade}}, "Property": prop}}


def med(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": P}}, "Property": prop}}


def ref(campo):
    k = "Column" if "Column" in campo else "Measure"
    return f"{campo[k]['Expression']['SourceRef']['Entity']}.{campo[k]['Property']}"


def proj(campo, nome=None):
    p = {"field": campo, "queryRef": ref(campo), "nativeQueryRef": campo[next(iter(campo))]["Property"]}
    if nome:
        p["displayName"] = nome
    return p


def props(**kw):
    return [{"properties": kw}]


def titulo(texto, tamanho=11):
    return {
        "title": props(show=lit(True), text=lit(texto), fontSize=num(tamanho), fontColor=cor(TINTA), bold=lit(True),
                       titleWrap=lit(True)),
        "background": props(show=lit(True), color=cor(FUNDO_CARTAO), transparency=num(0)),
        "border": props(show=lit(True), color=cor(GRADE), radius=num(6)),
        "padding": props(top=num(6), bottom=num(6), left=num(10), right=num(10)),
        "dropShadow": props(show=lit(False)),
    }


def sem_titulo(fundo=True):
    o = {"title": props(show=lit(False)), "dropShadow": props(show=lit(False))}
    o["background"] = props(show=lit(True), color=cor(FUNDO_CARTAO), transparency=num(0)) if fundo else props(show=lit(False))
    o["border"] = props(show=lit(False))
    return o


def filtro_where(entidade, alias, condicao):
    return {"Version": 2, "From": [{"Name": alias, "Entity": entidade, "Type": 0}], "Where": [{"Condition": condicao}]}


def cond_in(alias, prop, valores, negar=False):
    c = {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                "Values": [[lit(v)["expr"]] for v in valores]}}
    return {"Not": {"Expression": c}} if negar else c


class Pagina:
    def __init__(self, nome, titulo_pagina, largura, altura):
        self.nome, self.titulo, self.largura, self.altura = nome, titulo_pagina, largura, altura
        self.visuais = []

    def add(self, nome, x, y, w, h, visual, filtros=None):
        v = {"$schema": f"{SCHEMA}/visualContainer/{V_VISUAL}/schema.json", "name": nome,
             "position": {"x": x, "y": y, "z": len(self.visuais) * 1000, "width": w, "height": h,
                          "tabOrder": len(self.visuais) * 1000},
             "visual": visual}
        if filtros:
            v["filterConfig"] = {"filters": filtros}
        self.visuais.append(v)

    def salvar(self, base: Path):
        pdir = base / self.nome
        write_json(pdir / "page.json", {
            "$schema": f"{SCHEMA}/page/{V_PAGE}/schema.json", "name": self.nome, "displayName": self.titulo,
            "displayOption": "FitToPage", "height": self.altura, "width": self.largura,
            "objects": {"background": props(color=cor(FUNDO_PAGINA), transparency=num(0)),
                        "outspace": props(color=cor(FUNDO_PAGINA), transparency=num(0))}})
        for v in self.visuais:
            write_json(pdir / "visuals" / v["name"] / "visual.json", v)


def texto(paragrafos, fundo=False):
    """paragrafos = [[(texto, tamanho_pt, negrito, cor), ...], ...]"""
    pars = []
    for runs in paragrafos:
        pars.append({"textRuns": [{"value": t, "textStyle": {"fontFamily": "Segoe UI", "fontSize": f"{s}pt",
                                                              "fontWeight": "bold" if b else "normal", "color": c}}
                                  for t, s, b, c in runs]})
    vis = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": pars}}]},
           "visualContainerObjects": sem_titulo(fundo)}
    vis["visualContainerObjects"]["padding"] = props(top=num(2), bottom=num(0), left=num(10), right=num(10))
    return vis


def cartao(medida, tamanho, cor_medida=None, cor_fixa=TINTA, negrito=False):
    cor_label = {"solid": {"color": {"expr": med(cor_medida)}}} if cor_medida else cor(cor_fixa)
    return {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [proj(med(medida))]}}},
        "objects": {
            "labels": props(color=cor_label, fontSize=num(tamanho), fontFamily=lit("Segoe UI Semibold" if negrito else "Segoe UI")),
            "categoryLabels": props(show=lit(False)),
            "wordWrap": props(show=lit(True)),
        },
        "visualContainerObjects": sem_titulo(),
    }


def eixo_y(inicio=0.0, fim=None, mostrar=True, sec=False):
    p = {"show": lit(mostrar), "start": num(inicio), "gridlineShow": lit(True), "gridlineColor": cor(GRADE),
         "labelColor": cor(MUDO), "fontSize": num(8), "showAxisTitle": lit(False)}
    if fim is not None:
        p["end"] = num(fim)
    if sec:
        p.update({"secShow": lit(False), "secStart": num(inicio), "secEnd": num(fim)})
    return props(**p)


def eixo_x():
    return props(show=lit(True), labelColor=cor(TINTA2), fontSize=num(9), showAxisTitle=lit(False))


def legenda(mostrar=True, posicao="TopLeft"):
    return props(show=lit(mostrar), position=lit(posicao), labelColor=cor(TINTA2), fontSize=num(8), showTitle=lit(False))


def rotulos(mostrar=True, tamanho=8):
    return props(show=lit(mostrar), color=cor(TINTA2), fontSize=num(tamanho))


def cor_serie(medida_ref, hexa):
    return {"properties": {"fill": cor(hexa)}, "selector": {"metadata": medida_ref}}


def cor_categoria_serie(entidade, coluna, valor, hexa):
    return {"properties": {"fill": cor(hexa)},
            "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": col(entidade, coluna),
                                                              "Right": {"Literal": {"Value": f"'{valor}'"}}}}}]}}


def filtro_medida(nome, medida, tipo_comparacao, valor_literal):
    return {"name": nome, "field": med(medida), "type": "Advanced",
            "filter": filtro_where(P, "m", {"Comparison": {
                "ComparisonKind": tipo_comparacao,
                "Left": {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": medida}},
                "Right": {"Literal": {"Value": valor_literal}}}})}


def filtro_faixa(nome, medida, minimo, maximo):
    m = {"Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": medida}}
    return {"name": nome, "field": med(medida), "type": "Advanced",
            "filter": filtro_where(P, "m", {"And": {
                "Left": {"Comparison": {"ComparisonKind": 2, "Left": m, "Right": {"Literal": {"Value": minimo}}}},
                "Right": {"Comparison": {"ComparisonKind": 4, "Left": m, "Right": {"Literal": {"Value": maximo}}}}}})}


def filtro_excluir(nome, entidade, coluna, valores):
    return {"name": nome, "field": col(entidade, coluna), "type": "Categorical",
            "filter": filtro_where(entidade, "t", cond_in("t", coluna, valores, negar=True))}


def tabela(colunas, larguras, tamanho=9, ordenar=None, crescente=True):
    vis = {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [proj(c, n) for c, n in colunas]}}},
        "objects": {
            "columnHeaders": props(fontSize=num(tamanho), fontColor=cor(TINTA), bold=lit(True), wordWrap=lit(True),
                                   backColor=cor("#f0efec"), autoSizeColumnWidth=lit(False)),
            "values": props(fontSize=num(tamanho), fontColorPrimary=cor(TINTA), fontColorSecondary=cor(TINTA),
                            backColorPrimary=cor(FUNDO_CARTAO), backColorSecondary=cor("#fafaf8"), wordWrap=lit(True)),
            "total": props(totals=lit(False)),
            "grid": props(gridHorizontal=lit(True), gridHorizontalColor=cor(GRADE), gridVertical=lit(False),
                          rowPadding=num(1), textSize=num(tamanho)),
            "columnWidth": [{"properties": {"value": num(w)}, "selector": {"metadata": ref(c)}}
                            for (c, _), w in zip(colunas, larguras)],
        },
    }
    if ordenar is not None:
        vis["query"]["sortDefinition"] = {"sort": [{"field": ordenar, "direction": "Ascending" if crescente else "Descending"}],
                                          "isDefaultSort": False}
    return vis


def slicer(entidade, coluna, titulo_slicer, selecao=None, unico=False):
    gen = {}
    if selecao:
        gen["filter"] = {"filter": filtro_where(entidade, "s", cond_in("s", coluna, selecao))}
    vis = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj(col(entidade, coluna))]}}},
        "objects": {
            "data": props(mode=lit("Dropdown")),
            "selection": props(singleSelect=lit(unico), strictSingleSelect=lit(unico), selectAllCheckboxEnabled=lit(not unico)),
            "header": props(show=lit(True), text=lit(titulo_slicer), fontColor=cor(TINTA2), textSize=num(9)),
            "items": props(fontColor=cor(TINTA), textSize=num(9)),
        },
        "visualContainerObjects": sem_titulo(),
    }
    if gen:
        vis["objects"]["general"] = [{"properties": gen}]
    return vis


def pagina_dashboard() -> Pagina:
    pg = Pagina("dashboard", "Dashboard executivo", 1280, 720)

    # Cabeçalho
    pg.add("cabecalho", 16, 4, 880, 72, texto([
        [("Insatisfação acompanha a entrega atrasada, não a postagem do seller: priorizar a logística regional "
          "sem passar de 17,1% de frete", 13, True, TINTA)],
        [("Pedidos entregues, compra em jan–ago  ·  2024 = proxy jan–ago/2017  ·  2025 = proxy jan–ago/2018 "
          "(rótulos acadêmicos, não dados reais)", 9, False, TINTA2)],
    ]))
    pg.add("slicer_periodo", 908, 12, 186, 54, slicer("Calendário", "Período", "Período comparável", [PERIODO_2025], unico=True))
    pg.add("slicer_regiao", 1102, 12, 162, 54, slicer("Local Cliente", "Região", "Região do cliente"))

    # Três KPIs (únicos cartões de destaque)
    blocos = [
        ("KPI01", "ALVO  ·  KPI01 % de pedidos com avaliação ruim (nota 1–2)", "KPI01 % Avaliações Ruins"),
        ("KPI02", "RESTRIÇÃO  ·  KPI02 Frete ÷ valor dos produtos", "KPI02 % Frete sobre Produtos"),
        ("KPI03", "ALAVANCA  ·  KPI03 % de pedidos postados no prazo pelo seller", "KPI03 % Postagem no Prazo"),
    ]
    for i, (k, rotulo, medida) in enumerate(blocos):
        x, y = 16 + i * 419, 78
        pg.add(f"{k.lower()}_rotulo", x, y, 410, 26, texto([[(rotulo, 9, True, TINTA2)]], fundo=True))
        pg.add(f"{k.lower()}_valor", x, y + 26, 118, 78, cartao(medida, 28, cor_fixa=TINTA, negrito=True))
        pg.add(f"{k.lower()}_status", x + 118, y + 26, 292, 28, cartao(f"{k} Status", 10, cor_medida=f"{k} Cor Status", negrito=True))
        pg.add(f"{k.lower()}_contexto", x + 118, y + 54, 292, 25, cartao(f"{k} Contexto", 8.5, cor_fixa=TINTA2))
        pg.add(f"{k.lower()}_metas", x + 118, y + 79, 292, 25, cartao(f"{k} Metas", 8.5, cor_fixa=TINTA2))

    # G1 — evolução mensal
    k1, ea = med("KPI01 % Avaliações Ruins"), med("% Entrega Atrasada")
    pg.add("g1_mensal", 16, 190, 410, 240, {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(col("Calendário", "Mês"))]},
            "Y": {"projections": [proj(k1, "Avaliação ruim (%)"), proj(ea, "Entrega atrasada (%)")]},
            "Tooltips": {"projections": [proj(med("KPI01 Acumulado no Ano"), "Avaliação ruim acumulada no ano"),
                                         proj(med("Pedidos Avaliados"), "Pedidos avaliados")]}},
            "sortDefinition": {"sort": [{"field": col("Calendário", "Mês"), "direction": "Ascending"}], "isDefaultSort": True}},
        "objects": {
            "dataPoint": [cor_serie(ref(k1), AZUL), cor_serie(ref(ea), LARANJA)],
            "lineStyles": props(strokeWidth=num(2), showMarker=lit(True), markerSize=num(4)),
            "valueAxis": eixo_y(0.0, 0.30), "categoryAxis": eixo_x(), "legend": legenda(posicao="TopRight"),
            "labels": [{"properties": {"show": lit(True), "color": cor(TINTA2), "fontSize": num(7), "labelDensity": num(40)}},
                       {"properties": {"showSeries": lit(False)}, "selector": {"metadata": ref(ea)}}],
        },
        "visualContainerObjects": titulo("G1 · A piora de 2025 concentra-se em fev–mar, junto com a entrega atrasada"),
    })

    # G2 — UFs com maior excedente de avaliações ruins
    exc = med("Pedidos Ruins acima da Média")
    pg.add("g2_uf_excedente", 435, 190, 410, 240, {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(col("Local Cliente", "UF"))]},
            "Y": {"projections": [proj(exc, "Pedidos ruins acima da média nacional")]},
            "Tooltips": {"projections": [proj(med("KPI01 % Avaliações Ruins"), "Avaliação ruim (%)"),
                                         proj(med("Pedidos Avaliados"), "Pedidos avaliados"),
                                         proj(med("% Entrega Atrasada"), "Entrega atrasada (%)"),
                                         proj(med("KPI01 Desvio vs Todas as Regiões (p.p.)"), "Desvio vs nacional (p.p.)")]}},
            "sortDefinition": {"sort": [{"field": exc, "direction": "Descending"}], "isDefaultSort": False}},
        "objects": {
            "dataPoint": [cor_serie(ref(exc), AZUL)],
            "valueAxis": eixo_y(0.0, mostrar=False), "categoryAxis": eixo_x(), "legend": legenda(False),
            "labels": rotulos(True, 8),
        },
        "visualContainerObjects": titulo("G2 · RJ concentra o maior excedente de avaliações ruins, seguido de BA e CE "
                                         "(UFs com ≥ 20 pedidos ruins acima da média)"),
    }, filtros=[filtro_medida("f_excedente", "Pedidos Ruins acima da Média", 2, "20D")])

    # G3 — frete por região com o limite do KPI geral (eixo único fixo 0–30%)
    k2, lim = med("KPI02 % Frete sobre Produtos"), med("Limite Frete KPI02")
    pg.add("g3_frete_regiao", 854, 190, 410, 240, {
        "visualType": "lineClusteredColumnComboChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(col("Local Cliente", "Região"))]},
            "Y": {"projections": [proj(k2, "Frete ÷ produtos (%)")]},
            "Y2": {"projections": [proj(lim, "Limite do KPI geral (17,1%)")]},
            "Tooltips": {"projections": [proj(med("Pedidos Entregues"), "Pedidos entregues"),
                                         proj(med("Frete Total"), "Frete total"),
                                         proj(med("KPI01 % Avaliações Ruins"), "Avaliação ruim (%)")]}},
            "sortDefinition": {"sort": [{"field": k2, "direction": "Descending"}], "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": {"solid": {"color": {"expr": med("Cor Frete Região")}}}},
                           "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}},
                          cor_serie(ref(lim), TINTA)],
            "lineStyles": [{"properties": {"strokeWidth": num(2), "lineStyle": lit("dashed"), "showMarker": lit(False)},
                            "selector": {"metadata": ref(lim)}}],
            "valueAxis": eixo_y(0.0, 0.30, sec=True), "categoryAxis": eixo_x(), "legend": legenda(False),
            "labels": [{"properties": {"show": lit(True), "color": cor(TINTA2), "fontSize": num(8)}},
                       {"properties": {"showSeries": lit(False)}, "selector": {"metadata": ref(lim)}}],
        },
        "visualContainerObjects": titulo("G3 · Só o Sudeste fica abaixo do teto de 17,1% (linha); Norte e Nordeste têm o frete mais alto"),
    })

    # G4 — avaliação ruim por combinação postagem × entrega
    pg.add("g4_postagem_entrega", 16, 438, 520, 244, {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(col("Pedidos", "Situação Entrega"))]},
            "Series": {"projections": [proj(col("Pedidos", "Situação Postagem"))]},
            "Y": {"projections": [proj(k1, "Avaliação ruim (%)")]},
            "Tooltips": {"projections": [proj(med("Pedidos Avaliados"), "Pedidos avaliados"),
                                         proj(med("Pedidos com Avaliação Ruim"), "Pedidos com avaliação ruim")]}},
            "sortDefinition": {"sort": [{"field": col("Pedidos", "Situação Entrega"), "direction": "Descending"}], "isDefaultSort": False}},
        "objects": {
            "dataPoint": [cor_categoria_serie("Pedidos", "Situação Postagem", "Postagem no prazo", AZUL),
                          cor_categoria_serie("Pedidos", "Situação Postagem", "Postagem atrasada", LARANJA)],
            "valueAxis": eixo_y(0.0, 0.75), "categoryAxis": eixo_x(), "legend": legenda(), "labels": rotulos(True, 9),
        },
        "visualContainerObjects": titulo("G4 · Com entrega atrasada, ~63% avaliam mal, com ou sem postagem atrasada; "
                                         "a postagem atrasada sozinha pesa pouco"),
    }, filtros=[filtro_excluir("f_sem_entrega", "Pedidos", "Situação Entrega", ["Sem dado"]),
                filtro_excluir("f_sem_postagem", "Pedidos", "Situação Postagem", ["Sem dado"])])

    # G5 — ranking de sellers
    rk = med("Ranking Seller por Postagens Atrasadas")
    pg.add("g5_sellers", 545, 438, 719, 244, {
        **tabela([(rk, "#"), (col("Sellers", "Seller"), "Seller"), (col("Sellers", "UF Seller"), "UF"),
                  (med("Pares Pedido-Seller Elegíveis"), "Pares"),
                  (med("Postagens Atrasadas"), "Atrasadas"),
                  (med("% Postagem no Prazo do Seller"), "% no prazo"),
                  (med("% Participação nas Postagens Atrasadas"), "% do total atrasado")],
                 [30, 150, 40, 90, 90, 90, 130], tamanho=8, ordenar=rk),
        "visualContainerObjects": titulo("G5 · 10 sellers somam ~20% das postagens atrasadas (mín. 30 pares pedido–seller)"),
    }, filtros=[filtro_faixa("f_top10", "Ranking Seller por Postagens Atrasadas", "1L", "10L")])

    # Rodapé
    pg.add("rodape", 16, 684, 1248, 36, texto([
        [(AUTORES, 7.5, True, TINTA2)],
        [("Fonte: Olist (Kaggle), outputs E1 de 19/10/2026  ·  pedidos entregues, compra em jan–ago  ·  2024 = proxy jan–ago/2017, "
          "2025 = proxy jan–ago/2018, sem dado observado de 2026  ·  avaliação mais recente por pedido  ·  títulos referem-se ao "
          "recorte padrão 2025  ·  associação não prova causalidade", 6.3, False, MUDO)],
    ]))
    return pg


def gerar_relatorio() -> None:
    if RP.exists():
        shutil.rmtree(RP)
    write_json(RP / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}}})
    d = RP / "definition"
    write_json(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    versao = {"visual": V_VISUAL, "page": V_PAGE, "report": V_REPORT}
    write_json(d / "report.json", {
        "$schema": f"{SCHEMA}/report/{V_REPORT}/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": versao, "type": "SharedResources"},
            "customTheme": {"name": "OlistCP5.json", "reportVersionAtImport": versao, "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "OlistCP5.json", "path": "OlistCP5.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    })
    tema = next(PBI_BIN.glob(f"Microsoft.MicrosoftPowerBIDesktop_*/bin/WebView2Resources/minerva/sharedresources/BaseThemes/{BASE_THEME}.json"))
    destino = RP / "StaticResources" / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(tema, destino)
    write_json(RP / "StaticResources" / "RegisteredResources" / "OlistCP5.json", {
        "name": "Olist CP5",
        "dataColors": [AZUL, LARANJA, "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
        "foreground": TINTA, "foregroundNeutralSecondary": TINTA2, "foregroundNeutralTertiary": MUDO,
        "background": FUNDO_CARTAO, "backgroundLight": "#fafaf8", "backgroundNeutral": GRADE, "tableAccent": AZUL,
        "good": BOM, "neutral": ALERTA, "bad": CRITICO,
        "textClasses": {
            "callout": {"fontFace": "Segoe UI Semibold", "color": TINTA},
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": TINTA},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 10, "color": TINTA},
            "label": {"fontFace": "Segoe UI", "fontSize": 9, "color": TINTA2},
        },
    })
    paginas = [pagina_dashboard()]
    for p in paginas:
        p.salvar(d / "pages")
    write_json(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
                                            "pageOrder": [p.nome for p in paginas], "activePageName": paginas[0].nome})


def gerar_pbip() -> None:
    write_json(PBI / f"{NOME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NOME}.Report"}}], "settings": {"enableAutoRecovery": True}})
    write(PBI / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")


if __name__ == "__main__":
    gerar_modelo()
    gerar_relatorio()
    gerar_pbip()
    print(f"Projeto gerado em {PBI}  ({len(MEDIDAS)} medidas)")
