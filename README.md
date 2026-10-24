# Olist Store — Ciência de Dados | CP5 FIAP

**Autores:** Guilherme Moraes de Sousa (RM563530) · Júlia Ferreira França (RM563445)

Análise da base pública **Brazilian E-Commerce Public Dataset by Olist** para apoiar a decisão operacional: reduzir pedidos com avaliação 1–2 (meta de 10% até dez/2027), sem que o frete passe de 17,1% do valor dos produtos, decidindo entre **gestão de prazos dos sellers** e **logística por região**. A parte 1 (E1) gera as tabelas analíticas; a parte 2, em [`entregaveis/`](entregaveis/README_POWERBI.md), traz o dashboard Power BI, a ficha técnica e o one-page executivo.

> **Premissa temporal:** “2024” = jan–ago/**2017** e “2025” = jan–ago/**2018** nos dados originais (proxy acadêmica). O dataset não contém vendas reais de 2024/2025.

## Estrutura
```
olist_*.csv, product_category_name_translation.csv   dados originais do Kaggle (não versionados; ver abaixo)
olist_utils.py                                        funções compartilhadas (leitura, regras, KPIs)
notebooks/01..07_*.ipynb                              um notebook por etapa de tratamento (já executados)
readmes/README_01..07_*.md                            um README por notebook
data_processed/                                       tabelas intermediárias (.pkl, geradas pelo pipeline; não versionadas)
output/dashboard/                                     CSVs prontos para o dashboard
output/figuras/                                       gráficos exploratórios (.png)
relatorio_analitico.md                                relatório final (gerado pelo notebook 07)
tests/test_regras.py                                  testes das regras críticas
run_pipeline.py                                       executa os 7 notebooks em ordem
entregaveis/                                          parte 2: .pbix, ficha técnica, one-page e scripts
```

## Notebooks (executar em ordem)
| # | Notebook | O que faz | README |
|---|---|---|---|
| 01 | Inventário e qualidade | Schemas, nulos, chaves, duplicatas, domínios, datas incoerentes, cardinalidade dos joins | [README_01](readmes/README_01_inventario_qualidade.md) |
| 02 | Preparação | Filtro delivered + jan–ago, avaliação mais recente, região, categoria, variáveis de atraso; tabelas pedido / item / pedido–seller / pedido–categoria | [README_02](readmes/README_02_preparacao_tabelas.md) |
| 03 | KPIs gerais | KPI1, KPI2 e KPI3 por período e mês; notas; dias de atraso | [README_03](readmes/README_03_kpis_gerais.md) |
| 04 | Região, UF e categoria | KPIs por corte, com volume e flag de amostra pequena | [README_04](readmes/README_04_cortes_regiao_categoria.md) |
| 05 | Sellers e postagem | Ranking de sellers, top 50, ranking semanal, concentração | [README_05](readmes/README_05_sellers_postagem.md) |
| 06 | Hipótese | Atraso × avaliação ruim, cruzamento 2×2, origem do atraso por região, frete | [README_06](readmes/README_06_hipotese_atraso_avaliacao.md) |
| 07 | Validações e exportação | 111 asserts, `qualidade_dados.csv`, `dicionario_dados.csv`, relatório | [README_07](readmes/README_07_validacoes_exportacao.md) |

## Como reproduzir
Ambiente usado: Python 3.11, pandas 2.3, numpy 2.3, matplotlib 3.10, seaborn 0.13, scipy 1.17, jupyter/nbconvert. 

**Dados:** a base original não está no repositório. Baixe o [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença CC BY-NC-SA 4.0) e coloque os 9 CSVs (`olist_*_dataset.csv` e `product_category_name_translation.csv`) na raiz do projeto. As saídas já calculadas estão versionadas em `output/` e o `.pbix` já tem os dados embutidos, então dá para ver os resultados sem baixar nada.

```bash
python run_pipeline.py          # executa 01 → 07 (~5 min) e regrava os notebooks com as saídas
python tests/test_regras.py     # testes unitários das regras críticas
```
Também é possível abrir os notebooks no Jupyter/VS Code e executá-los em ordem, de 01 a 07.

## Principais resultados
| KPI | 2024 (proxy 2017) | 2025 (proxy 2018) | Meta 2026 | Meta 2027 |
|---|---:|---:|---:|---:|
| % avaliação ruim (1–2) | 10,59 | 13,37 | 12 | 10 |
| % frete / valor dos produtos | 16,02 | 17,09 | ≤ 17,1 | ≤ 17,1 |
| % postagem no prazo | 91,39 | 91,45 | 95 | 97 |

- Os valores coincidem com os da proposta (com arredondamento a uma casa), e os totais de pedidos também (21.998 / 52.783).
- Entrega atrasada: 62,9% de avaliação ruim, contra 9,3% quando chega no prazo (proxy 2025). 75% das entregas atrasadas tiveram postagem no prazo. **A hipótese recebe apoio parcial, com peso maior no lado logístico/regional** (Nordeste, Norte, RJ). Os sellers são uma alavanca secundária e concentrada: o top 50 responde por 40% das postagens atrasadas.

Detalhes, recomendações e limitações estão em [relatorio_analitico.md](relatorio_analitico.md).

## CSVs para o dashboard (`output/dashboard/`)
`kpi_resumo_periodo`, `kpi_mensal`, `kpi_regiao`, `kpi_uf`, `kpi_categoria`, `kpi_seller`, `relacao_atraso_avaliacao`, `top_50_sellers_atraso`, `qualidade_dados`, `dicionario_dados`. Extras: `distribuicao_notas`, `ranking_semanal_sellers_atraso`, `kpi_uf_seller_postagem`, `testes_associacao`, `origem_atraso_regiao`.
Formato: UTF-8, separador vírgula, ponto decimal, percentuais numéricos (ex.: `13.37`). A coluna `granularidade` indica a unidade de cada linha. As colunas estão descritas em `dicionario_dados.csv`.

## Parte 2: dashboard Power BI, ficha técnica e one-page executivo
Autores: Guilherme Moraes de Sousa (RM563530) · Júlia Ferreira França (RM563445).

Os entregáveis da segunda parte estão em [`entregaveis/`](entregaveis/README_POWERBI.md): `olist_cp5.pbix` (dashboard executivo de uma página), `olist_cp5_ficha_tecnica.pdf` (ficha técnica), `olist_cp5_one_page.pdf` (one-page de 1 página), `AUDITORIA_DAX.md` (contrato DAX F1–F6 e catálogo de medidas) e `README_POWERBI.md` (como abrir, reproduzir e limitações). O modelo lê as tabelas desta etapa, sem refazer a análise.
