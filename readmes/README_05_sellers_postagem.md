# 05 — Sellers: pontualidade de postagem e rankings de atraso

**Notebook:** [`notebooks/05_sellers_postagem.ipynb`](../notebooks/05_sellers_postagem.ipynb)

## Objetivo
Diagnosticar, de forma retrospectiva, quais sellers concentram as postagens atrasadas, e gerar o top 50 e o ranking semanal propostos pelo grupo.

## Tratamentos
- **Base pedido–seller** (75.845 linhas para 74.781 pedidos únicos; 1.012 pedidos com mais de um seller). Para cada pedido + seller, o prazo é o **menor** `shipping_limit_date` dos itens daquele seller, comparado com a data de postagem do pedido (`<=` = no prazo).
- As contagens são de **pedido–seller** (colunas com prefixo `pedido_seller_`). Elas não devem ser somadas como pedidos únicos; o KPI3 oficial está no notebook 03.
- Ranking por **número absoluto** de postagens atrasadas, com taxa, volume e `amostra_pequena` (menos de 30 elegíveis) lado a lado.
- **Ranking semanal:** semana (segunda a domingo) da data limite de postagem; top 50 sellers com mais atrasos em cada semana. A semana pode cair fora de jan–ago (ex.: compra em 31/08 com prazo em setembro).

## Resultados
- 6.451 postagens atrasadas (pedido–seller); 1.194 dos 2.810 sellers tiveram ao menos uma.
- **Concentração:**

| Top N sellers | % das postagens atrasadas | % do volume pedido–seller |
|---:|---:|---:|
| 10 | 16,9 | 8,1 |
| 50 | 39,9 | 23,9 |
| 100 | 53,2 | 31,2 |
| 200 | 67,8 | 47,4 |

- O seller nº 1 (`7c67e144…`, SP) tem 221 atrasos em 793 elegíveis (27,9%) e apareceu em 36 das 72 semanas do ranking semanal.
- Há sellers com taxa muito alta e volume relevante (ex.: `88460e8e…`, PR: 48,1% de atraso em 231).
- Por UF do seller (proxy 2025), SP concentra o volume absoluto de atrasos (3.212). O MA tem 31,1% de atraso, mas concentrado em **um único** seller.
- 2.286 dos 2.810 sellers têm menos de 30 pedidos elegíveis (`amostra_pequena`), por isso o ranking usa volume absoluto.

## Saídas
| Arquivo | Granularidade |
|---|---|
| `output/dashboard/kpi_seller.csv` | seller × período e seller consolidado (coluna `granularidade` diferencia) |
| `output/dashboard/top_50_sellers_atraso.csv` | top 50 consolidado + top 50 de cada período (coluna `rank`) |
| `output/dashboard/ranking_semanal_sellers_atraso.csv` | semana × seller (top 50 por semana, `rank_semana`) |
| `output/dashboard/kpi_uf_seller_postagem.csv` | período × UF do seller |
| `output/figuras/05_concentracao_atrasos_sellers.png` | curva de concentração |

## Limitações
- O dataset tem uma data de postagem **por pedido**. Em pedidos com vários sellers, todos recebem a mesma data.
- Os rankings são **diagnóstico histórico** (2017–2018), não alertas atuais.
