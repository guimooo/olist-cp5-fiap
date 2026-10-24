"""Texto da ficha técnica do dashboard Olist CP5, usado por 05_gerar_ficha_tecnica_pdf.py.

Os números citados aqui foram conferidos no modelo Power BI (validacao_dax_resultado.txt) e são
checados de novo pelo gerador do PDF contra os CSVs da E1.
"""

# =============================================================================
# Texto da ficha técnica (definições dos KPIs e registro dos visuais do dashboard)
# =============================================================================
FICHA_KPIS = [
    {
        "ordem": 1, "codigo": "KPI01", "papel": "Alvo",
        "kpi": "% de pedidos entregues com avaliação ruim (nota 1 ou 2)",
        "formula": "Pedidos entregues com nota 1–2 ÷ pedidos entregues com avaliação válida. "
                   "Uma avaliação por pedido: a mais recente (review_creation_date; desempate answer_timestamp, review_id).",
        "observacao": "476 pedidos sem avaliação (0,64%) ficam fora do denominador; 391 pedidos com mais de uma "
                      "avaliação usam a mais recente. Recalculado = proposta, diferença só de arredondamento.",
    },
    {
        "ordem": 2, "codigo": "KPI02", "papel": "Restrição",
        "kpi": "Frete ÷ valor dos produtos",
        "formula": "Σ freight_value ÷ Σ price dos itens dos pedidos entregues (somado no nível item, sem join que duplique frete).",
        "observacao": "380 itens com frete zero mantidos (frete grátis). O limite de 17,1% vale para o agregado; "
                      "os cortes por região são diagnóstico, não limites individuais.",
    },
    {
        "ordem": 3, "codigo": "KPI03", "papel": "Alavanca",
        "kpi": "% de pedidos postados no prazo pelo seller",
        "formula": "Pedidos com order_delivered_carrier_date ≤ menor shipping_limit_date dos itens ÷ pedidos elegíveis "
                   "(com data de postagem e prazo). Postar exatamente no limite = no prazo.",
        "observacao": "1 pedido sem data de postagem excluído; 165 pedidos com postagem anterior à compra mantidos e "
                      "sinalizados. A data de postagem é do pedido, não de cada seller.",
    },
]

REGISTRO_VISUAIS = [
    ("C1", "Cartão KPI01 · Avaliação ruim (alvo)",
     "Qual é a taxa de insatisfação e quão longe está do marco de 2026 e da meta de 2027?",
     "Número único com status em texto e variação vs período anterior: o KPI é a manchete, e um gráfico só o repetiria.",
     "13,4% na proxy 2025 (+2,8 p.p. vs 10,6% na proxy 2024). Está acima do marco de 12% de 2026 e 3,4 p.p. acima da meta de 10% de 2027.",
     "Confirma a urgência: o alvo piorou e precisa cair 3,4 p.p. até dez/2027."),
    ("C2", "Cartão KPI02 · Frete / produtos (restrição)",
     "Há folga de custo para melhorar a entrega pagando mais frete?",
     "Número único com o teto visível e a distância em p.p.: a pergunta é binária (dentro ou fora do limite).",
     "17,09% na proxy 2025, a 0,01 p.p. do teto de 17,1% (16,02% na proxy 2024: +1,1 p.p.).",
     "Não há espaço para comprar pontualidade com frete mais caro de forma generalizada."),
    ("C3", "Cartão KPI03 · Postagem no prazo (alavanca)",
     "A pontualidade dos sellers piorou junto com a avaliação?",
     "Número único com variação vs período anterior e distância para os marcos de 95% (2026) e 97% (2027).",
     "91,5% na proxy 2025, estável vs 91,4% na proxy 2024; faltam 3,5 p.p. para o marco de 95%.",
     "A postagem não piorou enquanto a avaliação ruim subiu, então não explica sozinha a piora."),
    ("G1", "Linha mensal · avaliação ruim × entrega atrasada",
     "Quando a insatisfação piorou e o que mudou junto?",
     "Linha no tempo com duas taxas na mesma escala (%): mostra se as curvas sobem juntas mês a mês.",
     "Fev e mar/2018: 19,4% e 21,2% de avaliação ruim, com 14,1% e 19,0% de entrega atrasada. Esses dois meses somam "
     "2.733 dos 7.016 pedidos ruins (39%). Em abr–ago/2018 o KPI01 foi 10,4%.",
     "Plano de capacidade logística para picos e acompanhamento mensal do KPI01 junto da entrega atrasada."),
    ("G2", "Barras por UF · pedidos ruins acima da média",
     "Onde está o maior volume de insatisfação acima do normal?",
     "Barra horizontal ordenada pelo excedente absoluto (taxa da UF − taxa geral) × avaliados, que combina taxa e "
     "volume. Taxa, denominador e entrega atrasada ficam no tooltip.",
     "RJ lidera com ~427 pedidos ruins acima da média (20,2% de 6.279 avaliados; 13,7% de entrega atrasada). Depois "
     "vêm BA (~74), CE (~44), PA (~33) e MA (~24).",
     "Define as rotas prioritárias do SLA logístico: RJ, mais Nordeste e Norte."),
    ("G3", "Colunas por região · frete / produtos com limite",
     "Em que região o frete pressiona o teto de 17,1%?",
     "Colunas por região e linha do limite no mesmo eixo fixo (0–30%), com as regiões acima do teto em vermelho e rótulo de valor.",
     "Só o Sudeste (15,5%, 70% dos pedidos) fica abaixo do teto. Norte 23,9%, Nordeste 22,7%, Centro-Oeste 18,8% e Sul 18,3% "
     "ficam acima, e o agregado fecha em 17,09%. O limite vale para o KPI geral, e o corte regional é diagnóstico.",
     "Renegociar SLA no N/NE sem subir o frete médio; o ganho de eficiência tem de vir de outras rotas."),
    ("G4", "Colunas agrupadas · postagem × entrega",
     "O que está mais associado à avaliação ruim: a postagem atrasada ou a entrega atrasada?",
     "Colunas agrupadas comparam as quatro combinações postagem × entrega no mesmo eixo de taxa, com os avaliados no tooltip.",
     "Com entrega atrasada, ~63% avaliam mal, com ou sem postagem atrasada. Postagem atrasada com entrega no prazo dá "
     "13,5% (vs 9,0%). 75% das entregas atrasadas tiveram postagem no prazo. É associação, não causalidade.",
     "Prioridade principal na logística (trecho postagem → cliente); sellers como alavanca secundária."),
    ("G5", "Tabela ranqueada · sellers com mais postagens atrasadas",
     "Quais sellers concentram os atrasos de postagem?",
     "Ranking (RANKX) com denominador visível e mínimo de 30 pares pedido–seller, para não destacar amostras pequenas.",
     "Na proxy 2025, os 10 primeiros somam 896 das 4.522 postagens atrasadas (19,8%) com 8,7% do volume. O nº 1 "
     "atrasou 164 de 478 (34%).",
     "Programa focado de pontualidade (alerta e penalidade progressiva) nos reincidentes para levar o KPI03 a 95%."),
]
