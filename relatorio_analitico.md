# Relatório analítico — Olist Store | CP5 FIAP

> Gerado automaticamente pelo notebook `07_validacoes_exportacao.ipynb` a partir das tabelas calculadas. Nenhum número foi digitado à mão.

> **Premissa temporal (proxy acadêmica):** “2024” = pedidos com compra em **jan–ago/2017** e “2025” = **jan–ago/2018** no dataset original. O dataset **não** contém vendas reais de 2024/2025; os rótulos servem só para a comparação equivalente pedida na proposta. As datas originais não foram alteradas.

## 1. Resumo executivo
- **A avaliação ruim subiu** de 10,59% para 13,37% (+2,78 p.p.), enquanto a **entrega atrasada ao cliente** passou de 3,50% para 7,73%. A **postagem no prazo** pelos sellers ficou praticamente estável (91,39% → 91,45%).
- **A hipótese recebe apoio parcial.** O atraso na entrega está fortemente associado à avaliação ruim (62,9% de notas 1–2 com entrega atrasada vs 9,3% no prazo, proxy 2025). A postagem atrasada pelo seller também está associada, mas com intensidade bem menor (24,6% vs 12,3%).
- **O atraso é mais logístico que de seller:** 75,2% dos pedidos avaliados com entrega atrasada (proxy 2025) tiveram a **postagem no prazo**. Norte e Nordeste têm a maior taxa de entrega atrasada mesmo quando o seller posta no prazo, além do frete proporcional mais alto.
- **Tamanho da oportunidade (descritivo, não causal):** se os pedidos atrasados tivessem a mesma taxa de avaliação ruim dos pedidos no prazo, o KPI1 da proxy 2025 seria 9,29% (−4,09 p.p.), abaixo da meta de 10%. O mesmo exercício com a postagem do seller levaria a 12,33% (−1,04 p.p.).
- **Frete:** o KPI2 da proxy 2025 está em 17,09%, praticamente no limite de 17,1%. Não há folga para resolver o atraso pagando frete mais caro de forma generalizada.
- **Recomendação:** priorizar a **logística regional** (Nordeste/Norte e RJ) com SLA de prazo da transportadora e revisão do prazo estimado, e manter um programa **focado** nos sellers reincidentes (os 50 sellers com mais postagens atrasadas concentram 39,9% dos atrasos de postagem).

## 2. Contexto e decisão
A Olist Store precisa decidir onde concentrar esforços para reduzir a insatisfação: **cobrar o prazo de postagem dos sellers** ou **renegociar/trocar transportadoras por região**. Meta: reduzir pedidos com avaliação 1–2 para **10% até dez/2027** (passo de **12% em 2026**), sem que o frete sobre o valor dos produtos passe de **17,1%**. Público: Diretor de Operações do Marketplace, Gestão de Sellers e Logística.

## 3. Fonte e recorte
- *Brazilian E-Commerce Public Dataset by Olist* (Kaggle), 8 tabelas relacionais usadas + `geolocation` (inventariada, não usada nos KPIs).
- Filtro: `order_status = delivered` e mês da compra entre janeiro e agosto de 2017 e 2018.
- Pedidos no recorte: **21.998** (2017) e **52.783** (2018), total **74.781**. Os totais coincidem com a referência da proposta (21.998 / 52.783 / 74.781).

## 4. Definições dos KPIs
| KPI | Fórmula | Regras |
|---|---|---|
| KPI1 | pedidos entregues com nota 1–2 / pedidos entregues com avaliação válida × 100 | avaliação mais recente por `review_creation_date` (desempate: `review_answer_timestamp`, depois `review_id`); pedidos sem avaliação fora do denominador |
| KPI2 | Σ `freight_value` / Σ `price` dos itens dos pedidos entregues × 100 | somado no nível item; joins N:1 validados para não multiplicar frete |
| KPI3 | pedidos postados até o prazo / pedidos elegíveis × 100 | prazo = **menor** `shipping_limit_date` entre os itens; postagem exatamente no limite = no prazo; elegível = tem data de postagem e prazo |

Derivadas: entrega atrasada = dia de `order_delivered_customer_date` > dia de `order_estimated_delivery_date` (a data estimada não tem hora); região do cliente por mapa explícito das 27 UFs.

## 5. Qualidade e tratamento dos dados
- 547 pedidos da base têm mais de uma avaliação (391 no recorte): usada a mais recente.
- Pedidos do recorte sem avaliação: 476 (0,64%), fora do denominador do KPI1.
- Excluídos do KPI3 por falta de data de postagem: 1; sem prazo limite: 0.
- Excluídos da métrica de entrega atrasada por falta de data de entrega: 7.
- Itens sem categoria: 1.139 (mantidos como `sem_categoria`); itens com categoria sem tradução: 22 (nome original mantido).
- 165 pedidos têm data de postagem anterior à compra (inconsistência da base). Foram mantidos e sinalizados; não alteram a classificação “no prazo”.
- Itens com frete zero (380) são válidos (frete grátis) e foram mantidos. Não houve preço/frete negativo nem nota fora de 1–5.
- Nenhuma data, nota ou valor monetário foi imputado.

