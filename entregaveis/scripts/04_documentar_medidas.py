"""Gera entregaveis/AUDITORIA_DAX.md: matriz do contrato DAX + catálogo de todas as medidas.

O catálogo vem da lista MEDIDAS de 02_gerar_pbip.py (a mesma que gera o TMDL do modelo), então
a documentação não diverge do .pbix. Os testes citados estão em scripts/validacao_dax.dax e o
resultado da última execução em validacao_dax_resultado.txt.

Uso (na raiz do projeto): python entregaveis/scripts/04_documentar_medidas.py
"""
import importlib.util
from pathlib import Path

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gerar_pbip", AQUI / "02_gerar_pbip.py")
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)

GRANULARIDADE = {
    "0. Metas e limites": "constante",
    "1. KPIs oficiais": "",
    "2. Contagens": "pedido (Pedidos)",
    "3. Valores (R$)": "item (Itens)",
    "4. Diagnóstico": "pedido (Pedidos) ou item (Itens) conforme a base",
    "5. Sellers": "par pedido × seller (Pedido Seller)",
    "6. Tempo": "dimensão Calendário (marcada como tabela de datas)",
    "7. Status": "herda do KPI",
}
GRAN_KPI = {
    "KPI01 % Avaliações Ruins": "pedido; denominador = pedidos avaliados",
    "KPI02 % Frete sobre Produtos": "item; denominador = Σ preço dos itens",
    "KPI03 % Postagem no Prazo": "pedido; denominador = pedidos elegíveis",
}

