---
date: "2026-08-29T09:00:00-04:00"
slug: "o-imposto-de-partida"
description: "Doze harnesses rodaram o mesmo modelo nas mesmas tarefas. O consumo de tokens variou 70 vezes. A causa não é o modelo nem o crescimento de contexto — é o piso que cada harness carrega antes de começar."
tags: ["ai-agents", "harness", "custo", "benchmarks"]
title: "O imposto de partida: quando o harness domina a fatura"
draft: false
summary: "Doze harnesses rodaram o mesmo modelo nas mesmas tarefas. O consumo de tokens variou 70 vezes. A causa não é o modelo nem o crescimento de contexto — é o piso que cada harness carrega antes de começar."
cover:
  image: "/og/o-imposto-de-partida.png"
  alt: "O imposto de partida: quando o harness domina a fatura"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# O imposto de partida: quando o harness domina a fatura

Quando um agente de código sai caro, o instinto é olhar o modelo. Medições
publicadas entre junho e agosto de 2026 apontam para outro lugar: **com o modelo
e a tabela de preços fixos**, trocar o harness mudou o consumo de tokens em
setenta vezes. E o que decide a fatura no fim do mês não é a contagem de tokens —
é a fração deles que chega em cache, propriedade do caminho de rede, não do
agente.

Uso *harness* para o conjunto que envolve o modelo: prompt de sistema, descrições
de ferramentas, adaptadores, políticas, laço de execução e telemetria. Não é a
interface de terminal; é tudo que roda em volta da chamada de inferência.

O modelo continua influenciando a conta, por preço por token, verbosidade e taxa
de acerto. A afirmação aqui é mais estreita e mais útil: mantido o modelo
constante, a variação atribuível ao harness é grande o bastante para dominar a
decisão de custo.

Ingeri 117 fontes sobre agentes num único lote esta semana. Esta foi a
convergência mais forte do conjunto, e é a que tem números reproduzíveis atrás.

Antes de qualquer tabela, três grandezas que o texto mantém separadas porque elas
divergem: **tokens enviados**, **tokens faturáveis** (entrada fresca e entrada em
cache são cobradas diferente) e **custo por resultado verificado**. Boa parte da
confusão sobre custo de agente vem de tratar as três como sinônimo.

## As medições

Duas comparam harnesses sob controle. A terceira cumpre outra função, e vale
dizer isso na entrada em vez de tratar as três como réplicas do mesmo
experimento.

