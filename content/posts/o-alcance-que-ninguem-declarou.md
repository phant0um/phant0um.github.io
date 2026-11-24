---
date: "2026-11-23"
description: "Meu agente rodou código de terceiro dentro da minha sessão, porque o alcance de um agente é o ambiente que ele herda, não o que está declarado para ele."
tags: ["ai-agents", "agent-security", "credentials", "sandboxing", "supply-chain"]
slug: "o-alcance-que-ninguem-declarou"
title: "O alcance que ninguém declarou"
draft: false
summary: "Meu agente rodou código de terceiro dentro da minha sessão, porque o alcance de um agente é o ambiente que ele herda, não o que está declarado para ele."
cover:
  image: "/og/o-alcance-que-ninguem-declarou.png"
  alt: "O alcance que ninguém declarou"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# O alcance que ninguém declarou

Em novembro, pedi ao meu agente que trabalhasse em contribuições em projetos de terceiros. Para conferir uma delas, ele rodou código no meu computador, dentro da minha sessão. Eu tinha um procedimento para isolar essa execução, mas ele não foi acionado. Não tenho sinal de que o código fosse malicioso, e o registro não me permite dizer quais recursos da sessão o processo chegou a usar. O alcance de um agente não é o que está declarado para ele. É o ambiente que ele herda.

O agente também publicou comentários nesses projetos. Na revisão posterior, encontrei afirmações incorretas ou sem evidência. Era um segundo erro: publicar sem ter sustentado o que dizia.

O texto anterior terminou numa pergunta: quando o agente pode executar código, de quem são as permissões que ele usa? Este caso responde do pior jeito: as minhas.

Não é que faltasse controle. Cada agente do meu sistema declara as capacidades que usa, e o que não está declarado é negado. Uma suíte de testes confere isso, inclusive tentativas de escalar para uma skill fora do contrato, e passa 31 de 31. O próprio registro da decisão diz o que esse verde cobre: a declaração estática, não o alargamento em runtime.

Rodar o código de um PR é exatamente alargamento em runtime. A ferramenta de shell estava declarada. O processo que ela abriu herdou todo o resto. É a mesma prova vizinha do texto anterior: o contrato prova o que o agente declarou, não o que um processo dele alcança.

Uma credencial herdada pode ser usada sem que a ação pareça anormal para o serviço. Um [texto da Socket sobre ameaças internas no GitHub Actions](https://socket.dev/blog/hardening-github-actions-against-insider-threats) lembra que, contra credenciais válidas, validação de entrada não ajuda, porque as requisições parecem trabalho normal. Token de acesso pessoal e chave SSH funcionam sem segundo fator enquanto existirem. Para o GitHub, um agente rodando na minha sessão sou eu.

O procedimento certo existia e tinha sido endurecido pouco antes. Ele exige isolamento declarado: se o modo não está no spec, a execução é bloqueada. O ambiente passa por allowlist (PATH, idioma, terminal), a home vira um diretório temporário novo, e a configuração global do git fica desligada. Nada disso rodou, porque o procedimento não foi acionado. Minha leitura é que o pedido curto foi tratado como atalho.

Para comandos do GitHub eu tinha uma camada a mais: um hook que intercepta toda linha com `gh`. Ele começou como lista de golpes proibidos. Um revisor automatizado rejeitou o desenho três vezes, e cada rejeição achou uma classe nova de furo de parsing. Troquei para allowlist: só passa a linha inteira que está na lista de leitura, e o resto pede confirmação. Mesmo assim, deixei registrado que ela cobre um caminho de execução, não todos. Um script gravado em arquivo ou um processo neto passa por fora. Escrever o limite fez parte da entrega.

O que tiro disso: decidir a autonomia de um agente pelo efeito, não pela ação. Meu contrato de agente tem uma regra que eu achava burocrática: efeito fora do sistema exige aprovação humana atual, porque não se desfaz, e só se aprova o que se vê. Dentro do sistema, aceito o contrário. Passei para agentes decisões de triagem que esperavam revisão humana, porque cada uma ficou registrada e reversível com um comando.

Um [guia da DigitalOcean para um time de on-call feito de agentes](https://www.digitalocean.com/blog/ai-agents-incident-response-microvms) chega ao mesmo lugar por outro caminho: a política de aprovação fica num gateway de ações, fora dos agentes, e não num prompt que o modelo possa ignorar.

Comentário publicado em projeto alheio está do lado errado dessa linha. Código rodando com a minha credencial também.

## O que ainda não sei

- Se os comentários passaram pela confirmação do hook de `gh` ou por outro caminho. O registro do incidente não diz.
- Quanto do alcance herdado foi usado. A saída das execuções não foi gravada na hora; o que tenho é transcrição.
- Qual gate mecânico fecha este caso. Bloquear comentário em projeto alheio sem evidência anexada está proposto, não implementado.

O procedimento que deveria ter isolado a execução já tinha me dado outro aviso: a versão anterior descrevia proteções que eu ainda não tinha visto funcionar. É daí que parte o próximo texto.