## 6. Resultados

### 6.1 KPIs por período (calculado × proposta)
| KPI | 2024 calculado | 2024 proposta | 2025 calculado | 2025 proposta | Meta 2026 | Meta 2027 |
|---|---:|---:|---:|---:|---:|---:|
| KPI1 — % avaliação ruim (1–2) | 10,59 | 10,6 | 13,37 | 13,4 | 12,0 | 10,0 |
| KPI2 — % frete / valor dos produtos | 16,02 | 16,0 | 17,09 | 17,1 | 17,1 | 17,1 |
| KPI3 — % postagem no prazo | 91,39 | 91,4 | 91,45 | 91,5 | 95,0 | 97,0 |

Os valores calculados coincidem com os da proposta quando arredondados a uma casa decimal. Isso confirma que as definições são as mesmas.

### 6.2 Evolução mensal (proxy 2025)
A piora da proxy 2025 está concentrada em **fevereiro e março/2018**: avaliação ruim de 19,4% e 21,2%, com entrega atrasada de 14,1% e 19,0%. De abril a agosto a avaliação ruim ficou entre 9,5% e 11,8%. A postagem no prazo nesses dois meses foi de 87,8% e 91,5%, sem queda equivalente. Ver `output/figuras/03_kpis_mensais.png`.

### 6.3 Atraso × avaliação ruim (proxy 2025)
| Postagem | Entrega | Pedidos avaliados | % avaliação ruim |
|---|---|---:|---:|
| postagem no prazo | entrega no prazo | 44.988 | 8,96 |
| postagem no prazo | entrega atrasada | 3.005 | 62,80 |
| postagem atrasada | entrega no prazo | 3.480 | 13,53 |
| postagem atrasada | entrega atrasada | 989 | 63,40 |

- Entrega atrasada vs no prazo: **62,9% vs 9,3%** (+53,7 p.p.; na proxy 2024: 57,7% vs 8,9%).
- Postagem atrasada vs no prazo: **24,6% vs 12,3%** (+12,2 p.p.).
- Postagem atrasada eleva a chance de entrega atrasada: 22,4% vs 6,4%.
- Com a entrega no prazo, a postagem atrasada eleva pouco a avaliação ruim (13,5% vs 9,0%). Com a entrega atrasada, a taxa é alta nos dois casos.
- Todos os testes qui-quadrado deram p < 0,001. Eles indicam associação, **não** causalidade.

### 6.4 Regiões
| Região (2025 proxy) | Pedidos | % aval. ruim | % entrega atrasada | % frete/produto | ref. frete proposta | % postagem no prazo |
|---|---:|---:|---:|---:|---:|---:|
| Norte | 866 | 17,56 | 12,36 | 23,85 | 23,9 | 92,96 |
| Nordeste | 4.669 | 17,45 | 14,44 | 22,68 | 22,7 | 91,20 |
| Centro-Oeste | 3.113 | 13,40 | 7,93 | 18,83 | — | 92,03 |
| Sudeste | 36.803 | 12,96 | 6,95 | 15,52 | 15,5 | 91,26 |
| Sul | 7.332 | 12,36 | 6,71 | 18,30 | — | 92,13 |

| Região (2025 proxy) | % postagem atrasada | % entrega atrasada c/ postagem no prazo | mediana dias postagem→entrega |
|---|---:|---:|---:|
| Norte | 7,04 | 11,43 | 18,0 |
| Nordeste | 8,80 | 13,32 | 13,9 |
| Centro-Oeste | 7,97 | 6,60 | 9,9 |
| Sudeste | 8,73 | 5,46 | 5,4 |
| Sul | 7,87 | 5,70 | 8,2 |

O frete por região na proxy 2025 coincide com as referências da proposta (Norte 23,9%, Nordeste 22,7%, Sudeste 15,5%). No Norte e no Nordeste a entrega atrasa mais mesmo com a postagem no prazo, e o trecho postagem→entrega é mais longo. A taxa de postagem atrasada, por sua vez, é parecida entre as regiões.

### 6.5 UFs com mais pedidos ruins acima da taxa média (proxy 2025)
| UF | Região | Pedidos avaliados | % aval. ruim | % entrega atrasada | % frete | pedidos ruins acima da média |
|---|---:|---:|---:|---:|---:|---:|
| RJ | Sudeste | 6.279 | 20,18 | 13,73 | 18,11 | 427 |
| BA | Nordeste | 1.713 | 17,69 | 14,08 | 20,89 | 74 |
| CE | Nordeste | 629 | 20,35 | 19,12 | 22,83 | 44 |
| PA | Norte | 442 | 20,81 | 16,56 | 22,70 | 33 |
| MA | Nordeste | 344 | 20,35 | 19,94 | 27,76 | 24 |

