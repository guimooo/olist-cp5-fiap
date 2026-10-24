# 03 — KPIs oficiais por período e por mês

**Notebook:** [`notebooks/03_kpis_gerais.ipynb`](../notebooks/03_kpis_gerais.ipynb)

## Objetivo
Calcular os três KPIs da proposta, guardando numeradores e denominadores, e comparar com as referências e metas (que ficam em colunas separadas dos valores calculados).

## Fórmulas
| KPI | Fórmula | Tabela-base |
|---|---|---|
| KPI1 | pedidos com nota 1–2 / pedidos com avaliação válida × 100 | `pedidos` |
| KPI2 | Σ `freight_value` / Σ `price` × 100 | `itens` |
| KPI3 | pedidos postados até o menor `shipping_limit_date` / pedidos elegíveis × 100 | `pedidos` |

As funções estão em `olist_utils.kpi_pedidos` e `olist_utils.kpi_frete`, reutilizadas em todos os notebooks.

## Resultados
| KPI | 2024 (proxy 2017) | Proposta | 2025 (proxy 2018) | Proposta | Meta 2026 | Meta 2027 |
|---|---:|---:|---:|---:|---:|---:|
| KPI1 % avaliação ruim | 10,59 (2.312 / 21.837) | 10,6 | 13,37 (7.016 / 52.468) | 13,4 | 12 | 10 |
| KPI2 % frete/produto | 16,02 (R$ 479 mil / R$ 2,99 mi) | 16,0 | 17,09 (R$ 1,23 mi / R$ 7,22 mi) | 17,1 | ≤ 17,1 | ≤ 17,1 |
| KPI3 % postagem no prazo | 91,39 (20.103 / 21.997) | 91,4 | 91,45 (48.271 / 52.783) | 91,5 | 95 | 97 |
| % entrega atrasada (apoio) | 3,50 | — | 7,73 | — | — | — |

Os três KPIs coincidem com a proposta quando arredondados a uma casa decimal.

Outros achados:
- **Pico de fev–mar/2018:** avaliação ruim de 19,4% e 21,2%, e entrega atrasada de 14,1% e 19,0%. De abril a agosto/2018 a avaliação ruim volta a ficar entre 9,5% e 11,8%.
- Notas 1 subiram de 7,6% para 10,4% dos pedidos avaliados; notas 2 ficaram estáveis (~3%).
- Pedidos sem avaliação: 0,73% (2017) e 0,60% (2018).
- Entre os atrasados, a mediana do atraso é de 7 dias nos dois períodos.
- Ciclo mediano compra→entrega: 10,4 dias (2017) e 9,5 dias (2018). Há 1.331 intervalos aprovação→postagem negativos (inconsistência da base, não corrigida).

## Saídas
| Arquivo | Granularidade |
|---|---|
| `output/dashboard/kpi_resumo_periodo.csv` | 1 linha por período: KPIs, numeradores, denominadores, referências, metas e diferença em p.p. |
| `output/dashboard/kpi_mensal.csv` | 1 linha por período × mês |
| `output/dashboard/distribuicao_notas.csv` | 1 linha por período × nota |
| `output/figuras/03_kpis_mensais.png`, `03_distribuicao_notas.png`, `03_dias_atraso_entrega.png` | Gráficos exploratórios |

## Limitações
A nota média aparece só como contexto. O indicador oficial é a proporção de notas 1–2.