MATRIZ = """# Auditoria DAX: Olist CP5 (Power BI)

Modelo: `entregaveis/olist_cp5.pbix`, dashboard de uma página (fonte editável em `entregaveis/powerbi/olist_cp5.pbip`).
Todas as medidas estão na tabela **`Medidas`** (coluna auxiliar `Auxiliar` oculta), organizadas em pastas de exibição.

**Como os testes foram executados.** As consultas de `scripts/validacao_dax.dax` rodaram com `scripts/executar_dax.ps1`
(ADOMD.NET, `Microsoft.PowerBI.AdomdClient.dll` do Power BI Desktop 2.159) contra o modelo **aberto do próprio `olist_cp5.pbix`**,
sem atualizar os dados. Resultado salvo em `validacao_dax_resultado.txt`: 13 consultas, 0 erros. Todos os itens abaixo
foram **executados**; nenhum foi marcado como validado sem execução.

**Referência E1.** Valores conferidos contra `output/dashboard/kpi_resumo_periodo.csv`, `kpi_mensal.csv`, `kpi_regiao.csv`,
`kpi_uf.csv`, `relacao_atraso_avaliacao.csv` e `kpi_seller.csv`.

## Matriz do contrato

| Família | Função / requisito | Medida em que aparece | Teste e resultado (consulta) | Contexto de filtro / granularidade |
|---|---|---|---|---|
| F1 Razão | `DIVIDE` | `KPI01 % Avaliações Ruins`, `KPI02 % Frete sobre Produtos`, `KPI03 % Postagem no Prazo`, `% Entrega Atrasada`, além de variações e participação | V01: 2025 = 0,13372 / 0,170884 / 0,914518; 2024 = 0,105875 / 0,160163 / 0,913897, iguais à E1 (13,37 / 17,09 / 91,45 e 10,59 / 16,02 / 91,39). V12: em set/2018 (sem dados) retornam vazio, sem erro | Nenhuma razão usa `/`. Sem alternativa explícita, o denominador zero/vazio devolve BLANK, e o status mostra "Sem dados no recorte" |
| F2 Contagem condicional | `CALCULATE` + filtro explícito | `Pedidos com Avaliação Ruim`, `Pedidos Avaliados`, `Pedidos Postados no Prazo`, `Postagens Atrasadas` | V01: 7.016 ruins ÷ 52.468 avaliados (2025) e 2.312 ÷ 21.837 (2024), iguais à E1 | Filtros com `KEEPFILTERS` para respeitar seleções do usuário nas mesmas colunas |
| F2 | `COUNTROWS` | `Pedidos Avaliados`, `Pedidos Elegíveis para Postagem`, `Pares Pedido-Seller Elegíveis` | V01: 52.783 elegíveis / 48.271 no prazo (2025) | `Pedidos` tem 1 linha por pedido (validado: 74.781 linhas = 74.781 IDs distintos) |
| F2 | `DISTINCTCOUNT` | `Pedidos Entregues`, `Pedidos com Avaliação Ruim` | V01: 52.783 e 21.998 pedidos, iguais à proposta | Conta `ID Pedido`, nunca linhas de item |
| F2 | `IN` | `Pedidos com Avaliação Ruim` (`Nota Avaliação IN {1, 2}`), `Pedidos Avaliados` (`IN {1,…,5}`), `Pedidos com Entrega Avaliável` | V01 (idem); V06: 2×2 postagem × entrega = 44.988 / 3.480 / 3.005 / 989 avaliados, igual a `relacao_atraso_avaliacao.csv` | Nota = avaliação mais recente do pedido (regra da E1) |
| F3 Contexto | `ALL` | `KPI01 Todas as Regiões` | V04: 0,13372 em todas as UFs de 2025 (referência nacional) | Remove só a tabela `Local Cliente`; mantém período. Ignora o slicer de Região de propósito (denominador nacional) |
| F3 | `REMOVEFILTERS` | `Pedidos Ruins acima da Média`, `% Participação nas Postagens Atrasadas` | V04: RJ = 427,4, BA = 73,9, CE = 43,9, PA = 32,9, MA = 24,0 (iguais ao relatório da E1). V13: participações dentro do Nordeste somam 1,00 (100%) | No excedente: tira UF/região para a taxa nacional. Na participação: tira o seller da linha **e** o filtro top 10 do visual G5; período e região selecionados continuam valendo |
| F3 | `ALLSELECTED` | `Ranking Seller por Postagens Atrasadas` (tabela de candidatos) | V07: ranking 1–10 correto com a UF do seller na mesma tabela. V14: dentro do Nordeste ranqueia só os pedidos do NE (1º = Seller 06a2c3af, 25 atrasadas) | Respeita os slicers de período/região e ignora o filtro de linha (seller e UF). Bug corrigido: a 1ª versão usava `ALLSELECTED(Sellers[Seller])` e empatava em 1 por UF |
| F4 Iteradoras | `SUMX` | `Valor Pago Produtos mais Frete` (`SUMX(Itens, Itens[Preço] + Itens[Frete])`) | V09: R$ 8.451.584,77 (2025) = Frete Total + Valor dos Produtos | Expressão por linha de item. O KPI02 usa `SUM` de propósito: soma simples é o correto e não precisa de iterador |
| F4 | `AVERAGEX` | `Nota Média de Avaliação`, `Média de Dias Postagem até Entrega` | V09: nota média 4,14 (2025) / 4,23 (2024); 9,1 / 9,0 dias | Itera sobre pedidos com valor; pedidos sem avaliação não entram |
| F4 | `RANKX` | `Ranking Seller por Postagens Atrasadas` | V07: 1º Seller 7c67e144 (164 atrasadas em 478), 2º 06a2c3af (121), 3º 88460e8e (111). V08: top 10 = 896 de 4.522 atrasadas (19,8%) e 4.639 de 53.622 pares (8,7%) | Mínimo de 30 pares elegíveis; desempate pela % atrasada (V14: dois sellers com 10 atrasadas ficam em 4º e 5º, à frente o de maior %). DENSE. Pares pedido × seller, não pedidos únicos |
| F5 Tempo | `TOTALYTD` | `KPI01 Acumulado no Ano` (numerador e denominador acumulados) | V03: o acumulado de ago/2018 = 0,13372, igual ao KPI01 de 2025; mar/2018 = 0,1805 | Sobre `'Calendário'[Data]`, marcada como tabela de datas. De set a dez repete o valor de agosto (não há vendas). Só é exibido no tooltip do G1 (jan–ago) |
| F5 | `SAMEPERIODLASTYEAR` | `KPI01 Período Anterior` | V02: em 2025 retorna 0,105875 (= 2024); variação +2,78 p.p. | Janela comparável jan–ago nos dois anos: a base não tem set–dez/2018, e o recorte da E1 exclui set–dez/2017 |
| F5 | `DATEADD` | `KPI02 Período Anterior`, `KPI03 Período Anterior` (−1 YEAR) | V02: 0,160163 e 0,913897 (= 2024); variações +1,07 e +0,06 p.p. | Mesma janela jan–ago; datas originais 2017/2018 = proxies 2024/2025 |
| F6 Lógica | `VAR` / `RETURN` | Todos os status, cores, contextos, variações, `Pedidos Ruins acima da Média`, `Ranking…` | V10: textos e cores calculados para os dois períodos | Limites centralizados na pasta "0. Metas e limites" (`Marco 2026 KPI01` = 12%, `Limite Frete KPI02` = 17,1% etc.) |
| F6 | `SWITCH(TRUE())` | `KPI01 Status`, `KPI02 Status`, `KPI03 Status`, `KPI0x Cor Status`, `Cor Frete Região` | V10, 2025: "✖ Acima do marco 2026: +1,4 p.p." / "✔ Dentro do limite: folga de 0,01 p.p." / "✖ Abaixo do marco 2026: faltam 3,5 p.p."; 2024: "● Dentro do marco 2026; faltam 0,6 p.p. para 2027". V05: `Cor Frete Região` vermelha para N, NE, CO e S e cinza para o Sudeste | Status sempre em texto com símbolo; a cor nunca é a única pista |

## Higiene do modelo

- **Tabela dedicada `Medidas`** com as 55 medidas em 8 pastas; a única coluna (`Auxiliar`) fica oculta.
- **Nenhuma coluna calculada.** Atributos de linha (flags booleanas, situação de postagem/entrega) vêm prontos da E1 via Power Query; a `Calendário` é gerada em M.
- **Formato definido na criação** em todas as medidas numéricas: `0.0%`, `#,0`, `R$ #,0.00`, `0.00`, `+0.0;-0.0;0.0` para p.p. As medidas de texto (status, contexto, metas) não têm formato numérico.
- **Relacionamentos** muitos-para-um, filtro em direção única e sem relação fato-fato: `Pedidos`, `Itens` e `Pedido Seller` → `Calendário` (Data Compra), → `Local Cliente` (UF Cliente); `Itens` e `Pedido Seller` → `Sellers`. O frete é somado em `Itens`, sem join que o duplique.
- **Chaves técnicas ocultas** (IDs, datas e UFs das fatos). Data e hora automáticas desligadas (`__PBI_TimeIntelligenceEnabled = 0`).
- Granularidades: `Pedidos` = 1 linha por pedido entregue; `Itens` = 1 linha por item; `Pedido Seller` = 1 linha por par pedido × seller, usada só no ranking de sellers.

## Catálogo de medidas

"""


def linha(pasta, nome, fmt, fam, desc, dax):
    gran = GRAN_KPI.get(nome) or GRANULARIDADE[pasta]
    expr = dax.replace("|", "\\|").replace("\n", "<br>").replace("    ", "&nbsp;&nbsp;")
    return f"| {pasta} | `{nome}` | {fam if fam != '-' else '—'} | `{fmt or 'texto'}` | {desc} | {gran} | <code>{expr}</code> |"


corpo = ["| Pasta | Medida | Família | Formato | Propósito | Granularidade / denominador | DAX |",
         "|---|---|---|---|---|---|---|"]
corpo += [linha(*m) for m in gp.MEDIDAS]
destino = AQUI.parent / "AUDITORIA_DAX.md"
destino.write_text(MATRIZ + "\n".join(corpo) + "\n", encoding="utf-8")
print(f"{destino} ({len(gp.MEDIDAS)} medidas)")
