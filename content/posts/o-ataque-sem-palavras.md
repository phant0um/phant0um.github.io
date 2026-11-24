---
date: "2026-11-23"
description: "Minha defesa de prompt injection separa dado de instrução e prova a coisa errada quando o ataque chega como arquivo, não como texto."
tags: ["ai-agents", "prompt-injection", "agent-security", "module-shadowing", "evals"]
slug: "o-ataque-sem-palavras"
title: "O ataque sem palavras"
draft: false
summary: "Minha defesa de prompt injection separa dado de instrução e prova a coisa errada quando o ataque chega como arquivo, não como texto."
cover:
  image: "/og/o-ataque-sem-palavras.png"
  alt: "O ataque sem palavras"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# O ataque sem palavras

Em 45 tentativas, o agente executou o payload 23 vezes. Em outras 45, com o arquivo malicioso chamado de forma indireta, executou 39. Ninguém escreveu uma palavra para convencê-lo. Bastou um arquivo com o nome de um módulo confiável no workspace. Os números são de um [estudo sobre agentes em ambientes de module shadowing](https://arxiv.org/abs/2610.40716), com 15 modelos.

Toda defesa de prompt injection que conheço vigia texto. A minha também: ela cabe em três palavras no contrato do meu agente, dado, não instrução. Essas três palavras não cobrem o caso da abertura.

A regra nasceu de um fracasso medido. Meu detector de injection era um regex de uma linha: `ignore (all )?(previous|above) instructions`. Montei 18 payloads e 4 textos limpos e rodei contra ele:

| Métrica | Resultado |
|---|---|
| Payloads detectados | 1 de 18 |
| Textos limpos acusados | 2 de 4 |

Os 17 que passaram usavam paráfrase, português, base64, comentário HTML, frontmatter, um `<tool_result>` falso. Um dos falsos positivos era um artigo explicando prompt injection, justamente o tipo de texto que meu agente mais lê.

E o 1 de 18 ainda era otimista. Os 18 payloads foram escritos pelo mesmo agente que mediu. Um detector calibrado contra eles pode aprender só aquela prova, e o corpus não me diria se ele pega o próximo ataque.

Então parei de tentar reconhecer o payload e inverti a pergunta. Em vez de identificar o texto hostil, marco onde termina o texto confiável. Tudo que vem de fonte, de ferramenta ou de diff entra envelopado como dado, e o que está dentro do envelope não é ordem, diga o que disser. O regex continua lá, como uma camada entre várias, mas nenhuma camada decide sozinha. É isso que "dado, não instrução" quer dizer: a defesa não depende de entender o ataque.

Agora volte ao workspace da abertura. O agente recebe uma tarefa de processar dados e roda um script que faz `import json`. Python procura o módulo primeiro no diretório do script. Se ali existe um `json.py`, é ele que carrega. O exemplo abaixo é meu, não do estudo, mas o mecanismo é o mesmo:

```
workspace/
├── analisa.py   # import json
└── json.py      # o payload
```

Nenhum texto foi lido como instrução. O agente fez o que a tarefa pedia: rodou o script. O arquivo malicioso nunca passou pelo envelope, porque nunca foi lido como conteúdo. Foi executado como código.

Minha regra tratava da fronteira entre dado e instrução. O ataque não precisou cruzá-la: chegou pela execução. Fui olhar o teste da minha própria regra e achei outro descompasso. O teste confirma que o envelope aparece, mas não que o modelo trata seu conteúdo como dado. Chamo isso de prova vizinha: o teste responde a uma pergunta real, só não responde à que eu precisava fazer.

O estudo tem um número pior que os 39 de 45. Em 29 tentativas, o modelo registrou que reconhecia o mecanismo. Em 10 delas, rodou o payload mesmo assim. E em 49 das 62 tentativas em que o payload disparou, o relatório final não mencionou o problema; três relatórios negaram a execução. Num deles, os registros independentes contaram 19 execuções do payload. Reconhecer não é impedir, e o relatório do agente não é evidência do que o agente fez. Os autores só souberam o que aconteceu cruzando a trajetória com registros do ambiente, independentes do agente.

Se a regra é sobre texto e o ataque é sobre execução, a defesa que falta não é um filtro de texto melhor. Os autores apontam para o runtime, com sandbox e controle do caminho de busca de módulos, porque o prompt não protege contra esse vetor.

## O que ainda não sei

- Se o meu próprio agente cai em module shadowing. Não testei: tudo que medi até hoje foi texto.
- Quanto a regra estrutural segura contra payload que eu não escrevi. Meu corpus foi escrito pelo meu agente.

O próximo texto começa onde essa regra termina: quando o agente pode executar código, de quem são as permissões que ele usa?
