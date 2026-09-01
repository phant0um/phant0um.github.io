---
date: "2026-09-01T17:30:57-04:00"
description: "Um gate que imprimia “4 errors” e saía com exit zero, três horas depois de passarmos a manhã consertando esse mesmo defeito em código alheio. Foi um dos sete lugares onde o sistema parecia medir, mas não media."
tags: ["ai-agents", "observabilidade", "testes", "harness", "postmortem"]
slug: "verde-que-significa-nao-olhei"
title: "Verde que significa “não olhei”"
draft: false
summary: "Um gate que imprimia “4 errors” e saía com exit zero, três horas depois de passarmos a manhã consertando esse mesmo defeito em código alheio. Foi um dos sete lugares onde o sistema parecia medir, mas não media."
cover:
  image: "/og/verde-que-significa-nao-olhei.png"
  alt: "Verde que significa “não olhei”"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Verde que significa “não olhei”

Passei um dia auditando o harness do meu vault junto com um agente. No fim da
tarde ele escreveu um bloco de gate para a rotina semanal: roda o verificador,
filtra os findings por severidade, falha se sobrar algum.

```python
err = [x for x in d['findings'] if x['severity'] in ('error','critical')]
print('harness: %d errors' % len(err))
```

Leu de novo, achou bom, executou antes de commitar:

```
harness: 4 errors, negativos 56/56
bloco rc=0
```

Quatro erros, exit zero. O bloco imprimia a contagem e não a usava para nada. Se
tivesse entrado assim, a cadeia semanal reportaria "4 errors" no log e seguiria
verde para sempre.

Isso aconteceu três horas depois de passarmos a manhã consertando exatamente
esse tipo de defeito em código escrito por outra pessoa.

Um gate verde não prova que o sistema está limpo. Prova que o gate não achou
nada. As duas frases só coincidem quando você sabe que ele olhou — e naquele dia
achamos sete lugares onde ninguém sabia, o nosso próprio incluído. Nenhum era
bug no sentido usual: nenhum código errado, nenhum teste falhando. Todos mediam
a própria ausência de medição.

## Verde nº 1: um verificador sem chamador

Tenho um script de auditoria de harness: 207 KB, onze subcomandos, 171 testes
próprios. Nasceu como gate de uma proposta de refatoração. A proposta fechou e
foi para o arquivo; o script ficou, sem chamador, por três semanas — zero
referências fora do diretório de scripts.

**Um verificador que ninguém chama nunca reprova nada.** Não aparece em nenhum
dashboard porque não está em nenhum dashboard. O sistema parecia auditado porque
a ferramenta de auditoria existia.

Quando o rodei, falhou com 33 erros.

## Verde nº 2: o vermelho que era ruído estrutural

Os 33 eram todos `MANIFEST_STALE`. O sistema mantém um manifesto com o hash de
cada artefato de autoridade — agentes, políticas, workflows — para detectar
mudança fora do processo.

Quatro deles eram logs append-only e arquivos de estado. Um log que cresce toda
vez que o sistema trabalha **nunca** bate hash: estava stale por construção, e
duas auditorias que não mudaram nada discordariam entre si.

O efeito é o oposto do verde e o mecanismo é o mesmo. Com 33 erros permanentes,
o modo `enforce` era inutilizável, e um gate que você não pode ligar é um gate
que não existe. O ruído estrutural desligou o sinal.

A correção não foi excluir os logs. O manifesto já classificava cada entrada por
`authority_class`, e esses arquivos já estavam marcados como `state-or-history`.
A distinção existia; o verificador é que não a usava. Passou a usar: a entrada
continua no manifesto, com seus consumidores e seu nível de risco, e só a
alegação de igualdade de bytes caiu, porque só ela era falsa.

Escolhi classificação em vez de casar caminhos de arquivo por um motivo
específico: o próximo log nasce coberto pela classe, sem ninguém precisar
atualizar uma regex.

