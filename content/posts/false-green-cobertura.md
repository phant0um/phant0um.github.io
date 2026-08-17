---
tags: ["testing", "verification", "mutation-testing", "ai-agents"]
description: "Um campo do relatório de auditoria errou de quatro formas diferentes, e a quarta apareceu enquanto eu escrevia o artigo. Todas produziam verde."
slug: "false-green-cobertura"
title: "Minha suíte de testes provou a si mesma, e a prova era falsa"
date: "2026-08-11T09:00:00-04:00"
draft: false
summary: "Um campo do relatório de auditoria errou de quatro formas diferentes, e a quarta apareceu enquanto eu escrevia o artigo. Todas produziam verde."
cover:
  image: "/og/false-green-cobertura.png"
  alt: "Minha suíte de testes provou a si mesma, e a prova era falsa"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
Meu harness de auditoria reportava 49 de 49 detectores provados. Neutralizei
cinco deles à mão e rodei de novo. Continuou 49 de 49. Continuou verde.

O número não media detectores. Media se a suíte de testes saía com código zero.

A tese, que me custou três bugs para aprender e um quarto para levar a sério: **suíte verde é fato sobre o runner,
não sobre o sistema.** "Os testes passaram" e "este código tem um teste que
planta o defeito dele" parecem a mesma afirmação e não são. A primeira descreve
um processo que terminou. A segunda descreve um artefato que existe.

## O problema: a pior classe de bug num sistema de verificação

Um detector quebrado falha alto e alguém conserta. Um detector que **mente
sobre estar verificado** falha calado, e toda decisão a jusante herda a mentira
sem sinal nenhum de que havia algo a desconfiar.

O mecanismo era burro, como costuma ser. O campo `proven` do relatório vinha do
exit code da suíte: suíte passa, e todo código declarado ganha `proven: true`,
exista ou não um teste para ele.

O que torna isso pior que um bug comum: o número existia justamente para eu
poder parar de olhar. Um painel de verificação que você confere manualmente não
serve para nada. Confiei, e a confiança era o produto do defeito.

## Como descobri: quebrar de propósito

Não descobri lendo o código. Descobri porque desconfiei do número redondo.

49 de 49 é bonito demais para um sistema que eu tinha acabado de escrever. Então
apliquei o teste mais barato que existe: **neutralizei cinco emit-sites** — os
pontos onde o gate emite seu código de erro — e rodei tudo de novo.

Se o relatório fosse honesto, cinco detectores deveriam aparecer como não
provados. Apareceu 49 de 49.

Isso é mutation testing na versão manual e feia, e foi suficiente. A pergunta
que ele responde não é "meus testes passam" e sim "meus testes *notam* quando
eu quebro alguma coisa". São perguntas diferentes, e só a segunda tem valor.

## O que tentei antes

**Confiar no relatório e olhar o resto.** É o default e é o que estava em
vigor. Falhou pelo motivo acima: o campo era derivado do processo, e o processo
terminava bem mesmo com o sistema quebrado.

**Contar testes.** Tentador porque é fácil: a suíte já era grande e isso soava
suficiente. Mas contagem de testes não mapeia para códigos cobertos. Dez testes podem exercitar
o mesmo código e deixar sete descobertos, que foi exatamente o meu caso.

**Cobrir por inspeção.** Ler a suíte e marcar o que parece coberto. Descartei
porque é a mesma autocertificação com passo humano no meio, e o humano cansa.
Se a regra é checável mecanicamente, ela pertence ao código.

## A solução: parar de perguntar se a suíte passou

A correção foi trocar a pergunta. Em vez de "a suíte passou?", o relatório passou
a perguntar **quais códigos um teste de negativo plantado realmente exercita**.

Na prática: parsear a suíte, extrair os códigos que os testes de fato afirmam,
intersectar com o conjunto de códigos declarados, e reportar essa interseção.

O número novo, na primeira rodada honesta: **43 de 50. Sete códigos com
cobertura zero.**

O denominador mudou de 49 para 50 aqui, e vai para 51 no fim deste texto. Não é
erro de digitação: o conjunto de códigos declarados cresceu enquanto eu
trabalhava, porque escrever os testes revelou detectores que precisavam de
código próprio. Registro a variação porque um artigo que acusa número sem
procedência não pode ter três denominadores calados.

E os sete não eram obscuros. Dois deles: se o conjunto de avaliação held-out
ainda bate com seu hash, e se uma execução emite os campos de telemetria que
declara emitir. As checagens sobre se a minha avaliação é honesta eram
justamente as sem teste.