### 6.6 Categorias com mais pedidos ruins acima da taxa média (proxy 2025, ≥ 30 avaliações)
| Categoria | Pedidos avaliados | % aval. ruim | % postagem no prazo | % entrega atrasada | % frete | pedidos ruins acima da média |
|---|---:|---:|---:|---:|---:|---:|
| bed_bath_table | 4.799 | 16,55 | 93,52 | 8,18 | 20,91 | 152 |
| computers_accessories | 3.956 | 15,87 | 89,25 | 7,66 | 17,68 | 99 |
| office_furniture | 631 | 22,82 | 73,27 | 7,55 | 26,55 | 60 |
| furniture_decor | 3.130 | 15,21 | 90,31 | 7,50 | 23,16 | 57 |
| watches_gifts | 3.392 | 14,92 | 91,72 | 8,52 | 9,00 | 52 |
| telephony | 2.103 | 15,50 | 91,21 | 8,60 | 20,94 | 45 |

Categorias com menor postagem no prazo (≥ 200 pedidos): office_furniture (73,3%), home_construction (79,6%), sem_categoria (88,1%), furniture_living_room (88,6%), pet_shop (89,0%).

### 6.7 Sellers
- Os 10, 50 e 100 sellers com mais postagens atrasadas concentram 16,9%, 39,9% e 53,2% das postagens atrasadas. Eles respondem por 8,1%, 23,9% e 31,2% do volume pedido–seller.
- O seller nº 1 do ranking tem 221 postagens atrasadas em 793 (27,9%). Ver `top_50_sellers_atraso.csv` e `ranking_semanal_sellers_atraso.csv`.
- Os rankings são **diagnóstico retrospectivo** (2017–2018), não alertas atuais. As contagens são na granularidade pedido–seller e não somam pedidos únicos.

## 7. Conclusão: evidência, interpretação e recomendação
**Evidência observada**
1. Entrega atrasada ao cliente está associada a uma taxa de avaliação ruim ~6,8× maior.
2. 75,2% das entregas atrasadas avaliadas (proxy 2025) tiveram postagem no prazo.
3. A postagem no prazo ficou estável entre os períodos, enquanto a entrega atrasada e a avaliação ruim cresceram, com pico em fev–mar/2018.
4. Norte/Nordeste combinam entrega mais lenta, mais atraso mesmo com a postagem no prazo e o frete proporcional mais alto. Pelo volume, o RJ é a UF com mais pedidos ruins acima da média.

**Interpretação**
- A hipótese recebe **apoio parcial**: o atraso na entrega é o fator mais associado à insatisfação, e a maior parte desse atraso **não** vem de postagem atrasada pelo seller. Os dados apontam para uma **combinação**, com peso maior no lado **logístico/regional**. A gestão de sellers é uma alavanca secundária, mas concentrada em poucos sellers.
- Não é possível separar com estes dados o efeito da transportadora, da distância e de uma promessa de prazo otimista: o dataset não identifica a transportadora.

**Recomendações priorizadas**
| # | Ação | Área | KPI de acompanhamento |
|---|---|---|---|
| 1 | SLA e renegociação com transportadoras nas rotas para Nordeste, Norte e RJ; revisão do prazo estimado nessas rotas | Logística | % entrega atrasada por região; KPI1 por região |
| 2 | Plano de capacidade para picos (o pico de fev–mar/2018 sugere gargalo sazonal) | Logística/Operações | % entrega atrasada mensal; KPI1 mensal |
| 3 | Programa de pontualidade para os sellers reincidentes (top 50 e ranking semanal), com alerta e penalidade progressiva | Gestão de Sellers | KPI3 (meta 95% em 2026 e 97% em 2027); % postagem atrasada do top 50 |
| 4 | Ações por categoria com postagem baixa (ex.: móveis de escritório) | Gestão de Sellers | KPI3 e KPI1 por categoria |
| 5 | Guarda-corpo de custo: toda mudança de transportadora deve ser avaliada pelo KPI2 geral (≤ 17,1%) e regional | Logística/Financeiro | KPI2 geral e por região |

**Como não mascarar a melhora com frete mais caro:** acompanhar o KPI1 e o KPI2 sempre lado a lado. Como o KPI2 já está em 17,09%, qualquer aumento de frete no Norte/Nordeste precisa ser compensado por ganho de eficiência em outras rotas. Na proxy 2025, os itens de pedidos entregues no prazo tiveram frete de 17,08% sobre o produto, contra 17,23% nos atrasados. Ou seja, pagar mais frete, por si só, não garante entrega no prazo.

## 8. Limitações e próximos passos
- Proxy temporal: 2017/2018 representam 2024/2025 apenas para fins acadêmicos.
- O dataset não informa a transportadora nem a data de postagem por seller: em pedidos com vários sellers, a data de postagem do pedido é atribuída a todos.
- Associação não é causalidade. Os próximos passos seriam um modelo multivariado (ex.: regressão logística com região, categoria, seller e mês) e testes A/B das ações.
- Grupos com menos de 30 avaliações estão sinalizados (`amostra_pequena`) e devem ser lidos com cautela.

## 9. Reprodução
Ver `README.md` na raiz. Saídas em `output/dashboard/` (CSVs) e `output/figuras/` (PNGs).
