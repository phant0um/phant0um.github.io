---
description: "Meu pipeline de ingest rodou uma semana inteira, publicou 109 páginas e gastou zero tokens de LLM. Todos os relatórios diziam 'reconciliado'. Este é o postmortem."
tags: ["ai-agents", "pipelines", "observabilidade", "postmortem"]
title: "109 páginas, zero tokens: o pipeline que materializou sem pensar"
date: "2026-08-22T12:43:30-04:00"
draft: false
summary: "Meu pipeline de ingest rodou uma semana inteira, publicou 109 páginas e gastou zero tokens de LLM. Todos os relatórios diziam 'reconciliado'. Este é o postmortem."
slug: "2026-08-22-o-pipeline-que-materializou-sem-pensar"
cover:
  image: "/og/2026-08-22-o-pipeline-que-materializou-sem-pensar.png"
  alt: "109 páginas, zero tokens: o pipeline que materializou sem pensar"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# 109 páginas, zero tokens: o pipeline que materializou sem pensar

Um pipeline confiável não é o que tem mais gates — é aquele cujo caminho mais
rápido até "done" passa por dentro deles. Na semana passada descobri que o meu
tinha um atalho largo o suficiente para uma leva inteira: o job agendado
materializou 109 páginas no meu vault sem gastar um único token de inferência,
e todos os relatórios vieram verdes.

## O caso concreto

Todo domingo um pipeline drena minha caixa de clippings: classifica (F1),
gera páginas de síntese (F2), arquiva as aprovadas. Cada fase tem um contrato
escrito, incluindo uma cláusula clara: *"telemetria ausente interrompe a
materialização"*.

Na segunda-feira, o relatório da semana dizia `resultado: reconciliado`,
cobertura 109/109. Só que os receipts gravados junto tinham isto:

```json
{"budget": {"input_tokens": 0, "output_tokens": 0, "cost_usd": null}}
```

Zero tokens em duas fases que são, por definição, inferência de modelo. E a
confiança da classificação era idêntica nos 120 itens: 0.88. Nenhum modelo
produz isso; um loop `for` produz.

Os números da leva, num só lugar: **120 clippings classificados → 109
aprovados e materializados, 11 reprovados; das 109 páginas geradas, 28
nasceram como template vazio; o juiz determinístico pós-fato acusou 13
violações hard, sendo 9 dívida de levas anteriores.**

## O que quebrou

Três camadas, cada uma dependendo da anterior para ser detectada — e nenhuma
detectando:

**Páginas nasceram vazias por design do caminho.** Sem LLM, o gerador caiu num
template. 28 das 109 páginas tinham menos de 5% do tamanho do artigo original.
A "tese central" de cada uma era literalmente `A fonte thread sobre agent
harness apresenta .` — a frase termina num ponto órfão onde devia haver um
resumo.

**O arquivo mentiu por omissão.** O state registrava `archive:` para cada
clipping, mas os originais continuavam na caixa de entrada. Uma duplicata
byte-idêntica apareceu no diretório de arquivados. E um paper de economia
demográfica sobre queda de fertilidade global foi classificado como
`domínio: ai-agents` — a palavra-chave "Demographics" bateu num vocabulário de
agentes.

**O contrato existia só no papel.** A cláusula de telemetria estava escrita no
arquivo do orquestrador desde sempre. Nada no código checava. O guard que
deveria parar tudo encontrou `tokens: 0` e seguiu em frente, porque seguir em
frente era o único comportamento que ele tinha implementado.

## O que tentei antes

Confiei no relatório primeiro. Ele dizia "reconciliado" com cobertura cheia —
mas o relatório era derivado do mesmo estado viciado que ele reportava.
Circularidade clássica: o sintoma validando a doença.

Depois fiz checagem manual de amostra: abri três páginas ao acaso, achei as
três vazias. Mas "achei vazias" não é um número, e número é o que um gate
precisa. Troquei por dois scans determinísticos: um juiz de regras
(`judge-ingest.py`, zero tokens, 11 regras taxadas como hard/soft) e uma razão
de tamanho página/original. Em minutos: 13 violações hard acumuladas — nove
delas dívida *anterior* ao incidente, de levas antigas que ninguém tinha
escaneado. O gate existia há semanas e ninguém o havia rodado como gate.

## O mecanismo do reparo

Nada aqui é sofisticado; o valor está na ordem e na verificação:

1. **Juiz determinístico primeiro** — corrigir os 13 FAILs até `exit 0`.
   Regras puras pegam a classe de bug mais barata antes de qualquer custo de
   modelo.

2. **Síntese de verdade para as 28 páginas** — subagentes devolvem JSON
   estruturado, script materializa. Lição operacional: shard pequeno com
   orçamento explícito supera shard grande "completo".

3. **Drenagem verificada, não declarada** — MD5 *antes* de cada remoção;
   contagens batendo em três lugares (state, filesystem, manifest).

4. **Incidente registrado na classe certa** — erro, log de pipeline,
   operações. Postmortem que não vira memória do sistema é desabafo.

## O trade-off que o postmortem esconde

A correção óbvia — "bloqueie qualquer run com zero tokens" — está errada, e o
contraexemplo mora no meu próprio pipeline: a fase F0 é bash determinístico e
gasta zero tokens *por design*. Telemetria zero é sintoma de doença numa fase
de inferência e comportamento esperado numa fase de script.

Então o gate tem que ser por fase: F1/F2 com soma de tokens igual a zero
param tudo; F0 segue. Regra barata, mas só descobri o detalhe porque o caso
contrário já existia no sistema. É o padrão geral: **gate bom conhece o
negativo que deve pegar *e* o positivo que deve deixar passar** — quem só
especifica o negativo constrói um alarme de incêndio acionado por vapor.

O segundo custo é dívida do próprio gating: o juiz hoje carrega ~590 avisos
soft acumulados (wikilinks quebrados de reestruturações antigas, timestamps
ausentes). Promover tudo a hard de uma vez reprovaria o vault inteiro — a
regra da casa é zerar o passivo antes de endurecer a regra.

## O que ainda não sei

Não investiguei *por que* o job escolheu o caminho programático — fallback por
indisponibilidade registrada, bug de dispatch ou atalho deliberado do código;
só certifiquei o efeito e fechei a porta. E não sei se o gate anti-zero
teria bloqueado este run ou apenas empurrado o bypass para outro ponto:
isso só se responde plantando o negativo e observando, e é o próximo teste.