## Verde nº 3: o bug que o conserto desmascarou

Consertados os 33, rodamos em modo `enforce`. Ainda bloqueava.

O comando de autoridade decidia bloquear assim:

```python
return report, 2 if findings and args.mode == "enforce" else 0
```

Qualquer finding bloqueava, sem olhar severidade: os oito `info` recém-criados
barravam tanto quanto um `error`. O resto do arquivo já filtrava por
severidade; só esse caminho não.

O interessante é **por que nunca apareceu**. O agregador guardava a chamada
assim:

```python
if authority_exit == 2 and not manifest_stale:
    blocking = True
```

Ou seja: se a autoridade bloqueou mas o manifesto estava stale, ignore. Como o
manifesto estava *sempre* stale, o ramo nunca era alcançado. Consertar a
primeira dívida revelou a segunda, inerte ali provavelmente desde que a cláusula
foi escrita.

Dívidas que se escondem mutuamente são difíceis de priorizar: só a de cima é
visível, e ela parece isolada.

## Verde nº 4: o nosso

Foi aqui que entrou o bloco da abertura. Tínhamos acabado de diagnosticar duas
vezes o mesmo padrão em código alheio; o passo seguinte era cabear o script na
rotina, e o gate que saiu contava erros e os descartava.

Reler mostrava um bloco correto. Só executá-lo mostrou o exit code. **Código de
gate é a categoria onde revisão visual mais falha**: o defeito não está no que
ele calcula, está no que ele faz com o resultado. Ter diagnosticado o padrão de
manhã não protegeu ninguém à tarde.

## Verdes nº 5 e nº 6: números que respondiam outra pergunta

A rotina mensal agrega custo por perfil de execução. O relatório mais recente:

> 304 eventos, $0 custo total. Perfis: deterministic(273), standard(5),
> advisor(6)...

Custo zero em todos os perfis. A leitura natural é "as rotinas são baratas"; a
correta é que `custo_usd` não está instrumentado, e o agregador soma um campo
ausente. A mesma run listava isso como action item de prioridade alta, o que
salva a situação — mas `$0` circulou no topo de uma tabela, e tabela não carrega
ressalva junto.

O valor honesto ali é `unknown`. A diferença entre `unknown` e `0` é justamente
a que decide se você vai investigar.

O segundo número veio do verificador de estado, que reportou exatamente um
problema: uma entrada de telemetria sem identificador de correlação. Um. Num
arquivo de 309 linhas, parecia um caso isolado.

O verificador tem um corte de data embutido:

```python
APPEND_CORRELATION_CUTOFF = "2026-09-01"
```

Ele só olha entradas novas. Contando o arquivo inteiro: **305 das 309 entradas
não têm o campo**. O relatório não mentia — ele respondia uma pergunta mais
estreita do que a que a gente achava estar fazendo.

A causa raiz: dois formatos com propósitos distintos escrevendo no mesmo
arquivo — telemetria de custo e receipts de pipeline. Quatro valores de
`schema_version` coabitam, e `1` e `"1"` são valores distintos para qualquer
consumidor que filtre por igualdade. Toda agregação sobre aquele arquivo hoje é
silenciosamente parcial.

Corte de data em verificador é útil: evita que dívida antiga bloqueie trabalho
novo. O problema é que o número depois do corte tem a mesma aparência de um
número absoluto.

## Verde nº 7: o checkpoint que sela a run seguinte

Este apareceu por causa de um erro anterior.

O agente me disse que a rotina mensal de auditoria "nunca tinha disparado".
Perguntei se um certo relatório no diretório de auditorias não provava o
contrário. Provava: a rotina rodara, 13 de 13 partes concluídas.

A fonte dele era um comentário dentro do arquivo da rotina:

```yaml
# NAO ha custo observado ainda (system-audit nunca disparou).
```

