---
slug: "o-gate-que-checava-o-titulo"
date: "2026-08-29T14:00:00-04:00"
title: "O gate que checava o título: 113 páginas verdes e semanticamente vazias"
tags: ["ai-agents", "pipelines", "gates", "postmortem"]
description: "Meu pipeline materializou 117 páginas em cinco segundos por zero dólar, com todos os gates verdes. Em 113 delas, a 'tese central' era a linha title: do frontmatter da fonte. Consertei, medi o mesmo eixo de antes, e errei de novo."
draft: false
summary: "Meu pipeline materializou 117 páginas em cinco segundos por zero dólar, com todos os gates verdes. Em 113 delas, a 'tese central' era a linha title: do frontmatter da fonte. Consertei, medi o mesmo eixo de antes, e errei de novo."
cover:
  image: "/og/o-gate-que-checava-o-titulo.png"
  alt: "O gate que checava o título: 113 páginas verdes e semanticamente vazias"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# O gate que checava o título: 113 páginas verdes e semanticamente vazias

Um gate que confirma a presença de uma seção não valida nada — valida que o
gerador sabe escrever cabeçalhos. Meu pipeline de ingest produziu 117 páginas
com o campo "Tese central" devidamente preenchido. Em 113 delas, o conteúdo
desse campo era a linha `title:` do frontmatter da fonte, lida como se fosse
corpo. O verificador olhou, achou a seção no lugar, e disse PASS.

As páginas não estavam vazias no sentido físico: têm entre 1,0 KB e 4,7 KB,
mediana de 1,7 KB, com argumentos, evidências e links. Estavam estruturalmente
completas e semanticamente vazias — que é a única forma de vazio que um gate de
presença é incapaz de ver.

## O caso concreto

Fire de 28 de agosto, 15h53. Fatia FIFO de 120 clippings, triagem por heurística
inline, materialização por script em lote. Os números do relatório:

| Métrica | Valor |
|---|---|
| Entradas na fatia | 120 |
| Aprovados e materializados | 117 (98%) |
| Reprovados | 3 (2%) |
| Duplicatas | 0 |
| Páginas escritas | 117, em ~5 s |
| Custo de inferência | US$ 0,00 |
| Duração total do fire | ~15 min |

Gates executados e aprovados: `state_parses`, `single_status`,
`receipt_sealed` em F1 e F2, `orphan_bodies`, `digest_match`, `schema_bounds`.
Zero wikilinks quebrados. Zero páginas órfãs. Um spot-check por amostragem
abriu três páginas ao acaso e registrou, nas três, "tese central presente".

Isto é uma página que passou por tudo isso:

```markdown
# Aider, Claude Code, and OpenClaw ran an identical model. Token use varied 70-fold.

## Tese central

title: "Aider, Claude Code, and OpenClaw ran an identical model. Token use varied 70-fold."

## Argumentos

- What the three benchmarks measured
- Cached tokens reorder the leaderboard
- Where the heavy harnesses earn their cost

## Evidências

- **[2026-08-28]** Aider, Claude Code, and OpenClaw ran an identical model. Token
  use varied 70-fold. — fonte: <caminho do clipping original>
```

A tese é o título repetido, com o nome da chave YAML junto. Os argumentos são os
cabeçalhos de seção do artigo original, raspados na ordem — é o índice, não o
conteúdo. A evidência é um ponteiro de volta para o arquivo que eu já tinha.
O artigo de origem, que continua inteiro no arquivo morto, tem os números que
importavam: 700 tokens de prompt inicial no Aider contra 26 mil no OpenClaw, R²
de 0,99 na regressão que liga esse piso ao custo por tarefa resolvida. Nada
disso entrou na página.

Vale contrastar o que o pipeline registrou com o que o incidente revelou, porque
nenhuma das duas colunas está errada — elas medem coisas diferentes:

