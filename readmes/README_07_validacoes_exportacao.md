# 07 — Validações, dicionário de dados e relatório

**Notebook:** [`notebooks/07_validacoes_exportacao.ipynb`](../notebooks/07_validacoes_exportacao.ipynb)

## Objetivo
Fechar a pipeline garantindo as regras críticas da seção 9 da proposta. Cada verificação é um `assert`: se uma regra for violada, o notebook **falha** em vez de deixar passar dados errados. Depois disso, gera a documentação das saídas e o relatório.

## Validações executadas (111, todas OK na última execução)
| Grupo | O que é verificado |
|---|---|
| Granularidade | `pedidos` 1 linha/pedido; `itens` 1 linha/item; `pedido_seller` 1 linha/pedido+seller e identificada como tal |
| Joins | nº de itens e somas de frete/preço idênticos aos dados originais; frete igual nas tabelas pedido, item e pedido–seller |
| Filtros | só `delivered`; ano e mês corretos; datas originais não alteradas; rótulo de período coerente |
| Avaliação | a escolhida é a mais recente (recálculo independente); notas 1–5; ruim = nota 1 ou 2; sem imputação |
| Postagem | KPI3 usa o menor `shipping_limit_date`; postagem no limite = no prazo; não elegíveis sem classificação; idem no pedido–seller |
| UF → região | todas as UFs mapeadas; 27 UFs e 5 regiões |
| CSVs | releitura sem erro de todos os CSVs; numerador ≤ denominador; percentuais entre 0 e 100 |
| Consistência | KPI1 e KPI2 recalculados de forma independente; soma mensal e regional = total do período |

**Exceção documentada:** o KPI2 (frete/preço) é uma razão e pode passar de 100% em grupos pequenos (ex.: seller que vende itens baratos com frete caro). Para ele a regra é ≥ 0, e a quantidade de grupos acima de 100% fica registrada.

A comparação com os totais da proposta (21.998 / 52.783) também é registrada, sem forçar: a diferença deu 0.

## Saídas
| Arquivo | Conteúdo |
|---|---|
| `output/dashboard/qualidade_dados.csv` | inventário (01) + descartes (02) + validações (07); colunas `etapa`, `tabela`, `verificacao`, `valor`, `detalhe` |
| `output/dashboard/dicionario_dados.csv` | 1 linha por arquivo × coluna: tipo, granularidade e descrição |
| `relatorio_analitico.md` | relatório executivo e analítico, gerado com f-strings a partir das tabelas calculadas (nenhum número digitado à mão) |

## Testes unitários complementares
`tests/test_regras.py` testa as regras de `olist_utils.py` com dados sintéticos (avaliação mais recente e desempate, percentual seguro, frete somado no nível item, numeradores/denominadores, mapa de UFs, fronteira do prazo). Para rodar: `python tests/test_regras.py`.
