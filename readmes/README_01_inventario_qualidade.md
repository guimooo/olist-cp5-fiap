# 01 — Inventário e qualidade dos dados

**Notebook:** [`notebooks/01_inventario_qualidade.ipynb`](../notebooks/01_inventario_qualidade.ipynb)

## Objetivo
Conhecer os dados antes de calcular qualquer KPI: quais arquivos e colunas existem, quantas linhas, tipos, chaves, valores ausentes, duplicatas, domínios inválidos, datas incoerentes e cardinalidade dos relacionamentos. **Nenhum dado é alterado aqui.**

## Entradas
Os 9 CSVs originais na raiz do projeto (`olist_*.csv` e `product_category_name_translation.csv`).

## Tratamentos / verificações
| Verificação | Por quê |
|---|---|
| Linhas, colunas, tipos, nulos por coluna | Saber o que existe e o que falta |
| Unicidade das chaves (`order_id`, `customer_id`, `order_id+order_item_id`…) | Garantir que os joins não multipliquem linhas |
| Duplicatas de linha inteira | Detectar registros repetidos |
| Status dos pedidos, notas fora de 1–5, preço/frete negativos ou zero | Validar domínios |
| Datas não conversíveis e sequências impossíveis (ex.: postagem antes da compra) | Medir inconsistências antes de derivar prazos |
| Integridade referencial (chave estrangeira sem correspondência) | Confirmar que os joins não perdem registros |
| Cardinalidade (itens/sellers/avaliações por pedido) | Decidir a granularidade das tabelas analíticas |
| UFs presentes × mapa de 27 UFs | Garantir que todo cliente terá região |

## Principais achados
- Base completa: 99.441 pedidos, 112.650 itens, 99.224 avaliações, 3.095 sellers, 32.951 produtos.
- `review_id` **não é único** (814 repetições), e **547 pedidos têm mais de uma avaliação** (máx. 3). Daí vem a regra da avaliação mais recente.
- Um pedido pode ter até 21 itens e 5 sellers; 1.278 pedidos têm mais de um seller. Por isso o frete é somado no nível item e o KPI3 precisa de agregação.
- 8 pedidos `delivered` sem data de entrega ao cliente e 2 sem data de postagem.
- 166 pedidos com postagem antes da compra e 23 com entrega antes da postagem (inconsistências da base, apenas registradas).
- Nenhuma nota fora de 1–5, nenhum preço/frete negativo; 383 itens com frete zero (frete grátis).
- 13 produtos com categoria sem tradução; 610 produtos sem categoria.
- Integridade referencial completa entre orders, items, customers, sellers, products e reviews.
- 27 UFs de clientes, todas cobertas pelo mapa UF → região.
- `geolocation` tem 261.831 linhas duplicadas, mas não é usada nos KPIs.

## Saídas
| Arquivo | Granularidade |
|---|---|
| `data_processed/qualidade_01.pkl` | 1 linha por verificação (consolidado depois em `qualidade_dados.csv`) |
| `data_processed/inventario_colunas.pkl` | 1 linha por tabela × coluna |

## Limitações
Este notebook só detecta problemas. Cada tratamento é decidido no notebook 02, conforme o KPI afetado.