| Indicador | O pipeline registrou | O incidente revelou |
|---|---:|---|
| Aprovação | 117/120 | 113 páginas sem tese própria |
| Tese presente | 3/3 na amostra | Linha `title:` do YAML |
| Corpo único por página | 117/117 | Corpo sem síntese |
| Wikilinks quebrados | 0 | Correto, e irrelevante |
| Custo | US$ 0,00 | O trabalho prometido não ocorreu |
| Tempo de escrita | ~5 s | Rápido por não transformar nada |

## O que o spot-check estava medindo

O verificador procurava a substring `## Tese central` e o fato de existir texto
depois dela. As duas condições eram verdadeiras. Um gerador que copia o título
para dentro da seção satisfaz as duas para sempre, com qualquer entrada.

O mesmo vale para o resto do painel verde. `orphan_bodies` conta se cada página
tem exatamente um corpo — e tinha. `digest_match` compara hashes de estado antes
e depois — e batiam. `schema_bounds` verifica se as reflexões caem entre 20 e
400 caracteres — e caíam. Cada gate respondeu com precisão à pergunta que lhe
foi feita. Nenhum foi perguntado se a página dizia alguma coisa.

## O mecanismo, em uma linha

Escrever este texto me obrigou a abrir o gerador, e o defeito é menor e mais
específico do que "o lote determinístico não sintetiza".

A função que monta a tese percorre as linhas do clipping e devolve a primeira
com mais de 40 caracteres que não seja cabeçalho, item de lista, linha de autor
ou e-mail. A ideia é pular metadados e cair no primeiro parágrafo de verdade.

Só que ela lê o arquivo **cru, com o frontmatter YAML incluído**. A linha
`title: "Aider, Claude Code, and OpenClaw ran an identical model…"` tem 88
caracteres, não é cabeçalho nem lista, e nenhum dos filtros a alcança. Ela
qualifica. Vira a tese.

Medido nas 117 páginas em vez de estimado:

| Verificação | Resultado |
|---|---:|
| Tese começa com `title:` | 113 (97%) |
| Tese contém o H1 inteiro | 113 (97%) |
| Tese com menos de 80 caracteres | 75 |

As quatro exceções são o que confirma o diagnóstico. O gerador tenta bullets
antes de cair nos cabeçalhos, e quatro fontes — papers com lista de contribuições
logo no início — tinham itens longos o bastante para serem capturados. Nessas, os
argumentos são texto real. O defeito não é "o lote nunca sintetiza"; é uma
extração cujo resultado depende do formato do arquivo de entrada, sem nada
avisando qual dos dois caminhos foi tomado.

Um detalhe de vocabulário, porque errei nele na primeira versão deste texto: isto
**não é truncamento**. Truncamento silencioso tem significado técnico preciso —
um dos artigos desta mesma leva mede exatamente isso, injetando 100 mil tokens de
ruído antes da tarefa, e reporta que dois harnesses descartaram entre 83% e 89%
do prompt e ainda **relataram sucesso**. Nada foi truncado no meu pipeline: o
arquivo inteiro foi lido, e o parser escolheu a linha errada dele.

O parentesco entre os dois casos é o modo de falha, não o mecanismo. Nos dois, a
saída é estruturalmente indistinguível de sucesso. É por isso que a instrumentação
tem que medir o conteúdo — em nenhum dos dois casos o status ajuda.

## O que tentei antes

Confiei na comparação com o fire anterior. Em 27 de agosto, a mesma fila rodou
com um modelo de verdade na triagem: 24 itens, 75% aprovados. No dia 28, a
heurística inline aprovou 98% por zero dólar. Li isso como a leitura otimista —
"determinístico venceu o LLM" — e cheguei a defender esse ângulo antes de abrir
uma página. Estava errado pelo motivo mais banal: o caminho barato foi barato
porque não fez o trabalho.

O segundo sinal que ignorei foi a distribuição. A confiança média da triagem caiu
de 0,909 para 0,793, com 29 itens (24%) abaixo de 0,7. E 77 das 117 páginas
foram parar num cluster chamado `agent-misc` — o balde residual, 66% do lote.
Registrei os dois como "afinar o roteamento depois". São a mesma evidência vista
de longe: um classificador que não lê o corpo não tem como discriminar, então
concentra tudo no genérico e no piso de confiança.

