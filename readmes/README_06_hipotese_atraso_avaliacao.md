# 06 — Hipótese: atrasos × avaliação ruim (com o frete junto)

**Notebook:** [`notebooks/06_hipotese_atraso_avaliacao.ipynb`](../notebooks/06_hipotese_atraso_avaliacao.ipynb)

## Objetivo
Testar se a avaliação ruim está associada a atrasos e separar as duas origens possíveis: **seller** (postagem atrasada) e **logística** (entrega lenta por região). Tudo aqui é **associação**, não causalidade.

## Análises
1. % avaliação ruim: entrega atrasada × no prazo.
2. % avaliação ruim: postagem atrasada × no prazo.
3. % entrega atrasada segundo a situação da postagem.
4. Cruzamento 2×2 postagem × entrega.
5. Decomposição descritiva: qual seria o KPI1 **se** os atrasados tivessem a taxa dos pedidos no prazo (é um teto otimista, não uma previsão).
6. Por região: entrega atrasada **mesmo com postagem no prazo** e tempo postagem→entrega.
7. Frete por situação de entrega e por região.

Teste qui-quadrado em cada comparação, para indicar se a diferença é maior do que o acaso explicaria. Ele **não** prova causa.

## Resultados (proxy 2025; proxy 2024 entre parênteses)
| Comparação | Grupo A | Grupo B | Diferença |
|---|---:|---:|---:|
| Aval. ruim: entrega atrasada × no prazo | 62,9% (57,7%) | 9,3% (8,9%) | +53,7 p.p. (6,8×) |
| Aval. ruim: postagem atrasada × no prazo | 24,6% (19,1%) | 12,3% (9,8%) | +12,2 p.p. (2,0×) |
| Entrega atrasada: postagem atrasada × no prazo | 22,4% (12,3%) | 6,4% (2,7%) | +16,0 p.p. |

Cruzamento 2×2 (proxy 2025, % avaliação ruim):

| | Entrega no prazo | Entrega atrasada |
|---|---:|---:|
| Postagem no prazo | 8,96% (44.988) | 62,80% (3.005) |
| Postagem atrasada | 13,53% (3.480) | 63,40% (989) |

- **75% das entregas atrasadas tiveram postagem no prazo** (3.005 de 3.994 avaliadas).
- Se a entrega atrasada tivesse a taxa de avaliação ruim do "no prazo", o KPI1 2025 iria de 13,37% para **9,29%** (−4,09 p.p.). O mesmo exercício para a postagem do seller leva a 12,33% (−1,04 p.p.).
- Entrega atrasada mesmo com postagem no prazo: Nordeste 13,3%, Norte 11,4%, Sudeste 5,5%, Sul 5,7%. Mediana postagem→entrega: Norte 18,0 dias, Nordeste 13,9, Sudeste 5,4.
- Frete sobre produto (2025): 17,23% nos atrasados × 17,08% nos no prazo. Pagar mais frete não aparece associado a chegar no prazo.

## Conclusão
- **Evidência:** a entrega atrasada é o fator mais associado à avaliação ruim. A postagem atrasada pesa menos e em parte *através* da entrega atrasada.
- **Interpretação:** a hipótese recebe **apoio parcial**. Os dados apontam para uma combinação, com peso maior no lado **logístico/regional**.
- **Limite:** não há identificação da transportadora no dataset, e não foi feito controle multivariado (categoria, distância, seller, mês).

## Saídas
| Arquivo | Granularidade |
|---|---|
| `output/dashboard/relacao_atraso_avaliacao.csv` | período × situação de postagem × situação de entrega (com linhas `todos`) |
| `output/dashboard/testes_associacao.csv` | período × comparação × grupo (numerador, denominador, %, qui², p-valor) |
| `output/dashboard/origem_atraso_regiao.csv` | período × região do cliente |
| `output/figuras/06_cruzamento_postagem_entrega.png` | gráfico do 2×2 |
