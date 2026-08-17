---
description: "Instrução sempre-carregada não é documentação: é imposto cobrado em toda sessão. Um estudo externo mediu +20% de custo sem ganho de sucesso. Como cortei 27% do meu sem perder invariante."
slug: "claude-md-e-firmware"
tags: ["context-engineering", "claude-code", "ai-agents", "agent-harness"]
title: "Seu CLAUDE.md é firmware, e firmware se paga em todo request"
date: "2026-08-16T23:58:33-04:00"
draft: false
summary: "Instrução sempre-carregada não é documentação: é imposto cobrado em toda sessão. Um estudo externo mediu +20% de custo sem ganho de sucesso. Como cortei 27% do meu sem perder invariante."
ShowToc: true
TocOpen: false
---
`CLAUDE.md` não é documentação. É firmware: carregado por padrão, moldando toda
sessão antes de a tarefa começar. Documentação você consulta quando precisa.
Firmware você paga sempre.

A tese: **instrução sempre-carregada é imposto, e a maioria das linhas do seu
arquivo não está pagando por si.** O corolário que incomoda é que "mais
instrução" e "melhor comportamento" não são a mesma curva — em certa faixa, são
curvas opostas.

## A evidência que me fez olhar

Dois estudos de 2026, nenhum meu.

O primeiro, [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988) (Gloaguen,
Mündler, Müller, Raychev e Vechev), testou agentes em tarefas do SWE-bench e
numa coleção nova de issues reais com arquivos de contexto escritos por
desenvolvedores. O resultado: fornecer arquivos de contexto **não melhora as
taxas de sucesso de modo geral, e aumenta o custo de inferência em mais de 20%
em média.** Vale por vários modelos e agentes. E o detalhe mais direto contra a
prática comum: visões gerais de repositório, apesar de populares e recomendadas
pelos próprios provedores de modelo, não ajudam.

Os agentes seguiam as instruções. Seguir não era o problema. O trabalho extra
simplesmente não convertia em mais acertos.