O terceiro sinal era histórico e eu tinha escrito sobre ele. Seis dias antes,
uma leva de 109 páginas materializou com zero tokens e 28 templates vazios. Eu
publiquei o postmortem, propus o gate anti-zero-tokens por fase, e não o
implementei. A recorrência não foi surpresa; foi agenda.

## O reparo

Não é "mais gates". É trocar a classe de pergunta que eles fazem — de presença
para conteúdo — e cada regra abaixo é barata e determinística:

1. **A tese não pode ser o título.** Se o texto sob `## Tese central` for
   substring do H1, ou casar com `^title:`, reprova. Pega o vazamento de chave
   YAML e a cópia literal na mesma regra.

2. **Razão de tamanho página/original.** Página abaixo de um piso da fonte é
   extração, não síntese. Já usei essa medida no incidente anterior e ela achou
   28 de 109 sozinha.

3. **Argumentos precisam de lastro próprio.** Ao menos um número, data ou nome
   próprio que **não** apareça nos cabeçalhos da fonte. Um índice raspado não
   passa; um resumo de verdade passa sem esforço.

4. **O gate só conta depois de reprovar um negativo plantado.** Escrevo uma
   página-stub à mão, rodo o gate, exijo FAIL. Gate que nunca viu vermelho é
   decoração — é a regra da casa e é o passo que eu tinha pulado.

E, antes de tudo isso, a correção de uma linha: retirar o frontmatter antes de
procurar o primeiro parágrafo. Nenhum gate seria necessário se o parser não
estivesse lendo metadados como corpo.

Nenhuma dessas regras precisa de modelo **para bloquear o caso óbvio**. Elas não
provam, sozinhas, que a síntese está correta — uma página pode passar nas quatro
e ainda resumir mal o artigo. O que elas fazem é separar "não sintetizou" de
"sintetizou mal", que são problemas com custos de detecção muito diferentes: o
primeiro é regex, o segundo é leitura. Confundir os dois foi o que me fez
endurecer a fase errada depois do incidente anterior.

## O segundo falso-verde

Apliquei a correção, rerodei a extração nas páginas afetadas e rodei de novo a
mesma medição que tinha produzido o 113. Deu zero. Anotei o antes-e-depois e dei
o assunto por encerrado.

Repeti, na verificação, exatamente o erro que o artigo acusa no gate: medi o eixo
que eu já conhecia. "Tese começa com `title:`" foi a 113 para 0 — e a métrica
estava certa. Só não era a pergunta.

O que apareceu quando alguém olhou as páginas em vez do meu regex:

| Tese central, após o primeiro reparo | Páginas |
|---|---:|
| Prosa do artigo | 91 |
| Imagem markdown | 17 |
| Link solto com quase nenhum texto | 8 |
| Resíduo de fonte de conversão PDF | 1 |

Vinte e seis páginas de 117 tinham como tese algo que não era o `title:` do YAML
e também não era o artigo. A mais literal delas abria com
`![Image](https://pbs.twimg.com/media/HQpjG3zXsAA8F8M…)`. O filtro pulava
cabeçalho, lista, autor, e-mail e afiliação — a lista do que eu tinha previsto
quando escrevi a função. Imagem de topo não estava na lista, porque não estava na
minha cabeça.

Quem achou isso foi uma auditoria adversarial: um modelo barato lendo doze
páginas e classificando cada tese como conteúdo, metadado ou entulho de página.
Nenhuma expressão regular minha teria encontrado essa classe, porque escrever a
expressão exige já saber o que procurar. Foi o único passo do reparo inteiro que
precisou de um modelo, e foi o que pagou.

O relatório dessa auditoria, porém, não servia como medida. Ele afirmou 41,7% de
páginas defeituosas; a taxa real na população era 22%. E marcou um arquivo de
origem como desaparecido — o arquivo existe, e o que falhou foi o apóstrofo
curvo no caminho. Duas afirmações erradas em um relatório de doze linhas.

