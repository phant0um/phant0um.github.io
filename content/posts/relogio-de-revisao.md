---
date: "2026-08-12T09:00:00-04:00"
title: "Um hook zerava meu relógio de revisão, e a documentação parecia fresca"
slug: "relogio-de-revisao"
description: "Gate de obsolescência que nunca disparou não é sinal de saúde. Era erro de categoria: 'updated' responde quando os bytes mudaram, 'reviewed' responde quando alguém conferiu."
tags: ["docs-as-code", "ai-agents", "verification", "knowledge-management"]
draft: false
summary: "Gate de obsolescência que nunca disparou não é sinal de saúde. Era erro de categoria: 'updated' responde quando os bytes mudaram, 'reviewed' responde quando alguém conferiu."
cover:
  image: "/og/relogio-de-revisao.png"
  alt: "Um hook zerava meu relógio de revisão, e a documentação parecia fresca"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
Eu tinha um gate de obsolescência sobre a documentação dos meus agentes. Nada
ficava obsoleto. Nunca. Achei que era saúde.

Um hook de PostToolUse bumpava o campo `updated:` a cada escrita, e o gate lia
esse campo. Tocar no arquivo zerava o relógio de revisão dele. Fresco para
sempre.

A tese: **o gate estava calado não porque os documentos estavam bem, mas porque
lia o relógio errado em quase todos eles.** Um gate calado e um sistema saudável
produzem a mesma tela, e eu levei meses para checar qual dos dois eu tinha.

## Erro de categoria, não erro de hook

O hook estava certo. Ele existe para responder uma pergunta legítima, e
respondia bem.

O problema é que há duas perguntas, e elas só parecem a mesma:

| Campo | Responde |
|---|---|
| `updated` | quando os bytes mudaram pela última vez |
| `reviewed` | quando alguém conferiu isto contra a realidade |

O gate queria a segunda e lia a primeira. Um typo de doutrina.

A distinção importa porque as duas divergem justamente no caso perigoso. Corrigir
uma vírgula num documento de política muda os bytes e não confere nada. Reler o
documento inteiro contra o estado atual do sistema e concluir que continua
correto **não muda byte nenhum** — e era exatamente esse trabalho que o esquema
antigo não conseguia registrar.

Sob `max(updated, reviewed)`, a vírgula valia tanto quanto a releitura.

## A correção, e o comentário que vale mais que ela

A correção é uma linha de intenção: quando existe `reviewed`, ele é a âncora
única. Sem `max()` com `updated`.

O que me custou mais foi o comentário. Dois, na verdade: um no hook dizendo que
ele **nunca** escreve `reviewed`, outro no gate dizendo para não "consertar" a
âncora de volta para `max()`.

Comentário anti-regressão parece ruído até você notar quando ele é necessário:
quando a versão errada é a que parece mais arrumada. `max(updated, reviewed)` lê
como generosidade — pega o sinal mais recente dos dois, por que não? Um leitor
futuro (inclusive eu, inclusive um agente) olha aquilo e vê simetria. A versão
correta é assimétrica de propósito, e assimetria sem explicação atrai
"limpeza".

## O que o gate disse quando passou a funcionar

Não gostei da resposta. **Dos 279 documentos no escopo, 272 não tinham qualquer
campo `reviewed`.**

Um detalhe honesto sobre esse número: um registro do plano feito dois dias
depois anota 274, não 272. Os dois estão certos — o escopo andava enquanto eu
trabalhava. Guardo isso como lembrete de que número em relatório é retrato, não
constante, e artigo que publica número precisa dizer de quando ele é.

Também tirei documentos gerados do escopo. Artefato de rebuild não pode ser
revisado: ele é reescrito da fonte a cada execução. Cobrar cadência humana de
revisão dele fabrica trabalho e ensina você a ignorar o gate — que é o modo de
falha que eu estava tentando sair, não entrar.

## O que tentei antes: carimbar

O movimento óbvio, com 272 arquivos sem âncora, é rodar um script que estampa a
data de hoje em todos. O gate fica verde na hora.

Isso é lavagem, não revisão. E o pior é que funciona: produz exatamente o mesmo
verde que o trabalho real produziria, e ninguém consegue distinguir os dois
depois. Um gate que aceita carimbo treina você a carimbar.

Então o campo foi partido em três:

- `reviewed` — a data
- `reviewed-by` — quem conferiu
- `reviewed-scope` — **o que foi conferido**

`reviewed-scope` é a parte que morde, porque ela tem que ser falsificável:

```yaml
reviewed-scope: "checagem mecanica: 9/9 wikilinks resolvem;
                 5/5 paths citados existem; 0 par modelo-effort invalido"
```

Se a string de escopo não pode ser re-executada contra o arquivo, o carimbo é
decoração. "Revisado" não é escopo. "9 de 9 wikilinks resolvem" é: eu posso
rodar isso de novo amanhã e te dizer se era verdade.

