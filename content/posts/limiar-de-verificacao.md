---
tags: ["verification", "testing", "ai-agents", "engineering-practice"]
title: "Quando seis canários, quando um hook, quando nada"
description: "Cinco artigos e nenhum critério: eu decidia por instinto quanta verificação cada mudança merecia. A régua que montei descreve três dos cinco casos e me condena em dois."
slug: "limiar-de-verificacao"
date: "2026-08-17T09:00:00-04:00"
draft: false
summary: "Cinco artigos e nenhum critério: eu decidia por instinto quanta verificação cada mudança merecia. A régua que montei descreve três dos cinco casos e me condena em dois."
ShowToc: true
TocOpen: false
---
Um dos cinco artigos que escrevi sobre verificação termina assim: "hoje decido
por instinto, que é precisamente o mecanismo que este texto argumenta contra".
Este texto é a tentativa de responder àquela frase.

Os outros quatro terminam admitindo variações do mesmo buraco. Cada um sabe que
a métrica que escolheu é proxy; nenhum sabe dizer por que escolheu aquele preço.
Uma mudança minha levou seis canários em doze sessões pareadas, fixtures por
hash e um revisor independente. Outra levou um hook de dez linhas. Uma terceira
levou uma linha de comentário e mais nada.

A tese: **o limiar é função de quanto tempo o erro fica invisível, não do
tamanho da mudança.** Um erro que grita custa pouco mesmo que derrube o
repositório inteiro, porque alguém descobre em noventa segundos. Um erro calado
custa meses, e o tamanho dele não muda isso. Verificação existe para comprar a
visibilidade que o sistema não dá de graça.

## O eixo errado: blast radius

O critério que eu achava que estava usando é o do manual: quanto maior o
alcance, mais teste. Mudou um arquivo, revisa; mudou cinquenta, faz cerimônia.

Ele erra nas duas pontas, e as duas pontas me morderam.

Uma mudança enorme e ruidosa é barata. Se eu quebrar o build, descubro em
noventa segundos, de graça, sem ter escrito teste nenhum. O alcance era o
repositório inteiro e o custo de verificação certo era zero, porque o próprio
sistema já reclamava.

Uma mudança de uma linha e silenciosa é cara. Trocar `max(updated, reviewed)`
por `reviewed` é uma linha; ela decidia se um gate de obsolescência olhava para
o relógio certo, e a versão errada produzia silêncio idêntico ao da versão
correta. Alcance mínimo, custo de verificação alto, e eu levei meses para notar.

Blast radius mede quanta coisa a mudança toca. A pergunta útil é outra: **se
isto estiver errado, quem me avisa, e quando.**

## O eixo certo: latência do erro

Duas perguntas, nesta ordem.

**Primeira: quanto tempo o erro fica invisível?** Não "é grave", que ninguém
consegue responder antes do fato. Quanto tempo, em unidades reais: segundos até
o build falhar, dias até alguém reclamar, indefinido até alguém olhar por
acaso.

**Segunda: quando ele finalmente aparecer, é reversível?** Um número errado num
relatório interno se corrige com uma errata. Conteúdo público indexado não se
corrige: você publica uma retratação e o original continua em cache.

O cruzamento dá quatro faixas, e cada uma tem um preço de verificação que eu
consigo defender:

| Latência | Reversível | O que a mudança merece |
|---|---|---|
| segundos | sim | nada. O sistema já é o teste |
| dias | sim | um teste comum, sem cerimônia |
| indefinida | sim | hook ou gate permanente, com negativo plantado |
| qualquer | **não** | gate que barra, mais revisor que não escreveu |

A linha que importa é a terceira, porque é a única que exige inventar
visibilidade que não existia. Teste comum verifica um caso. Gate com negativo
plantado verifica que o mecanismo de aviso funciona, o que é uma pergunta
diferente e a única que resolve latência indefinida.

A quarta linha ignora latência de propósito. Quando o erro é irreversível, não
importa se ele aparece em um segundo: já saiu.

## Passando os cinco casos pela régua

Fui checar se a régua descreve o que eu de fato fiz. Descreve em três casos e me
condena em dois.

**Cobertura derivada do exit code** ([a suíte que se autocertificava](/posts/false-green-cobertura/)):
latência indefinida. O campo dizia "provado" e ninguém tinha motivo para
duvidar dele. Terceira faixa, e a resposta foi exatamente essa: gate
permanente, com teste que planta o defeito e exige o código de erro exato.

**O relógio de revisão** ([o gate que nunca disparava](/posts/relogio-de-revisao/)):
latência indefinida também, pelo mesmo mecanismo. Um gate calado e um sistema
saudável são indistinguíveis por construção. Terceira faixa. Foi hook mais
catraca.