A divisão de trabalho que sai disso é mais útil que qualquer das duas
ferramentas isolada. **O modelo nomeia a classe de defeito que você não
antecipou; o script mede quantos casos dela existem.** Trocar os papéis quebra os
dois: pedir contagem a um modelo produz número inventado com aparência de
medição, e pedir descoberta a um regex produz o verde que este artigo inteiro
descreve.

Depois de estender o filtro para imagem, link solto, URL nua e metadado de fonte
— com os quatro casos plantados e verificados vermelhos antes do reparo —, a
contagem final é 117 de 117 com tese em prosa.

O arco inteiro, em três medições da mesma coisa: **4 páginas com tese em prosa
antes de qualquer conserto, 91 depois do reparo do frontmatter, 117 depois do
reparo do entulho de página.** Cada número foi, no seu momento, o resultado de
uma verificação honesta. Dois deles eram falso-verde. É o terceiro número deste texto, e
não tenho garantia de que seja o último: ele mede as classes de defeito que já
foram nomeadas.

## O trade-off

A correção óbvia — "exija síntese de modelo em toda página" — devolve o custo
que o caminho determinístico eliminou, e nem sempre pelo valor devido. Para uma
release note de três parágrafos, o índice raspado é um resumo honesto; a página
oca só é oca em relação a um artigo denso.

A saída mais barata é parar de chamar as duas coisas pelo mesmo nome. O lote
determinístico produz **extração**; a fase com modelo produz **síntese**. Se o
estado registra qual das duas gerou a página, a métrica "117 ingeridos" deixa de
ser mentira e vira duas contagens verdadeiras — e o gate de conteúdo só se
aplica onde foi prometida síntese.

O segundo custo é o passivo. Endurecer a regra hoje reprova as 117 páginas desta
leva mais o que já estava no acervo com o mesmo defeito. A ordem que funciona é
a que aprendi da vez anterior: zerar o passivo primeiro, promover a regra a
bloqueante depois. Fazer o contrário produz um número vermelho grande demais
para alguém olhar.

## O que ainda não sei

Não sei se o lote determinístico devia gerar página nenhuma. Talvez o resultado
correto para uma extração seja uma entrada de índice apontando para o clipping,
sem fingir ser uma página de síntese — mas isso muda o contrato de quem lê o
acervo, e não testei.

Também não sei se a queda de confiança de 0,909 para 0,793 mede triagem pior ou
apenas o piso da heurística, que atribui 0,65 a tudo que não casa no vocabulário
central. São hipóteses diferentes com o mesmo número, e separá-las exige rodar
as duas triagens sobre a mesma fatia — coisa que ainda não fiz.

E não sei quantas classes de defeito ainda não foram nomeadas nessas 117 páginas.
Duas apareceram, uma de cada vez, e a segunda só porque paguei uma auditoria que
lê. Suspeito que a resposta honesta para "quantas faltam" não seja um número, e
sim uma cadência: rodar a auditoria adversarial por amostra a cada leva, aceitando
que o número que ela devolve serve para apontar, nunca para contar.

Fecho com o contraexemplo, porque ele é a única evidência que tenho de que o
problema deste artigo tem solução. Na véspera, dois disparos simultâneos
escrevendo no mesmo espaço de nomes fizeram oito arquivos sumir no meio da janela
de leitura. O adaptador não conseguiu ler os arquivos e devolveu decisão nula,
travando o fire — em vez de emitir um veredito plausível sobre conteúdo que não
tinha.

É exatamente a escolha oposta à do gerador de páginas, diante do mesmo tipo de
entrada faltante: um parou e reportou ignorância, o outro preencheu o campo com o
que tinha à mão e reportou sucesso. A diferença entre falso-verde e incidente
legível cabe nessa escolha. E não sei dizer se acertei ali por projeto ou por
sorte, o que é motivo suficiente para ir ler.
