# 04 — KPIs por região, UF e categoria

**Notebook:** [`notebooks/04_cortes_regiao_categoria.ipynb`](../notebooks/04_cortes_regiao_categoria.ipynb)

## Objetivo
Localizar onde estão as maiores oportunidades: regiões e UFs do **cliente** e categorias de produto.

## Tratamentos
- KPI1, KPI3 e % de entrega atrasada vêm da tabela `pedidos`; o KPI2 vem da tabela `itens`.
- **Categoria:** um pedido com itens de várias categorias é contado uma vez **em cada** categoria que contém (tabela `pedido_categoria`). Por isso a soma por categoria é maior que o total de pedidos.
- Todo grupo traz o denominador e a flag `amostra_pequena` (menos de 30 avaliações). Nenhum grupo é removido.
- Para priorizar, além da taxa, usamos o **excesso de pedidos ruins**: pedidos ruins do grupo menos o que ele teria na taxa geral do período (13,37%). Isso combina taxa e volume.

## Resultados (proxy 2025)
| Região | Pedidos | % aval. ruim | % entrega atrasada | % frete | Ref. frete proposta | % postagem no prazo |
|---|---:|---:|---:|---:|---:|---:|
| Norte | 866 | 17,56 | 12,36 | 23,85 | 23,9 | 92,96 |
| Nordeste | 4.669 | 17,45 | 14,44 | 22,68 | 22,7 | 91,20 |
| Centro-Oeste | 3.113 | 13,40 | 7,93 | 18,83 | — | 92,03 |
| Sudeste | 36.803 | 12,96 | 6,95 | 15,52 | 15,5 | 91,26 |
| Sul | 7.332 | 12,36 | 6,71 | 18,30 | — | 92,13 |

- O frete por região coincide com as referências da proposta.
- A postagem no prazo é parecida em todas as regiões (91–93%). Já a entrega atrasada e a avaliação ruim são bem maiores no Norte e no Nordeste.
- **UFs com mais pedidos ruins acima da média:** RJ (+427; 20,2% ruim; 13,7% atrasada), BA (+74), CE (+44), PA (+33), MA (+24). Pelo volume, o RJ é a maior oportunidade isolada.
- **Categorias com mais pedidos ruins acima da média:** bed_bath_table (+152), computers_accessories (+99), office_furniture (+60), furniture_decor (+57), watches_gifts (+52).
- **office_furniture** tem a pior combinação: 22,8% de avaliação ruim, só 73,3% de postagem no prazo e 26,6% de frete. home_construction também tem postagem baixa (79,6%).
- 46 grupos categoria × período estão com `amostra_pequena`.

## Saídas
| Arquivo | Granularidade |
|---|---|
| `output/dashboard/kpi_regiao.csv` | período × região do cliente (inclui referência de frete da proposta) |
| `output/dashboard/kpi_uf.csv` | período × UF do cliente |
| `output/dashboard/kpi_categoria.csv` | período × categoria (pedido contado em cada categoria que contém) |
| `output/figuras/04_kpis_regiao.png`, `04_uf_atraso_vs_ruim.png` | Gráficos |

## Limitações
Diferenças entre regiões são associações. Distância, mix de categorias e sellers de origem não foram controlados ao mesmo tempo.
