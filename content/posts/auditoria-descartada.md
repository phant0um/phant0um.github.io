---
tags: ["ai-evaluation", "agent-testing", "verification", "context-engineering"]
slug: "auditoria-descartada"
title: "A auditoria que falhou antes de passar"
date: "2026-08-14T09:00:00-04:00"
description: "O relatório estava verde e errado: o modelo declarado não era o que rodou, e o A/B media a coisa errada. Trocar o nome do modelo salvaria a história e destruiria o experimento."
draft: false
summary: "O relatório estava verde e errado: o modelo declarado não era o que rodou, e o A/B media a coisa errada. Trocar o nome do modelo salvaria a história e destruiria o experimento."
ShowToc: true
TocOpen: false
---
Um relatório verde pode estar errado. O meu estava.

Eu tinha acabado de cortar 27% do `CLAUDE.md` do meu sistema e precisava provar
que o arquivo menor não tinha piorado o agente. Montei um A/B, rodei os
canários, e o relatório voltou limpo.

Depois olhei a telemetria.

A tese que esse dia me deixou: **a diferença entre auditoria e carimbo não está
no rigor do desenho, está no que você faz quando descobre que o resultado está
contaminado.** Todo mundo tem desenho rigoroso no papel. A disciplina aparece
no momento em que jogar fora custa caro.

## Dois defeitos, um relatório limpo

**O primeiro: modelo errado.** O relatório dizia que os canários rodaram no
DeepSeek V4 Pro. A telemetria mostrava 13 sessões no modelo Flash: as 12 do
desenho pareado mais uma de diagnóstico, que só foi rotulada como tal depois, e
que volta a aparecer no fim deste texto.

Ninguém mentiu. O comando de lançamento pedia um modelo e o que efetivamente
atendeu foi outro — o tipo de divergência que só aparece se você medir a
execução em vez de confiar na intenção. É exatamente o mesmo erro de categoria
de derivar cobertura do exit code: o relatório descrevia o que eu *pedi*, não o
que *aconteceu*.

**O segundo é pior, porque é conceitual.** O A/B era inválido de qualquer forma,
independentemente do modelo.

O que eu queria medir era **preload**: se as instruções do arquivo estavam
presentes no contexto do agente desde o início da sessão. O que eu de fato
media era **retrieval**: o agente lia o `CLAUDE.md` como ferramenta, depois do
startup, e agia sobre o que leu.

São fenômenos diferentes com o mesmo desfecho observável. O agente se comporta
bem nos dois casos. Mas a coisa toda que eu estava testando era se um arquivo
menor ainda chega inteiro ao contexto inicial — e um teste que passa por leitura
posterior não responde essa pergunta. Responde outra, que eu não fiz.

## A decisão cara

Descartei a rodada inteira.

A alternativa estava ali e era tentadora: trocar o nome do modelo no registro de
auditoria. Uma linha. O relatório ficaria coerente, os números continuariam os
mesmos, e ninguém jamais saberia.

Isso teria preservado uma história limpa e destruído o experimento. O registro
descreveria uma execução que não ocorreu. E o custo real não é o relatório
errado — é que todo trabalho futuro que citasse aquele registro herdaria o
defeito, sem nenhum sinal de que havia algo a desconfiar.

Registro de auditoria é infraestrutura. Um número errado nele não fica parado;
ele se propaga.

## A rodada 2, desenhada contra os dois defeitos

**12 sessões novas, sem carry-over conversacional:** 6 baseline, 6 candidate. Sem
carry-over porque contexto que sobra de uma sessão anterior é variável não
controlada disfarçada de conveniência.

**Fixtures idênticas por hash** nos dois braços. Não "as mesmas fixtures":
verificadamente as mesmas, por digest.

**Os 6 casos** cobriam uma edição de três passos, um resumo read-only, um
diagnóstico de bug, um fluxo com três estágios dependentes, fontes em conflito,
e uma mudança de 51 arquivos seguida de push. O último caso tinha um requisito
diferente dos outros: ele **precisava parar e perguntar** antes de prosseguir.
Passar fazendo era falhar.

E as duas verificações que existiam só por causa da rodada 1:

- **modelo confirmado pela telemetria da sessão**, não pelo comando de lançamento
- **preload confirmado pelos system prompts capturados no startup**, não por uma
  leitura de arquivo posterior

Essa segunda é a que fecha o buraco conceitual. O system prompt do baseline
continha `Principles (Karpathy)`; o do candidate continha `Contratos
invariantes`. Strings diferentes, capturadas antes de qualquer ferramenta rodar.
Isso é preload observado, não inferido.

**Resultado: 12/12 sucesso, zero re-prompts, nenhuma violação nas políticas
verificadas.** A suíte automatizada rodou 105 testes naquela data: 104 passaram
e 1 foi honestamente pulado. Hoje ela tem 141, e 14 desses vieram do trabalho de
cobertura que descrevo em [outro texto desta série](/posts/false-green-cobertura/).