Escrevi 14 testes para fechá-los (`DeclaredNegativeGapTests`, se você quiser o
formato). Cada um planta um defeito e afirma que o gate emite aquele código
exato. Não "algum erro": aquele código.

O teste do hash held-out precisou de dois diretórios temporários, porque o
conjunto held-out tem que viver fora da raiz auditada. Se ficar dentro, a
auditoria lê o próprio gabarito e o teste passa por motivo errado.

### O segundo false green

Mesmo campo, forma diferente. Por subcomando, `detected` estava contando
**achados vivos no meu vault**, não detectores cobertos.

Vault sujo, número alto. Vault limpo, número baixo. O significado invertido:
quanto melhor o repositório, pior parecia a cobertura.

O teste que fixa isso não checa um valor, checa uma **independência**:

> Rode a função de cobertura contra uma lista suja de achados e contra uma
> limpa. Afirme que as duas retornam o mesmo `detected`.

Se o estado do repositório move esse número, a semântica está errada. Esse
padrão vale muito além do meu caso: quando um campo deveria descrever a
*capacidade* do sistema e não os *dados* do momento, o teste certo é de
invariância, não de valor.

### O terceiro

Mesmo campo, visão agregada. A rodada completa somava os contadores por
subcomando, então qualquer código checado por dois subcomandos era contado
duas vezes.

Três formas distintas de o mesmo campo estar confiantemente errado. Ainda
apareceria uma quarta, no fim deste texto.

## Onde está hoje

Rodei tudo de novo agora, escrevendo este texto, porque número em artigo
público envelhece mal:

```
Pytest: 141 passed, 0 failed, 1 skipped
cobertura: detected 51, required 51, uncovered []
```

O `uncovered: []` só vale alguma coisa porque eu sei quebrá-lo. Quando
neutralizei doze emit-sites, oito testes falharam. Os outros quatro não tinham
teste que os matasse, e o valor disso foi saber **quais quatro**.

### O quarto false green, que apareceu enquanto eu escrevia isto

Reli os dois parágrafos acima em sequência e eles se contradizem. Se todo código
tem um teste que o exercita, neutralizar doze emit-sites deveria derrubar doze
testes. Derrubou oito.

A explicação é que emit-site e código não são a mesma unidade: um código pode
ser afirmado por um teste que passa por outro emit-site, então o mapa
código→teste fica completo enquanto quatro pontos de emissão continuam sem teste
próprio. `detected 51, required 51` é verdade e insuficiente pela mesma razão que
o exit code era: mede na granularidade errada.

Não é a ressalva de que cobertura de existência não garante qualidade do
detector, que já é conhecida. É a existência sendo contradita pela mutação, no
mesmo relatório, e eu tinha publicado o número sem cruzar os dois. Quarta forma
do mesmo campo estar confiantemente errado, e a primeira que o próprio artigo
produziu.

## O trade-off

Isso custa caro e o custo é permanente.

Cada código novo agora exige um teste que planta o defeito dele. Não dá para
adicionar um detector em cinco minutos: são cinco minutos de detector e vinte de
teste que o quebra de propósito. A suíte cresce mais rápido que o sistema.

Também ficou mais lenta. A suíte passa de dois minutos, o que já é atrito real
— rodo menos vezes do que deveria, e isso é uma dívida que ainda não paguei.

Aceitei porque a alternativa é um painel que mente. Nunca tinha visto esse gate
falhar até neutralizar os emit-sites à mão, e até ali ele era um comentário que
eu pagava em toda rodada.

## O que ainda não sei

Neutralizar emit-site à mão funcionou com doze sites e não vai funcionar com
cem. Vira trabalho chato que eu pulo exatamente quando estou com pressa, que é
quando importa. Suspeito que precise virar rotina automatizada, mas ainda não
desenhei como fazer isso sem que a suíte de mutação vire ela própria um processo
cujo verde ninguém audita. O problema tem cara de recursivo e não sei onde ele
para.

E quanto vale `detected == required`? Ele prova que cada código tem *um* teste
que o exercita, e não prova que o teste cobre os casos que importam nem que o
código do detector está certo. Melhor que exit code, e ainda proxy. Minha
suspeita é que exista uma terceira ilusão embaixo desta que eu ainda não sei
nomear, porque as duas primeiras também pareciam o fim da linha.