**O corte do arquivo always-on** ([o arquivo que se paga em todo request](/posts/claude-md-e-firmware/)):
aqui a régua me dá razão de um jeito que eu não esperava. A mudança era grande
(46 linhas a menos), mas o que assustava não era o tamanho, era que a
degradação de comportamento de um agente não emite erro. Ele não falha: faz
algo razoável e errado. Latência indefinida com um agravante, que é não haver
build para quebrar. Seis canários rodados em doze sessões pareadas é caro, e foi
o preço de fabricar um sinal que o sistema não produzia sozinho.

Segunda condenação, e mais incômoda que a primeira: a terceira faixa pede gate
**permanente**, com negativo plantado. O que eu fiz foi uma bateria one-off. O
próprio artigo daquele corte admite que nunca automatizei aquilo, então a régua
prescreve uma coisa e o registro mostra outra.

**A rodada de auditoria contaminada** ([a rodada que descartei](/posts/auditoria-descartada/)):
quarta faixa, pelo motivo que aquele artigo esgota, e eu não tinha percebido
isso na época. O descarte da rodada inteira foi caro e era o preço da faixa.

E aqui a régua me condena: a prescrição da quarta faixa é gate que barra mais
revisor independente, e gate que barrasse eu não tinha nenhum. O erro foi pego
depois, na telemetria, e a resposta foi descarte retroativo. Metade da
prescrição estava ausente exatamente no caso mais caro.

**O gate de wikilink** ([o gate de publicação](/posts/gate-de-privacidade-wikilink/)):
quarta faixa explícita. Conteúdo público é indexado, e é por isso que ali o
desenho barra em vez de avisar. É a única das cinco em que barrar é a resposta
na primeira ocorrência: o gate de cobertura também falha a suíte, e o relógio
também tem catraca, mas os dois só passaram a barrar depois que eu já tinha
visto o padrão.

**E o caso que não levou nada.** Mudei o `hugo.yaml` do blog para trocar um
campo depreciado. Se estivesse errado, o build falharia no push, em noventa
segundos, com a linha exata no log. Primeira faixa. Não escrevi teste, não rodei
canário, e a régua concorda: o sistema já era o teste, e verificação ali seria
cerimônia paga sem nada em troca.

## O problema com essa validação

Três encaixes e duas condenações. O encaixe é o que deveria me deixar
desconfiado, e deixa.

Construí a régua olhando para as decisões que já tinha tomado. Uma regra
derivada dos casos que ela explica não foi testada por eles: foi ajustada a
eles. É o mesmo erro de categoria que os cinco artigos descrevem, com outro
disfarce.

As duas condenações são o único pedaço desta seção com algum valor probatório,
porque são o que uma régua puramente ajustada não produziria. Não bastam. Uma
régua pode discordar de mim em dois casos e ainda estar errada nos cinco.

O teste real é prospectivo e ainda não aconteceu: a próxima mudança em que a
régua disser "nada" e o instinto disser "canário". Nesse dia eu descubro qual
dos dois está errado, e é a única rodada que vale.

Escrevo isso porque a alternativa era publicar a tabela sem a ressalva, e a
tabela sem a ressalva é mais persuasiva do que merece ser.

## O trade-off

Latência é mais difícil de estimar que tamanho, e essa é a objeção honesta.

Tamanho de mudança está no `git diff`. "Quanto tempo este erro ficaria
invisível" é um julgamento sobre um futuro que não aconteceu, e julgamento sob
pressa colapsa para a resposta conveniente. Sempre dá para argumentar que
alguém notaria.

A contramedida que estou usando é obrigar uma resposta concreta. Não "alguém
notaria", e sim **quem**, por **qual sinal**, em **quanto tempo**. Se eu não
consigo nomear o sinal, a latência é indefinida por definição, e a régua manda
para a terceira faixa. O default de não saber é caro, o que está certo.

O custo residual é que a régua não diz nada sobre qualidade. Ela decide se você
precisa de um gate, não se o gate que você escreveu presta. Um canário mal
desenhado e um canário bom custam o mesmo e aparecem iguais na tabela.

## O que ainda não sei

Latência e reversibilidade podem não bastar. Falta um eixo de frequência, e não
sei se ele é eixo mesmo: um erro de latência indefinida numa rotina que roda mil vezes por
dia e o mesmo erro numa rotina anual têm o mesmo lugar na minha tabela e não
deveriam. Suspeito que frequência entre como multiplicador e não como terceira
dimensão, mas não tenho caso que force a distinção, e regra construída sem caso
que a force é a que estou justamente desconfiando.

Usei a régua seis vezes e todas olhando para trás, com calma, escrevendo um
artigo. Aplicá-la em tempo real é outra coisa, e é a que importa. O
momento em que ela precisa funcionar é o oposto disso: meio da tarefa, com
pressa, quando a resposta cara é a que ninguém quer ouvir. Nenhum dos meus
gates me pergunta em qual faixa a mudança está, e essa pergunta é a única parte
deste texto que ainda depende inteiramente de mim lembrar de fazê-la.