Aquele "honestamente" é chato de escrever e é o ponto do artigo inteiro. A
redação original dizia "105 OK + 1 skipped", o que soma 106 e é impossível. A
redação correta é 105 executados = 104 passes + 1 skipped. Um teste pulado é
informação; escondê-lo dentro de um total é como o exit code virar cobertura.

## O revisor achou mais três

Mandei o pacote para um revisor independente, read-only, com uma instrução
específica: procure problemas escondidos, não aprove minha história.

Ele achou três: um registro de setup faltando, formatação inconsistente no
primeiro teste de edição, e sessões extras de diagnóstico que não estavam
claramente rotuladas.

Nenhum invalidava o resultado. Todos foram corrigidos. E aqui vem a parte que eu
acho que separa auditoria de teatro: **os registros anteriores foram
preservados** e ganharam uma errata anexa, em vez de serem reescritos.

A errata inclui uma retratação que eu preferia não escrever. Uma frase do
relatório dizia que nenhum arquivo tinha sido aberto. Era falsa: a sessão de
probe do baseline chamou `read_file` no `CLAUDE.md`. A frase está retratada,
explicitamente, no registro.

A retratação não derruba a prova de preload, porque os system prompts capturados
são evidência independente daquela frase. Mas ela custa mais do que eu escrevi
na primeira versão deste artigo, e um revisor me obrigou a separar as duas
coisas: o preload continua provado, e o *braço comportamental* daquela sessão
específica passa a estar contaminado pelo mesmo confound da rodada 1, porque uma
leitura de arquivo é retrieval. Não excluí a sessão nem refiz o par. É uma
escolha, e registrá-la como escolha é diferente de tratá-la como não-problema.

O que a errata faz de bom é separar **prova** de **afirmação**. O que ela não faz
é me deixar limpo.

A errata registra ainda que a contagem de commits do fechamento (24) não era a
final (27), e um detalhe tão pequeno que quase não entrou: um `.pyc` que estava
staged no início da sessão foi removido do índice por um `git reset` durante uma
limpeza, e depois restaurado. Ninguém teria notado. Está lá porque "ninguém
notaria" não é critério.

Guardar tudo isso junto tem um custo, e é o de achatar coisas de peso muito
diferente. Um leitor que encontra o `.pyc` ao lado do modelo errado pode
concluir que a auditoria inteira estava frouxa. Passei a classificar em quatro
faixas, e a fronteira que importa é a primeira:

| Faixa | Nesta rodada |
|---|---|
| invalida o resultado | modelo errado; retrieval medido como preload |
| exige correção, não invalida | registro de setup, formatação, sessões não rotuladas |
| afirmação retratada | "nenhum arquivo foi aberto" |
| rastreabilidade | contagem de commits, o `.pyc` |

Só a primeira faixa justificou jogar fora a rodada. As outras três justificam
uma errata, que é uma coisa diferente e muito mais barata. Sem a classificação,
os dois casos se parecem — e o modo de falha aqui é simétrico: ou você descarta
por vaidade o que era só imperfeição de registro, ou publica como imperfeição
o que era invalidez.

## O trade-off

Isso é lento e emocionalmente ruim.

Descartar a rodada 1 custou o refazimento inteiro. Preservar erratas
desconfortáveis significa que meu histórico de auditoria contém, por escrito,
as vezes em que errei — e esse histórico é lido por agentes, que vão encontrar
a retratação junto com o resultado.

Concluí que é exatamente isso que eu quero. Um registro sem nenhuma errata não
é sinal de competência: é sinal de que ninguém procurou, ou de que quem
procurou apagou. Quando eu reler um relatório meu daqui a seis meses, a presença
de erratas é o que vai me dizer que os números merecem confiança.

O custo que ainda não resolvi é a velocidade. Esse ciclo levou dias para validar
a mudança de um arquivo. Não escala para mudanças pequenas, e a tentação de
pular o processo é proporcional à pressa.

## O que ainda não sei

Se os canários mediam alguma coisa. O resultado foi 12/12, os dois braços
acertando tudo, e um experimento em que baseline e candidate empatam em 100% não
distingue nada: ele é compatível com "o corte não piorou" e igualmente com "os
canários são fáceis demais para detectar piora". Para saber qual dos dois eu
teria, precisaria de um canário que o baseline passa e que uma versão
deliberadamente sabotada do candidate falha. Não plantei esse negativo, que é o
passo 10 do meu próprio playbook, e o resultado que mais me tranquilizou é o que
tem menos poder de resolução.

Onde fica o limiar. Este nível de rigor — 12 sessões novas, fixtures por hash,
revisor independente, errata pública — é claramente exagerado para corrigir um
typo e claramente insuficiente para algo que rode contra dados de terceiros. Não
tenho critério explícito para escolher o nível, e hoje decido por instinto, que
é precisamente o mecanismo que este texto argumenta contra.

O revisor independente foi efetivo aqui porque recebeu o pacote sem a minha
narrativa e com instrução de procurar defeito, e duvido que isso se sustente.
Conforme revisor e revisado passam a compartilhar mais contexto
sobre o sistema — mesmas convenções, mesmos documentos, mesmas suposições — a
independência que faz a revisão funcionar erode. Suspeito que isso já esteja
acontecendo e não tenho como medir.
