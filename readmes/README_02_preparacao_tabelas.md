# 02 — Preparação: filtros, variáveis derivadas e tabelas analíticas

**Notebook:** [`notebooks/02_preparacao_tabelas.ipynb`](../notebooks/02_preparacao_tabelas.ipynb)

## Objetivo
Aplicar o recorte da proposta, derivar as variáveis da hipótese e gerar as tabelas analíticas com granularidade explícita. É a base de todos os notebooks seguintes.

## Premissa temporal (proxy acadêmica)
| Rótulo | Dados originais usados |
|---|---|
| `2024 (proxy jan-ago/2017)` | compras de jan a ago/2017 |
| `2025 (proxy jan-ago/2018)` | compras de jan a ago/2018 |

As datas originais **não são alteradas**. Cada linha guarda `ano_original`, `periodo_comparativo` e `mes`. O dataset não contém vendas reais de 2024/2025.

## Tratamentos aplicados
| Tratamento | Regra | Justificativa |
|---|---|---|
| Filtro de status | `order_status == "delivered"` | Os KPIs da proposta são sobre pedidos entregues |
| Filtro de período | ano da compra ∈ {2017, 2018} e mês 1–8 | Comparação equivalente jan–ago |
| Avaliação por pedido | a mais recente por `review_creation_date`; desempate por `review_answer_timestamp` e depois `review_id` | Regra da proposta, de forma determinística |
| Sem avaliação | `tem_avaliacao = False`, sem imputar nota | Fica fora do denominador do KPI1 |
| Região | mapa explícito das 27 UFs (`olist_utils.UF_REGIAO`) | Rastreável e validado |
| Categoria | tradução em `categoria_en`; nome original se não houver tradução; `sem_categoria` se ausente | Nada é escondido |
| Prazo de postagem do pedido | **menor** `shipping_limit_date` entre os itens | Regra da proposta para o KPI3 |
| Postagem no prazo | `order_delivered_carrier_date <= prazo` (no limite = no prazo) | Fronteira explícita |
| Elegibilidade KPI3 | ter data de postagem **e** prazo | Não se avalia pontualidade sem data |
| Entrega atrasada | dia da entrega > dia estimado | A data estimada não tem hora; entregar no dia estimado conta como no prazo |
| Dias de atraso | dia entregue − dia estimado (positivo = atraso) | Convenção de sinal documentada |
| Intervalos do ciclo | só quando as duas datas existem | Sem datas imputadas |
| Joins | `validate="one_to_one"` / `"many_to_one"` + asserts de contagem | Impede multiplicar pedidos e frete |

## Resultado do recorte
| | Calculado | Referência da proposta |
|---|---:|---:|
| Pedidos jan–ago/2017 | 21.998 | 21.998 |
| Pedidos jan–ago/2018 | 52.783 | 52.783 |
| Total | 74.781 | 74.781 |

Descartes: 2.963 pedidos com status diferente de `delivered`; 21.697 `delivered` fora do período.
No recorte: 391 pedidos com mais de uma avaliação (mantida a mais recente), 476 sem avaliação, 1 sem data de postagem (fora do KPI3), 7 sem data de entrega (fora da métrica de atraso), 165 com postagem antes da compra (mantidos e sinalizados), 1.139 itens sem categoria, 22 itens com categoria sem tradução.

## Saídas (`data_processed/`, formato pickle)
| Tabela | Granularidade | Linhas | Uso |
|---|---|---:|---|
| `pedidos.pkl` | 1 por `order_id` | 74.781 | KPI1, KPI3, atraso de entrega |
| `itens.pkl` | 1 por `order_id + order_item_id` | 85.267 | KPI2, categoria |
| `pedido_seller.pkl` | 1 por `order_id + seller_id` | 75.845 | Rankings de sellers (**não** somar como pedidos únicos) |
| `pedido_categoria.pkl` | 1 por `order_id + categoria` | — | KPIs por categoria (pedido conta em cada categoria que contém) |
| `qualidade_02.pkl` | 1 por verificação/descarte | — | Consolidado em `qualidade_dados.csv` |

## Limitações
- O dataset tem **uma** data de postagem por pedido. Em pedidos com vários sellers, ela é atribuída a todos.
- Pickle foi usado porque `pyarrow` (parquet) não está instalado. Os arquivos são intermediários; as saídas finais são CSV.
