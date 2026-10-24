# Olist CP5: dashboard Power BI, ficha técnica e one-page executivo (parte 2)

**Autores:** Guilherme Moraes de Sousa (RM563530) · Júlia Ferreira França (RM563445)

Segunda parte do CP5. A partir das saídas da E1 (`output/dashboard/` e `data_processed/`), o projeto entrega um relatório
Power BI de uma página (dashboard executivo), a ficha técnica do dashboard em PDF e um PDF executivo de uma página. Nenhum resultado foi recalculado
do zero: o modelo lê as tabelas da E1, e os KPIs no Power BI batem com a E1 em todas as casas (ver `AUDITORIA_DAX.md`).

> **Premissa temporal.** “2024” = pedidos com compra em jan–ago/**2017** e “2025” = jan–ago/**2018** (proxy acadêmica).
> Não são dados reais de 2024/2025 e **não existe dado observado de 2026**: os marcos de 2026 são planejamento.

## Entregáveis

| Arquivo | O que é |
|---|---|
| `olist_cp5.pbix` | Relatório final (5,7 MB, dados embutidos), com **uma página**: o Dashboard executivo |
| `olist_cp5_ficha_tecnica.pdf` | Ficha técnica do dashboard (3 páginas, A4 horizontal): KPIs recalculados × proposta, registro dos visuais (por que cada gráfico e o que foi retirado dele), captura do painel, contrato DAX e modelo |
| `olist_cp5_one_page.pdf` | One-page executivo, A4 horizontal, **1 página** (`olist_cp5_one_page.png` = prévia) |
| `AUDITORIA_DAX.md` | Matriz do contrato DAX (F1–F6) com o teste de cada função e o catálogo das 55 medidas |
| `validacao_dax_resultado.txt` | Saída das 13 consultas de validação executadas contra o `.pbix` (0 erros) |
| `preview_dashboard.png` | Captura do dashboard aberto no Power BI Desktop (usada na ficha técnica) |
| `powerbi/olist_cp5.pbip` | Fonte editável do mesmo relatório (modelo TMDL + relatório PBIR), útil para versionar |
| `powerbi/dados/*.csv` | Tabelas do modelo exportadas da E1 |
| `scripts/` | Pipeline que gera tudo (abaixo) |

## Como abrir

- **Só visualizar:** abra `olist_cp5.pbix` no Power BI Desktop. Os dados já estão no arquivo, e não é preciso atualizar.
- **Atualizar a partir dos CSVs:** em *Transformar dados > Editar parâmetros*, ajuste `PastaDados` para a pasta
  `entregaveis\powerbi\dados\` da sua máquina (com a barra no final) e clique em *Atualizar*.

## Como reproduzir (na raiz do projeto)

```bash
python entregaveis/scripts/01_preparar_dados_powerbi.py   # exporta as tabelas do modelo a partir de data_processed/ (E1)
python entregaveis/scripts/02_gerar_pbip.py               # gera o projeto powerbi/olist_cp5.pbip (TMDL + PBIR)
python entregaveis/scripts/03_gerar_one_page.py           # gera o PDF de 1 página e a prévia PNG
python entregaveis/scripts/04_documentar_medidas.py       # gera AUDITORIA_DAX.md a partir das medidas do modelo
python entregaveis/scripts/05_gerar_ficha_tecnica_pdf.py  # gera a ficha técnica em PDF (textos em scripts/conteudo_ficha.py)
```

Depois: abra `powerbi/olist_cp5.pbip` no Power BI Desktop, clique em *Atualizar agora* e use *Arquivo > Salvar como >
Arquivo do Power BI (\*.pbix)*. Para revalidar as medidas com o relatório aberto:

```powershell
powershell -File entregaveis/scripts/executar_dax.ps1 -Arquivo entregaveis/scripts/validacao_dax.dax -Saida entregaveis/validacao_dax_resultado.txt
```

O script `03_gerar_one_page.py` confere 12 números contra os valores validados no Power BI e falha se algum divergir.
Também verifica que o PDF tem exatamente uma página.

## Modelo de dados

```
Calendário (Data, marcada como tabela de datas) ─┐
Local Cliente (UF → Região) ─────────────────────┼──< Pedidos        1 linha por pedido entregue      → KPI01, KPI03, entrega atrasada
                                                 ├──< Itens          1 linha por item                  → KPI02 (Σ frete ÷ Σ preço)
Sellers ─────────────────────────────────────────┴──< Pedido Seller  1 linha por par pedido × seller   → ranking de sellers
Medidas (só medidas)
```

Relacionamentos muitos-para-um, filtro em direção única e sem relação fato-fato. Regras herdadas da E1: só `delivered`
com compra em jan–ago; avaliação mais recente por pedido; frete somado no nível item; postagem comparada ao **menor**
`shipping_limit_date` do pedido (postar exatamente no limite = no prazo).

## O dashboard (página única)

Filtros: **Período comparável** (padrão: 2025 proxy, seleção única) e **Região do cliente**. Os três KPIs da E1 são os
únicos cartões de destaque, cada um com valor, status em texto (✔ / ● / ✖ + cor), variação vs ano anterior, referência da
proposta e marcos.

| ID | Visual | Papel | Leitura principal (2025 proxy) |
|---|---|---|---|
| C1–C3 | Cartões KPI01 / KPI02 / KPI03 | alvo, restrição, alavanca | 13,4% (acima do marco de 12%) · 17,09% (folga de 0,01 p.p.) · 91,5% (faltam 3,5 p.p. para 95%) |
| G1 | Linha mensal: avaliação ruim × entrega atrasada | alvo | Pico em fev–mar/2018 (19,4% e 21,2%) junto com 14,1% e 19,0% de entrega atrasada; abr–ago = 10,4% |
| G2 | Barras por UF: pedidos ruins acima da média | alvo | RJ ~427, BA ~74, CE ~44, PA ~33, MA ~24 |
| G3 | Colunas por região + linha do limite (eixo único 0–30%) | restrição | Só o Sudeste (15,5%) fica abaixo de 17,1%; Norte 23,9%, Nordeste 22,7% |
| G4 | Colunas: % avaliação ruim por postagem × entrega | alavanca | Entrega atrasada ≈ 63% com ou sem postagem atrasada; postagem atrasada + entrega no prazo = 13,5% (vs 9,0%) |
| G5 | Tabela ranqueada (RANKX) de sellers, mín. 30 pares | alavanca | Top 10 = 19,8% das postagens atrasadas, com 8,7% do volume |

O rodapé do painel identifica os autores. A **ficha técnica** fica fora do `.pbix`, em `olist_cp5_ficha_tecnica.pdf`:
tabela atualizada dos KPIs (fórmula, valores 2024 e 2025, numerador ÷ denominador, referência da proposta, diferença em
p.p., marco 2026, meta 2027, status e limitações), uma linha por visual acima (pergunta, por que o gráfico, evidência,
decisão), o contrato DAX e o modelo de dados.

## KPIs finais

| Papel | KPI | 2024 (proxy 2017) | 2025 (proxy 2018) | Proposta E1 (2024 → 2025) | Marco 2026 | Meta 2027 |
|---|---|---:|---:|---:|---:|---:|
| Alvo | % pedidos com avaliação ruim (1–2) | 10,59% | 13,37% (7.016 ÷ 52.468) | 10,6% → 13,4% | 12% | 10% até dez/2027 |
| Restrição | Frete ÷ valor dos produtos | 16,02% | 17,09% (R$ 1,23 mi ÷ R$ 7,22 mi) | 16,0% → 17,1% | ≤ 17,1% | ≤ 17,1% |
| Alavanca | % pedidos postados no prazo | 91,39% | 91,45% (48.271 ÷ 52.783) | 91,4% → 91,5% | 95% | 97% |

As diferenças entre o valor recalculado e a proposta são de −0,03, −0,01 e −0,05 p.p. (só arredondamento).

## Limitações

- Proxy temporal 2017/2018 → 2024/2025. Não há realização de 2026, então a suficiência do plano é avaliada de forma condicional.
- A base não identifica a transportadora nem a data de postagem por seller: em pedidos com vários sellers, a data de postagem do pedido vale para todos.
- Os títulos-conclusão do dashboard descrevem o recorte padrão (2025 proxy, todas as regiões). Com outros filtros, os números dos visuais mudam, mas os títulos continuam fixos.
- `KPI01 Acumulado no Ano` (TOTALYTD) repete o valor de agosto de set a dez, porque esses meses não têm vendas no recorte. Ele só aparece no tooltip do G1 (jan–ago).
- Associação não prova causalidade; os próximos passos são um modelo multivariado e testes A/B (ver `relatorio_analitico.md`).
- O `.pbix` foi gerado no Power BI Desktop 2.159 (Microsoft Store). Versões antigas do Desktop podem não abrir o formato de relatório PBIR.
