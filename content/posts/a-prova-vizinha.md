---
date: "2026-11-23"
description: "Antes de contar um controle como cobertura, quero vê-lo barrar a falha que ele promete barrar, pelo mesmo caminho que o sistema usa de verdade."
tags: ["ai-agents", "agent-security", "supply-chain", "evals", "false-green"]
slug: "a-prova-vizinha"
title: "A prova vizinha"
draft: false
summary: "Antes de contar um controle como cobertura, quero vê-lo barrar a falha que ele promete barrar, pelo mesmo caminho que o sistema usa de verdade."
cover:
  image: "/og/a-prova-vizinha.png"
  alt: "A prova vizinha"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# A prova vizinha

Em 16 de setembro, descobri que 13 hooks do meu agente estavam mortos. Entre eles estavam o que registra telemetria e os que aplicam privilégio mínimo, como o que barra leitura em massa de contexto. A suíte tinha 89 gates, todos verdes.

A causa era banal. Os arquivos tinham passado pelo WhatsApp, e o macOS carimbou cada um com o atributo de quarentena. O harness chama o hook pelo caminho do arquivo, o sistema operacional tenta executá-lo e nega com `Operation not permitted`. A suíte rodava os mesmos hooks com `python3 <arquivo>`. O interpretador só lê o arquivo, e leitura passa pela quarentena. Os testes provavam a lógica. Não provavam que o hook rodava.

Nos dois textos anteriores, chamei isso de prova vizinha: o controle responde a uma pergunta real, só não à que eu precisava fazer. O teste da minha regra contra injection confirmava o envelope, e o ataque chegou como arquivo. O contrato de capacidades provava a declaração, e o alcance veio do ambiente herdado. Este texto é sobre o caso mais comum: o controle que existe no papel, passa no teste e não roda.

O procedimento de isolamento do texto anterior tinha um problema mais antigo. No fim de outubro, revisando o documento, achei promessas sem mecanismo. Ele prometia container, credencial isolada e checagem do commit revisado. O executor real rodava sem isolamento por padrão e herdava o ambiente do host. O container exigia que a entrada estivesse dentro do projeto e cortava a rede, então a instalação de dependências quebrava. E neste computador não há daemon Docker, então os testes de contenção davam `SKIP_AMBIENTE`, que não é verde nem vermelho.

Reescrevi o documento para descrever o executor que existe. Ficou mais curto e mais feio. E escrevi a regra que hoje acho a mais importante daquele registro: não marcar falha fechada como fechada enquanto canário e testes de contenção não rodarem no ambiente real.

Lendo o que saiu numa semana de novembro sobre segurança de agentes, achei o mesmo desenho em quatro controles, de fontes diferentes:

| Controle | O que prova | O que não prova |
|---|---|---|
| Pinar action por SHA | Que a revisão usada é sempre a mesma | Que essa revisão era confiável |
| Assinar imagem de container | Que o artefato não mudou depois de assinado | O que entrou nele antes da assinatura |
| Retenção zero na inferência | Que a chamada não fica guardada | Que a cópia para análise não fica |
| Avaliar o agente pela resposta final | O que o agente disse | O que o agente fez |

As linhas vêm da [Socket](https://socket.dev/blog/hardening-github-actions-against-outside-threats), do [Datadog](https://www.datadoghq.com/blog/engineering/software-supply-chain-policy-enforcement/), da [Eden AI](https://www.edenai.co/post/fireworks-ai-breach-limit-third-party-ai-exposure) e do [Claw-Eval](https://arxiv.org/abs/2604.06132). A última tem número: avaliar sem olhar a trajetória deixou passar 44% das violações de segurança, em 14 modelos de fronteira.

Em 23 de novembro, testei o linter de voz nos rascunhos desta série. Fiz duas mudanças: tirei a seção obrigatória de incerteza e inseri a frase "Além disso, vale destacar que é importante ressaltar". O linter apontou a seção ausente. Não apontou a frase.

Rodado depois do incidente do texto anterior, o mesmo linter deu zero erros nos comentários publicados. Isso não contradiz a revisão que achou fato errado neles: o linter checava voz, a revisão checava se as afirmações tinham sustentação. Minha impressão é que, no painel, verde ao lado de verde parece cobertura.

Meu contrato de agente já tinha uma regra para isso: gate novo só conta quando detecta um negativo plantado, porque gate que nunca reprovou pode ser verde de graça. A série me mostrou que a regra é fraca do jeito que está escrita. O linter reprovou um negativo, a seção ausente, e deixou passar o defeito que eu queria testar. Os 89 gates de setembro nunca tinham enfrentado um hook que não executa. Reprovar alguma coisa não basta: o negativo tem que ser o defeito que importa, no caminho que importa.

## O que ainda não sei

- Não conferi se já foi implementado um teste que chama os hooks pelo mesmo caminho usado pelo harness. Essa era a prevenção que anotei em setembro.
- Quantos dos meus outros gates verdes são prova vizinha. Não fiz o censo.
- O que o linter de voz deixa passar além daquela frase. Testei um negativo, não um corpus.

Antes de contar um controle como cobertura, quero vê-lo barrar a falha que ele promete barrar, pelo mesmo caminho que o sistema usa de verdade.