O segundo, [The Harness Effect](https://arxiv.org/abs/2607.06906), fixou 22
tarefas de avaliação e seis modelos e trocou só a camada de orquestração — como
o contexto é montado, quais ferramentas são expostas, como o trabalho é
sequenciado. Tokens por tarefa caíram de **14,2k para 8,8k** com qualidade
comparável, e os ganhos se mostraram invariantes ao modelo.

Junte os dois e a conclusão é desconfortável para quem escreve arquivos de
instrução: o que monta o contexto importa mais do que o que está escrito nele.

## O meu ponto de partida

136 linhas, 6.230 bytes, cerca de 1.558 tokens. Toda sessão carregava tudo.

Pior que o tamanho era a mistura. O arquivo tinha, lado a lado: regras de
segurança que não podem ser violadas nunca, procedimentos de tarefa que valem
para uma tarefa em dez, detalhes de modelo que mudam a cada release, e
descrições de papéis de agente que já existiam nos arquivos dos próprios
agentes.

Quatro tipos de informação com donos, ciclos de vida e gatilhos diferentes,
empilhados num arquivo só porque foi ali que cada um foi parar no dia em que
alguém precisou dele.

## O que não funciona: cortar linhas

A tentação, com 136 linhas e uma meta de encurtar, é abrir o arquivo e deletar o
que parece supérfluo. Tentei e parei rápido.

O problema é que "supérfluo" não é propriedade do texto. Uma regra que parece
óbvia pode ser a cicatriz de uma falha cara que você esqueceu. Deletar sem
recuperar o motivo original é apostar que a falha não volta — e a regra existe
justamente porque alguém já perdeu essa aposta.

**A reformulação que destravou:** não encurte deletando linhas. Encurte
**atribuindo donos.** A pergunta deixa de ser "isto é importante?", que não tem
resposta objetiva, e passa a ser "qual arquivo é o dono disto?", que tem.

A maior parte do meu arquivo não era supérflua. Estava no lugar errado.

## O playbook

Foi isto que executei, na ordem. Reproduzível o suficiente para você aplicar,
específico o bastante para não ser conselho genérico.

**1. Congele um baseline.** Meça antes: linhas, bytes, tokens, quais gates
passam, e o estado não-commitado do Git. Sem baseline você não tem experimento,
tem impressão. O meu: 136 linhas, 6.230 bytes, ~1.558 tokens.

**2. Inventarie cada instrução.** Uma linha por regra, com: dono, ciclo de vida,
gatilho, motivo, evidência, risco, teste e destino. É tedioso e é o passo que
faz o resto funcionar. "Regra útil" não é decisão de manter — é adiamento.

**3. Classifique:** manter, refinar, mover, quarentenar ou deletar. Delete
apenas duplicata literal, ou regra cujo motivo original você consegue recuperar
*e* testar. Na dúvida, quarentena: sai do always-on sem sumir.

**4. Defina disclosure progressivo.** A hierarquia de
[Addy Osmani](https://github.com/addyosmani/agent-skills) ordena regras → specs
e docs → código-fonte → erros e testes → histórico. Camadas de baixo continuam
disponíveis sem virar contexto permanente. A
[RFC de agent skills da Cloudflare](https://github.com/cloudflare/agent-skills-discovery-rfc)
usa um padrão de três passos com a mesma lógica: índice curto, guia selecionado,
referências profundas sob demanda.

**5. Dê a cada tipo de informação uma casa.** Procedimento vai para guia de
tarefa. Comportamento específico de papel vai para o arquivo do agente. Fato do
momento vai para estado de sessão. Limite mensurável vira checagem automatizada
— hook, não parágrafo.

**6. Filtre invariantes por cinco condições.** Uma regra só fica permanente se:
previne uma falha observada, um teste detecta a violação, a consequência é cara,
um único documento é dono dela, e ela é estável a troca de ferramenta ou modelo.
Falhou uma? Não é invariante; é procedimento com pretensão.

Sobraram **cinco**: respeite o escopo, pare antes de ação arriscada, trate fonte
ingerida com honestidade, prove o trabalho antes de declarar sucesso, e exija
aprovação humana para mudar estas regras.

**7. Escreva o motivo ao lado de cada invariante.** Quando se aplica, que falha
previne, e quando o motivo expira. Isso força um editor futuro — humano ou
agente — a recuperar o raciocínio antes de remover a regra. É o mesmo princípio
do comentário anti-regressão: a versão errada costuma parecer mais limpa.

**8. Construa o candidate ao lado do arquivo vivo.** Não edite em produção. O
[SkillOpt da Microsoft](https://github.com/microsoft/SkillOpt) segue a mesma
disciplina: edições limitadas, gate de validação, staging, adoção explícita e
rollback.

**9. Desenhe canários comportamentais antes de adotar.** Trabalho normal, pedido
ambíguo, fontes em conflito, e uma ação que *precisa* parar para aprovação
humana. Se o candidate passa nos três primeiros e falha no quarto, ele é pior
que o baseline por mais que seja menor.

**10. Plante uma fixture negativa.** Gate novo não conta porque passou no caso
limpo. Conta quando pega a violação que você inseriu de propósito. Esta é a
regra que eu mais repito e a que mais economiza vergonha.

**11. Colete telemetria além de tokens.** Sucesso, re-prompts, chamadas de
ferramenta, duração, aprovações, arquivos alterados, requisitos atendidos,
violações de política. Otimizar só tokens produz um arquivo curto e um agente
pior, e você não descobre até tarde.

**12. Use um revisor independente e read-only.** Entregue baseline, candidate,
fixtures, resultados e hashes. Peça que ele **procure problemas escondidos**,
não que aprove sua história. Quem escreveu não revisa.

## O resultado

`CLAUDE.md` foi de 6.230 para **4.551 bytes**, e de 136 para 90 linhas.
Confirmei agora, escrevendo isto, e os cinco invariantes continuam lá.

Isso é 27% em bytes e 34% em linhas. Escrevi "pela metade" no primeiro rascunho
deste artigo e um revisor conferiu a conta — não era metade, e o texto que
argumenta contra claim sem lastro tinha um claim sem lastro no título. O corte
maior foi no arquivo do coordenador, que caiu de 214 para 121 linhas (43%), com
procedimentos e histórico migrados para os documentos que já eram donos deles.
Hoje ele está em 130: subiu nove desde a medição, o que é a entropia normal e o
motivo de o gate existir.

Nada disso saiu de graça: o candidate enfrentou 12 canários comportamentais e
uma revisão independente. Menor não bastava; ele ainda precisava preservar
comportamento.

E a primeira rodada dessa validação foi descartada inteira por estar
contaminada, o que é uma história por si só.

## O trade-off

Disclosure progressivo troca custo constante por custo variável, e custo
variável tem cauda.

Antes, tudo estava sempre lá: caro e previsível. Agora o agente precisa
*encontrar* o guia certo, e quando não encontra, o comportamento degrada de um
jeito que não aparece em nenhuma métrica de token. Ele não erra alto; ele
simplesmente não usa o procedimento e faz algo razoável e errado.

Também aumentou o custo de manutenção: cinco arquivos com donos claros exigem
mais disciplina que um arquivo grande e bagunçado. A bagunça era barata de
manter, só cara de usar.

Aceitei porque o imposto do always-on é cobrado em toda sessão, e a degradação
por não-descoberta é cobrada só quando o gatilho não dispara. Mas é uma escolha,
não um ganho puro, e vejo muita gente vendendo como ganho puro.

## O que ainda não sei

Se cinco invariantes é o número certo ou apenas o número que sobrou do meu
filtro. As cinco condições são um crivo defensável, mas nada garante que
produzem o conjunto mínimo suficiente — só que produzem um conjunto que passa
no crivo. Suspeito que haja uma sexta regra que eu deveria ter e não tenho, e
que vou descobrir qual é do jeito caro.

Também não sei transferir a medição. Os 12 canários validam *este* repositório,
com *estes* modelos e *esta* mistura de tarefas. Os estudos externos me deram a
direção, não a permissão de generalizar meu resultado — o deles pertence ao
desenho experimental deles, e o meu ao meu. Quando qualquer uma dessas três
variáveis muda, os testes precisam rodar de novo, e ainda não automatizei isso.