Prosa datada, lida como estado. O estado real estava em dois lugares — um
checkpoint e um diretório de relatórios — ambos a um `ls` de distância.
Comentário com afirmação categórica é o formato que mais convence e menos
garante, e vale para qualquer leitor: eu quase aceitei a resposta.

Verificando direito, apareceu o verde de verdade. Houve duas execuções naquele
dia: o cron às 06:08 fez a parte semanal, correta; uma execução manual às 21:43
fez as 13 partes.

A execução manual ocorreu em 31 de agosto, com dados de agosto, mas **gravou o
checkpoint lógico de setembro**: `run_mes: 2026-09`, com tudo `done`. A regra de retomada diz: se o mês do checkpoint
difere do mês atual, recrie as partes como pendentes. Na próxima janela mensal,
os dois valores serão iguais. As partes seguirão `done`.

**Pela regra atual, a auditoria mensal de setembro não vai rodar.** Foi
consumida antes de setembro começar, e nenhum gate vai reclamar, porque do ponto de vista do
checkpoint está tudo concluído.

O checkpoint não distingue "rodou na cadência" de "rodou".

## O que os sete têm em comum

Nenhum é um teste que passou quando deveria falhar. Todos são medições cujo
denominador mudou sem que o numerador contasse a história:

| verde | o que parecia | o que era |
|---|---|---|
| ferramenta órfã | sistema auditado | auditor sem chamador |
| stale estrutural | 33 problemas | gate desligado por ruído |
| severidade ignorada | limpo | mascarado por outra dívida |
| bloco sem exit | 0 erros | 4 erros, não propagados |
| custo $0 | barato | campo ausente |
| "1 entrada" | caso isolado | 305, atrás de um corte |
| 13/13 done | auditado | próxima janela selada |

A defesa que funcionou foi **negativo plantado**: quebrar o sistema de propósito
e exigir que o gate detecte.

O script já fazia isso internamente: o relatório traz `negative_controls:
{detected, required, uncovered}`, contando quantos defeitos plantados a suíte
ainda pega. Ao cabeá-lo na rotina, propagamos a regra — se `detected < required`,
a run inteira é inválida, porque a capacidade de detectar encolheu e
`findings: []` passou a significar "não olhei".

Cada mudança passou pelo mesmo teste. Um log reclassificado como arquivo de
autoridade: o erro voltou. Hash falso num agente: o bloco novo falhou com exit
1. Tudo restaurado e conferido byte a byte.

## Trade-off

Isso custa. Três coisas concretas:

**Negativos plantados são código que precisa de manutenção.** A suíte que
verifica o gate é ela mesma um gate, e pode cegar. Paramos no primeiro nível e
aceitamos que o verificador de verificadores não é verificado.

**Separar `info` de `error` reduz a pressão para consertar.** Os oito findings
reclassificados viraram ruído aceito, e se a classificação estiver errada, agora
está errada em silêncio. É falso vermelho trocado por risco de falso verde. Só é
bom negócio porque a classe é declarada no manifesto por outra pessoa, em outro
momento — não por quem está mexendo agora, para fazer o número fechar.

**Executar blocos de gate literalmente é lento.** Reler é mais rápido, e na
maioria das vezes reler funciona. Não tenho uma regra melhor que "para código
que decide passa/falha, execute".

## O que ainda não sei

Não sei se `negative_controls` escala. Funciona num sistema com uma suíte de
defeitos plantados curada à mão; não sei o que acontece quando essa suíte tem
centenas de casos e ninguém lembra por que cada um existe.

Também não sei separar, em geral, "corte de escopo legítimo" de "denominador
escondido". O corte de data que escondia 305 entradas foi uma decisão razoável
de quem o escreveu. Suspeito que a diferença esteja em o relatório dizer qual
pergunta respondeu, mas não testei isso como regra.

E não decidi o caso da run manual que sela a cadência. Marcar a execução como
manual e não gravar o mês resolve o sintoma; não sei se cria outro — uma run
manual que nunca conta pode fazer alguém rodar a rotina três vezes achando que
não pegou.