O primeiro lote saiu com **39 arquivos e 33 escopos distintos**. Essa
distinção é o sinal anti-carimbo que eu passei a olhar: escopos idênticos
repetidos por um lote inteiro significam que ninguém leu nada — significam um
template preenchido. Escopos distintos significam que cada arquivo foi
encontrado no seu próprio estado.

Depois disso entrou uma catraca: o gate avisa quando um documento que já tinha
carimbo perde o carimbo.

## Valeu a leitura?

Essa é a pergunta cara, porque leitura é caro. E o custo real até aqui não é o
escopo inteiro: revisei cerca de 148 documentos em lotes, e 133 continuam sem
âncora. O número grande é a fila, não a fatura.

A resposta que me convenceu foi um defeito que **nenhum gate meu podia ver**:
seis arquivos, oito ocorrências, todas apontando uma referência de política para
um caminho de rulebook que não existe. Dois deles eram construtores de packet,
o que significa que todo briefing que o pipeline emitia citava um arquivo
inexistente.

Nenhum teste pegaria isso. O caminho era uma string dentro de um campo de
metadado — sintaticamente perfeita, semanticamente órfã. Só leitura pega.

Detalhe que achei engraçado ao verificar isto para o artigo: o caminho errado
ainda existe em dois arquivos do repositório. São `.pyc`, bytecode compilado
antes da correção. A fonte está limpa; a sombra compilada guardou o erro.

## O terceiro relógio

Escrevendo isto percebi que tinha parado uma casa antes. Troquei `updated` por
`reviewed` e continuei medindo em dias desde o carimbo — e "dias" é um proxy
pelo mesmo motivo que "bytes mudaram" era: nenhum dos dois é o fenômeno. O que
invalida uma revisão não é o tempo passar. É o mundo que o documento descreve
mudar.

Prazo fixo erra nas duas pontas. Um documento de política estável sobrevive
dois anos sem uma linha errada e o relógio cobra revisão aos noventa dias. Um
procedimento cujo comando mudou ontem está errado hoje, e o relógio dá mais
oitenta e nove dias de silêncio.

A primeira versão, que ainda é papel, associa cada tipo de documento ao evento
que invalida a revisão dele, em vez de a um intervalo:

| Tipo | Evento que invalida a revisão |
|---|---|
| Política de segurança | mudança de política, ferramenta, permissão, ou incidente |
| Procedimento operacional | mudança de comando, dependência ou fluxo |
| Documentação de arquitetura | mudança de contrato, componente ou integração |
| Nota de referência | fonte original alterada, ou uso em decisão de alto custo |
| Documento gerado | nunca — revisa-se a fonte |

A última linha é a mesma exclusão que já tinha feito à mão, agora com motivo em
vez de exceção.

Escrevo "ainda é papel" de propósito, porque o resto do artigo é sobre a
diferença entre trabalho declarado e trabalho registrado, e uma tabela bonita
sem implementação é exatamente o carimbo que este texto condena. Nenhum
documento meu declara gatilho hoje. O prazo fixo continua rodando para tudo,
grosseiro, porque é o que existe.

Prazo é uma subtração. Evento exige saber de que cada documento depende, e essa
dependência hoje mora na minha cabeça, que é o pior lugar possível para ela.

## O trade-off

O custo é que a revisão agora é trabalho declarado e visível, em vez de trabalho
invisível que eu fingia estar acontecendo.

133 documentos ainda estão sem âncora hoje — rodei o gate escrevendo este
parágrafo. Caiu de 272, e o escopo cresceu para 281 no meio tempo. Metade do
caminho, em lotes, ao longo de semanas.

Um gate honesto transforma dívida oculta em dívida visível e não paga nada
sozinho. A fila fica longa e a longa fila é a informação. Preferir o gate
quebrado porque ele mostrava zero é preferir não saber.

## O que ainda não sei

O `reviewed-scope` funciona hoje porque estou atento a ele, e atenção não é
mecanismo. Minha aposta é que, sob pressa, os escopos começam a convergir para o mesmo
template e a distinção que uso como sinal anti-carimbo se degrada em silêncio —
e nesse dia o campo vira o `updated` de novo, com mais passos. Não tenho gate
para isso. Medir distinção de escopos por lote seria o começo, e ainda não
escrevi.

A tabela de gatilhos da seção anterior pode ser bonita e inimplementável. Cada linha dela exige
que o documento declare de que ele depende, e declaração de dependência
envelhece igual a qualquer outro metadado — pelo mesmo mecanismo que quebrou o
`updated`. Suspeito que o gatilho confiável seja o que o repositório consegue
derivar sozinho (o arquivo citado mudou, o comando citado sumiu) e que tudo que
depender de eu declarar corretamente vá degradar. Ainda não escrevi nenhuma das
duas metades.
