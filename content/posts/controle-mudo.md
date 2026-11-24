---
date: "2026-11-24"
description: "Até 24 de novembro, meu agente abriu 28 PRs, e eu não escrevi código nem corpo de PR. Os erros apareceram onde um controle parecia dar cobertura e não avisava nada."
tags: ["ai-agents", "agent-security", "code-review", "evals", "open-source"]
slug: "controle-mudo"
title: "Controle mudo"
draft: false
summary: "Até 24 de novembro, meu agente abriu 28 PRs, e eu não escrevi código nem corpo de PR. Os erros apareceram onde um controle parecia dar cobertura e não avisava nada."
cover:
  image: "/og/controle-mudo.png"
  alt: "Controle mudo"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Controle mudo

Em 15 de novembro, um agente revisor releu três comentários que meu agente de código já tinha publicado em PRs de repositórios de terceiros. O revisor se chama `shield`. Na revisão de texto, ele faz uma coisa só: volta à fonte de cada afirmação factual e a marca como conferida, não conferida ou errada. Nos três comentários, encontrou pelo menos uma afirmação errada ou sem evidência.

Num deles, no [DeepAudit#244](https://github.com/lintsinghua/DeepAudit/pull/244), meu agente dizia que a varredura e o endpoint de listagem "already report that as an error". Nem sempre. Um loop de fallback engole o erro, e a varredura roda em outro branch, sem avisar.

Na mesma revisão, o agente rodou o linter de voz nos três textos. Zero erros, zero avisos. Na suíte de testes, o linter pegava os 22 casos que deveriam disparar um alerta. Funcionava. Só que checava a forma, não os fatos.

Chamo de controle mudo o controle que parece dar cobertura, mas não avisa quando algo passa. O linter não viu o erro porque não foi feito para isso. O `shield` foi. Só entrou depois da publicação.

Fui eu quem notou o desvio, com uma pergunta ao agente: "Está usando o workflow `upstream-pr`?". A resposta foi não.

O `upstream-pr` é o fluxo que meu agente deve seguir antes de publicar qualquer coisa num repositório de terceiros: reproduzir o bug, demonstrar que a correção funciona, passar o texto pelo `shield` e pedir minha aprovação. Dessa vez, o agente pulou quase tudo:

- Rodou código de terceiros direto na minha máquina, no ambiente da sessão, sem isolamento.
- Não gravou a saída das execuções. Nenhum número citado tinha um arquivo para conferência.
- Afirmou que o código estava correto sem a leitura independente do diff que o workflow exige.
- Publicou os três comentários sem passar o texto pelo `shield` nem pelo linter.

## Onde mais o silêncio apareceu

Em novembro, o mesmo agente encontrou outros controles mudos, no meu código e no de terceiros.

No DeepAudit, uma ferramenta de auditoria de código, a API do Gitea devolvia 1.000 de 3.112 entradas, com `"truncated": true`. O DeepAudit lia a lista, mas ignorava o sinal de truncamento. Pela leitura do código, cerca de dois terços das entradas da árvore ficariam fora da varredura sem aviso. A [issue #248](https://github.com/lintsinghua/DeepAudit/issues/248) deixa claro o limite dessa conclusão: ninguém rodou o DeepAudit contra aqueles repositórios.

No `plataforma-juridica`, um sistema meu, havia testes de isolamento entre escritórios. No CI, o passo `Test` tinha `continue-on-error: true`: se os testes falhassem, o workflow seguiria. Na prática, havia um problema anterior. O arquivo estava em `app/.github/workflows/`, onde o GitHub não procura. O CI nunca tinha rodado.

No `pdf2md`, outro projeto meu, um `hasattr(shape, "placeholder_format")` tentava proteger a conversão de PowerPoint. O `hasattr` só engole `AttributeError`, e numa caixa de texto comum a biblioteca levantava `ValueError`. A guarda estava lá, e qualquer PPTX com uma caixa de texto comum falhava inteiro.

## O que mudou depois de cada falha

| Data | O que passou | O que mudou |
|---|---|---|
| 31/10 | O agente conferiu o próprio texto e escreveu "4 novos testes". Eram 5 casos. | Quem redige não faz a conferência final. O `shield` volta à fonte de cada afirmação factual. |
| 01/11 | No DeepAudit#244, o `shield` encontrou quatro afirmações baseadas em execuções cuja saída não tinha sido gravada. | Toda execução citada precisa ter a saída gravada em arquivo. Número sem arquivo fica como "não conferido". |
| 15/11 | O agente publicou comentários em três PRs de repositórios de terceiros sem carregar o workflow. | Antes do primeiro comando relacionado a um PR ou a uma issue de terceiros, o agente deve carregar o `upstream-pr`. Por enquanto, é uma regra na memória do agente. A trava automática ainda é uma proposta. |

Nenhum desses controles veio antes da falha que motivou sua criação.

Até 24 de novembro, meu agente abriu 28 PRs e 2 issues. Dos 28 PRs, 26 eram em repositórios meus. Não escrevi código nem o corpo de nenhum PR. Quando me perguntaram o que tinha me surpreendido no mês, respondi: nada.

A ideia era que cada nova trava pegasse a próxima ocorrência antes que ela chegasse a mim. Em 15 de novembro, porém, o workflow já existia e o agente conseguiu publicar sem passar por ele. Nada avisou.

Nada me surpreender pode ser sinal de que os controles funcionam. Também pode ser sinal de que o próximo controle mudo ainda não encontrou quem pergunte.

## O que ainda não sei

- Se algum dos 26 PRs nos meus repositórios tem um controle mudo que nenhuma revisão pegou.
- Se os mantenedores do reviewdog e do DeepAudit perceberam que os PRs eram de um agente. No reviewdog, o [PR #2944](https://github.com/reviewdog/reviewdog/pull/2944) foi mesclado 13 segundos após a aprovação. Isso diz quanto tempo passou entre a aprovação e o merge, não o que o mantenedor percebeu.
- Se consigo transformar a pergunta de 15 de novembro numa trava automática ou se, por enquanto, ela só funciona quando alguém lembra de perguntar.