**O benchmark de junho** ([harness-efficiency-bench](https://www.eishanlawrence.com/blog/harness-efficiency-bench))
rodou doze configurações — Aider, Claude Code, Codex, Goose, Hermes, Kilo, Kimi
Code, Nanobot, OpenClaw, Opencode e Qwen Code, contando o modo architect do Aider
à parte — nas mesmas doze tarefas de Python, todas através do OpenRouter, com o
mesmo modelo. Depois repetiu tudo com um segundo modelo não relacionado.

**A Composio** ([comparação de agosto](https://composio.dev/content/best-agent-harness-deepseek-v4-flash))
comparou oito harnesses com um só modelo em trinta fluxos de trabalho
corporativos — Airtable, Gmail, Google Calendar, Sheets, GitHub, Slack, PostHog
— com teto de 900 segundos por tarefa e um verificador programático no lugar de
um juiz LLM, sobre fixtures isoladas semeadas com iscas.

**A Artificial Analysis** mantém um
[índice contínuo](https://artificialanalysis.ai/agents/coding-agents) que combina
DeepSWE, Terminal-Bench v2.1 e SWE-Atlas-QnA: 326 tarefas, taxa de acerto
média de três tentativas cada. Ela não isola o efeito do harness como as duas
primeiras — é um índice agregado de desempenho de pares harness-modelo. Entra
aqui como o instrumento com mais peso estatístico para comparar opções em
produção, não como terceira confirmação do mecanismo.

## O problema: o piso, não o crescimento

O resultado de junho: tokens por tarefa resolvida variaram de cerca de 3.500
(Aider em modo architect) a 292 mil (OpenClaw). A ordenação praticamente não
mudou entre os dois modelos, o que torna o software do harness a explicação mais
provável para o efeito — não uma atribuição demonstrada, e sim a que sobrevive
depois de o modelo ter sido trocado.

A tentação é explicar isso por acúmulo de contexto: o harness caro seria o que
guarda mais histórico. Os dados dizem o contrário. Todos os harnesses cresceram
o contexto num ritmo parecido, algumas centenas de tokens por turno. O que os
separa está antes do primeiro turno.

Cada harness embarca sua própria bagagem — prompt de sistema, descrições de
ferramentas, preparação de ambiente — e reenvia isso a cada requisição. O
benchmark chama isso de imposto de partida e mediu: cerca de 700 tokens para o
Aider em modo architect, contra cerca de 26 mil para o OpenClaw. Uma diferença
de quarenta vezes seria tolerável se fosse paga uma vez. Não é: um piso de 26 mil
tokens atravessando quinze turnos gasta cerca de 390 mil tokens de entrada só em
andaime.

O imposto de partida multiplicado pela contagem de turnos acompanha os tokens por
tarefa resolvida com R² de 0,99, nos dois modelos — e a ressalva pertence à mesma
frase: o benchmark rodou uma passagem única por combinação de harness, tarefa e
modelo, sem estimativa de variância, e execução de agente é estocástica. Um
ajuste com essa aderência dentro daquela suíte mostra que o mecanismo é forte
ali; não demonstra que a relação se mantém em outros modelos, tarefas ou versões.

Com essa qualificação, o conselho operacional sobrevive: antes de tocar em
qualquer coisa mais elaborada, meça o piso do seu prompt e a contagem de turnos.

## O que reordena a tabela: o cache

Aqui está o achado que muda decisão de compra, e é o que mais gente erra.

A Composio reportou que o Claude Code puxou 1,5% dos tokens de entrada do cache,
contra cerca de 70% do Codex e 57% do OMP. Entrada fresca custa cerca de cinco
vezes mais que entrada em cache. O consumo bruto do Claude Code era comparável
ao dos rivais; a fatura, não.

O benchmark de junho encontrou a mesma assimetria por conta própria: o Codex
faturou mais de um milhão de tokens na suíte, dos quais 77% eram leitura de
cache, cobrada a cerca de um décimo da taxa normal. Precificado como a fatura
chega de fato, o Codex saiu mais barato por tarefa resolvida que o Claude Code —
um harness que gastou metade dos tokens brutos.

A atribuição é o detalhe que importa. O autor associou a fração quase nula de
cache do Claude Code ao caminho de serving, não aos prompts: naquele arranjo, o
Claude Code era o único harness falando com o OpenRouter pelo endpoint no
dialeto da Anthropic, e a tradução desse dialeto no gateway parece ter reduzido
os acertos de cache que o mesmo tráfego teria conseguido pelo endpoint no
dialeto da OpenAI. Comportamento de gateway muda; é um caminho observado, não
uma lei.

Mas o formato do achado é geral, e é a tese deste texto: **desconto de cache não
é propriedade do harness.** Depende do endpoint, do gateway e do provedor. Duas
equipes rodando o mesmo harness com o mesmo modelo pagam contas diferentes por
causa de uma escolha de infraestrutura que ninguém registrou como decisão.

## Onde o harness caro se paga

Explicar o custo não é coroar o mais barato. O laço de agente — olhar, agir,
conferir, repetir — é um multiplicador de custo que rende mais em código
desconhecido, teste quebrando e mudança espalhada por vários arquivos. Numa
edição pequena e bem descrita, o laço quase só reconfirma o que uma chamada
única já teria assumido.

Só que o teste de tarefa difícil não saiu como o argumento do andaime prevê.
Quatro harnesses cobrindo toda a faixa de custo rodaram dez tarefas do SWE-bench
Lite com limites generosos, e os quatro resolveram exatamente uma tarefa — a
mesma. O Aider chegou lá com 0,8 milhão de tokens; o Codex gastou 15 milhões.
Dez tarefas num modelo é base fina para generalizar; conte como sugestivo.

E a qualidade qualifica a moldura inteira. A Composio reportou taxas de acerto
entre 46,7% (OpenCode) e 66,7% (Pi Agent) — vinte pontos de diferença no mesmo
modelo. Escolha de harness move custo em múltiplos e move sucesso em pontos
percentuais. São magnitudes diferentes, não direções opostas: o harness caro
costuma acertar mais, só não o suficiente para justificar qualquer preço.

Daí sai a única métrica de compra que sobrevive: **custo por resultado
verificado**. Claude Code e DeepAgents fecharam o mesmo número de fluxos da
Composio, e uma execução bem-sucedida do Claude Code custou mais de quatro vezes
mais. O custo por **tarefa bem-sucedida** vai de US$ 0,028 (Pi Agent) a US$ 0,195
(Claude Code) — o denominador importa, e é o que separa essa tabela de um ranking
de preço por chamada.

## O que medi no meu próprio pipeline

Duas noites seguidas, a mesma fila de ingest rodou por caminhos diferentes. Em 27
de agosto, com um modelo na triagem: 24 itens, 75% aprovados, cerca de 17
minutos. Em 28, com heurística determinística no lugar: 120 itens, 98%
aprovados, cerca de 15 minutos, custo zero.

Li isso primeiro como vitória do caminho barato. Estava errado: em 113 das 117
páginas o extrator tinha copiado a linha `title:` do frontmatter da fonte para o
campo da tese, e o custo zero refletia trabalho não feito. Escrevi esse
postmortem à parte — é a mesma falha deste artigo numa versão semântica: medir o
sinal barato e chamá-lo de resultado.

O detalhe que vale trazer para cá é o que aconteceu depois do conserto. Corrigi o
parser, rerodei, medi de novo a mesma coisa — e ela deu zero. Outras 26 páginas
continuavam com uma tese que não era o artigo: imagem de topo, link solto,
resíduo de fonte de PDF. Quem achou essa segunda classe foi um modelo barato
lendo doze páginas e classificando o que via; nenhum regex meu chegaria lá,
porque escrever o regex exige já saber o que procurar. O mesmo relatório, no
entanto, errou a taxa (disse 41,7%, era 22%) e deu um arquivo como inexistente
sem que fosse. Serve para apontar a classe, não para contar os casos — e é
exatamente a divisão que este artigo pede na medição de custo: instrumento
determinístico conta, julgamento descobre o que contar.

Mas o exercício serviu para outra coisa: a comparação de custo entre os dois fires é
**impossível** com a telemetria que eu tinha. O receipt do dia 27 registrou 94
mil tokens sem separar entrada de saída, o que colapsa a diferença de cinco vezes
entre entrada fresca e entrada em cache. Meu relatório gravou `cost_usd:
unknown`, que é a resposta honesta e também a inútil.

O conselho do benchmark é operacional e eu não tinha seguido: a fração de cache
no seu próprio tráfego é verificável numa tarde, e esse exercício vale mais que
uma migração de modelo. Sem o split de entrada/saída e sem a fração em cache,
qualquer comparação entre dois caminhos de agente é opinião com casas decimais.

## O modo de falha que ninguém instrumenta

Custo não é o único risco de um harness pesado. O mesmo andaime que engorda a
conta também carrega falhas que não aparecem em nenhuma das métricas acima.

O benchmark de junho injetou 100 mil tokens de ruído irrelevante antes de cada
tarefa e observou cinco comportamentos distintos. Sete das doze configurações
transmitiram o prompt fielmente. O OpenClaw se recusou a rodar. O Kimi Code
quebrou. O Claude Code enviou tudo e foi mal.

E dois — Kilo e Opencode — descartaram entre 83% e 89% do prompt **relatando
sucesso**.

Esse é o caro. Recusa e crash aparecem no log. Truncamento silencioso é
indistinguível de sucesso na saída do harness: a tarefa volta marcada como
concluída, com uma resposta plausível construída sobre um sétimo do que você
mandou. Se a sua avaliação lê o campo de status, ela pontua isso como acerto.

A medida correspondente é bruta e cabe em uma linha de instrumentação: bytes
enviados contra bytes transmitidos. Nenhum dos painéis de custo que vi nesta leva
de 117 fontes reporta essa razão.

## O trade-off

Nada disto sobrevive intacto ao tempo. O imposto de partida é uma escolha de
produto que muda a cada release — um harness pode cortar o prompt de sistema pela
metade na semana que vem e inverter a tabela. A fração de cache depende de
roteamento de gateway, que muda sem aviso e sem changelog. As três medições
concordam hoje sobre o mecanismo; a ordenação específica tem prazo de validade
curto.

O que fica é o método, e ele custa uma tarde: meça o piso do seu prompt, conte
seus turnos, veja a fração em cache no seu tráfego real, e divida o custo por
resultado verificado em vez de por tarefa. Quatro números seus valem mais que
qualquer tabela minha ou de terceiros.

## O que ainda não sei

Não sei o quanto do efeito de cache atribuído ao dialeto do endpoint sobrevive
fora do OpenRouter. A observação vem de um gateway, num arranjo, num mês —
suspeito que o formato do achado (a infraestrutura definindo o desconto) seja
geral, e que o número específico de 1,5% não seja.

Também não sei como precificar honestamente o que o harness caro compra. Vinte
pontos de taxa de acerto contra quatro vezes o custo por sucesso é uma troca cuja
resposta depende do custo de uma falha na sua operação — e esse número não está
em nenhum benchmark, porque é seu.

E não medi a razão bytes-enviados contra bytes-transmitidos no meu próprio
pipeline. É a instrumentação mais barata deste texto inteiro e é a próxima que
vou escrever.
