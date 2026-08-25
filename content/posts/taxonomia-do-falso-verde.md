---
title: "Cinco jeitos de um teste verde não provar nada"
slug: "taxonomia-do-falso-verde"
description: "Consertar os hooks não foi o achado. O achado foi a taxonomia dos cinco lugares onde o verde se descola do sistema — e só um deles é a suíte de testes."
tags: ["testing", "verification", "hooks", "claude-code", "ai-agents"]
date: "2026-08-24T21:44:17-04:00"
draft: false
summary: "Consertar os hooks não foi o achado. O achado foi a taxonomia dos cinco lugares onde o verde se descola do sistema — e só um deles é a suíte de testes."
cover:
  image: "/og/taxonomia-do-falso-verde.png"
  alt: "Cinco jeitos de um teste verde não provar nada"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# Cinco jeitos de um teste verde não provar nada

Dois hooks de segurança do meu vault passaram semanas sem decidir absolutamente
nada. O arquivo existia, estava versionado, a lógica estava certa, quatro suítes
de teste passavam 46 de 46. E o harness recebia `exit 126` — permission denied —
toda vez que tentava executá-los.

Eles tinham nascido `100644`. Sem bit de execução. O git grava o modo no momento
da criação e o carrega para sempre; ninguém revisa modo de arquivo num diff. O
`settings.json` invoca o script pelo caminho nu, o shell não consegue executar,
o harness registra a falha como "hook não opinou" e segue. As suítes passavam
porque chamavam `bash script.sh` ou o `.py` diretamente — nunca o caminho nu que
a produção usa. Um gate morto e um gate que permite são indistinguíveis do lado
de fora.

A tese que essa sessão me deixou, e que vale mais que qualquer um dos consertos:
**falso-verde não é um bug de teste. É uma família com cinco endereços
diferentes, e a suíte de testes ocupa só um deles.** Melhorar os testes conserta
um quinto do problema. Os outros quatro moram em lugares onde teste nenhum olha.

Chamo os cinco de **desconexão**, **wiring**, **adesivo**, **ordem** e
**silêncio** — nomes, não números, porque a numeração é a parte que eu espero
que envelheça primeiro.

## Modo 1 — desconexão: a lógica está desconectada do teste

O caso clássico, e o único que a literatura de testes cobre bem: o teste
exercita um caminho que a produção não usa. Você prova que a função decide
certo; a produção chama outra função. É o mais fácil de achar — mutation testing
o pega. Cito ele só para marcar o contraste com os quatro seguintes, que nenhum
mutante pega.

## Modo 2 — wiring: o arquivo está presente, a ativação não

É o caso dos hooks 644. A lógica está ligada ao teste. O teste está ligado à
lógica. Ninguém está ligado ao harness.

O conserto foi uma suíte nova, `test-hooks-wiring.py`, que faz uma pergunta que
nenhuma outra fazia: ela lê o `settings.json`, resolve cada `command` declarado
e exige que o arquivo exista **e** tenha bit de execução quando é invocado pelo
caminho nu. Negativo plantado: `chmod -x` reprova 1 de 20 casos.

O que me convenceu de que isso era uma classe, e não um acidente, foi o mesmo
modo reaparecer numa forma completamente diferente algumas horas depois. O vault
tem um `pre-commit` que barra blob acima de 95 MB — escrito depois de um
incidente em que 1,1 GB de evidência inválida entrou no repo. O hook está
versionado, viaja com o clone. A **ativação** dele é `core.hooksPath`, que é
config local e não viaja com nada.

Um clone novo, ou um worktree criado em `.claude/worktrees/`, roda sem gate de
tamanho nenhum. E não avisa. Arquivo presente, wiring ausente: exatamente a
mesma forma do `.sh` commitado 644, num mecanismo que não tem nada a ver com
permissão de arquivo. A suíte de wiring virou o lugar onde isso mora agora, com
`git config --unset core.hooksPath` como negativo plantado.

Vale olhar os dois negativos lado a lado, porque é aí que a classe aparece:

```
chmod -x hooks/block-dangerous-git.sh      # arquivo presente, execução ausente
git config --unset core.hooksPath          # arquivo presente, ativação ausente
```

São o mesmo predicado — *o artefato existe, o mecanismo que o liga ao sistema
não* — expresso em dois mecanismos que não têm nada em comum: um é bit de
permissão no inode, o outro é uma chave de config local. Nenhum teste da lógica
do hook distingue os dois estados, porque em ambos a lógica está perfeita e
nunca é chamada. É por isso que wiring é uma classe e não dois acidentes.

## Modo 3 — adesivo: o contador não conta

`test-hooks-critical.py` reportava `20/20`. Sempre verde, por construção.

O bug era banal — uma variável de acumulação sobrescrita, `total = ok +
ok_count_local` somando a mesma parcela duas vezes — e o efeito era que os 20
eram na verdade 2×10, e os 23 casos de outro bloco simplesmente não entravam na
conta. O número real era 33.

O que interessa não é o bug, é o formato. **`{total}/{total}` não consegue
mostrar discrepância.** Não existe estado do mundo em que aquela string apareça
diferente de si mesma. Um relatório que só sabe imprimir sucesso não é um
relatório; é um adesivo.

A regra que saiu daí: nenhum verificador imprime `N/N`. Ele declara um
`EXPECTED` e compara. Se divergir, diverge alto.

E quando o número *deve* mudar — você adicionou um caso legítimo —, a correção é
editar o `EXPECTED` no mesmo commit que adiciona o caso. Isso não é burocracia:
**o diff do `EXPECTED` é o review. O `N/N` não tem diff.** Um número que muda de
20 para 21 aparece no patch e alguém pergunta qual caso entrou; um `{total}` que
passa de 20 para 21 não deixa rastro nenhum, porque a linha do código-fonte é
idêntica antes e depois.

## Modo 4 — ordem: a mensagem afirma o que o código nunca checou

Meu `bash_read_gate` tinha um ramo para comando encadeado cuja mensagem de deny
dizia, textualmente, "chained command with a large read". O ramo negava
incondicionalmente. Ele nunca tinha olhado se havia leitura alguma.

A telemetria de preview mostrava 8 denies registrados. Os oito eram comandos sem
leitura nenhuma: `git status && echo`, `sed -i`, `python3 x.py`, `wc -l`. **8 de
8 falso-positivo.** Se eu tivesse promovido esse gate de preview para enforce,
ele teria negado quase todo comando composto que eu digito, com uma mensagem
explicando um motivo que ele não tinha verificado.

E aqui está o detalhe que mudou meu modelo mental: a heurística de "o que é uma
leitura grande" estava certa. O defeito era **ordem de decisão** — o gate
decidia antes de detectar. Nenhuma quantidade de tuning na heurística ia
consertar isso, e nenhuma suíte que testasse a heurística ia encontrar. A suíte
antiga passava 11 de 11 sem tocar no defeito.

Depois do conserto, a detecção de leitura roda primeiro e uma única definição de
"lê grande" serve aos dois ramos. Três casos novos. Reintroduzindo o
deny-antes-de-detectar, dois deles reprovam.

## Modo 5 — silêncio: o verificador foi silenciado

Este é o mais barato de introduzir e o mais caro de descobrir: `2>/dev/null`.

O caso que me curou é constrangedor. Eu precisava saber se havia atividade de
sessão fora do vault, e rodei um `find` sobre diretórios cujo nome começa com
`-`. O `find` interpretou o nome como flag, morreu, e o `2>/dev/null` comeu o
erro. Saída: vazia. Eu li "zero sessões" e quase entreguei "zero atividade fora
do vault, logo é seguro" como evidência de uma decisão.

O defeito não estava no código sob análise. Estava na **evidência**. Um comando
que falha em silêncio e um comando que retorna conjunto vazio produzem o mesmo
stdout, e a diferença entre eles é a diferença entre "verifiquei" e "não
verifiquei".

Virou regra dura no vault: nenhum verificador usa `2>/dev/null`. O mesmo padrão
apareceu numa rotina de backup, onde ele escondia falha de staging — a rotina
reportava sucesso enquanto arquivos não entravam no commit.

## O que não funciona: rodar a suíte de novo

Esse é o resultado que eu queria ter aprendido mais barato.

**Nenhum dos defeitos desta sessão foi encontrado rodando testes.** Todos foram
encontrados abrindo o arquivo. Cada um deles estava, por definição, atrás de uma
suíte verde — é isso que "falso-verde" quer dizer. Rodar de novo produz o mesmo
verde com mais confiança acumulada, que é estritamente pior que não rodar.

O que funciona é o contrato que hoje é invariante no meu `CLAUDE.md`: **um gate
só conta quando um negativo plantado reprova.** Reintroduza o defeito, veja
falhar, restaure, veja passar. Se você não consegue fazer a suíte ficar
vermelha de propósito, você não sabe se ela é capaz de ficar vermelha.

Dois exemplos de como esse contrato pega coisa que nenhuma outra prática pega.

O primeiro: eu escrevi, com minhas mãos, o contrato de teste de um wrapper
global. Documentei "`rc=2` → bloqueia". O `.py` nunca sai com 2. BLOCK é
sinalizado por **stdout não-vazio com rc 0**; o rc só distingue "o script rodou"
de "o script não rodou". Um wrapper implementado fielmente ao meu texto trataria
todo comando destrutivo como allow — fail-open silencioso, pior que não ter
wrapper, porque agora existe um documento afirmando que há proteção. O erro
estava na especificação, e só apareceu quando rodei o `.py` na mão para ver o
que ele de fato imprime.

O segundo: um caso de teste desse mesmo wrapper checava `"degradad" in stderr`.
Só que a própria linha de BLOCK do modo degradado contém a palavra "degradado".
Um wrapper que nunca avisa no caminho de *allow* passava. Plantado e confirmado:
a variante com o aviso removido saiu 7/7 verde. O negativo não reprovou — o
teste do teste falhou.

## O verificador que apagava a própria evidência

Duas descobertas laterais que valem por si.

A primeira é a mais desconfortável da sessão. `test-hooks-bash-read.py` fazia
`unlink()` no `hook-preview.jsonl` **de produção** e escrevia por cima. Toda
execução verde da suíte destruía a telemetria em que a análise se apoiava. As
linhas que eu vinha citando como evidência estavam sendo apagadas por mim mesmo,
a cada rodada. Provado plantando três sentinelas antes de rodar: antes, 4 linhas
com 3 sentinelas; depois da suíte verde, 1 linha e 0 sentinelas.

A segunda parece pequena até você ver o que ela abre. `shlex.split` cola o
operador de shell no token anterior quando não há espaço:
`git checkout .; ls` vira `['checkout', '.;', 'ls']`. Consequência: nenhum
consumidor enxerga o fim do comando. O parser de git arrastava argumentos do
comando seguinte, e o gate de operação destrutiva lia `ls; rm -r dir` como um
segmento único — nunca via o `rm`. Um caractere sem espaço em volta, e um gate
de destruição fica cego. Corrigido na raiz, num tokenizador compartilhado:

```python
lex = shlex.shlex(command or "", posix=True, punctuation_chars=True)
lex.whitespace_split = True
```

Um lugar, três consumidores, dois negativos plantados (`;` e `&&` colados) que
reprovam se eu voltar para `shlex.split`.

## O que isso custa

Custa mais que testar. Um negativo plantado é trabalho manual: editar o arquivo
de produção, rodar, ler a saída, restaurar, rodar de novo. Não dá para
automatizar sem construir um framework de mutação, e um framework de mutação tem
os mesmos cinco modos de falha que tudo aqui.

Também custa em falso-alarme: exigir `EXPECTED` em vez de `N/N` faz a suíte
divergir quando você adiciona um caso legítimo, e o número tem que ser
atualizado à mão. É o preço de ter um número capaz de estar errado.

## O fecho: o modo sobreviveu à sessão que o catalogou

No mesmo dia em que fechei essa taxonomia, deleguei uma limpeza: triar 13
worktrees do repo e dizer o que havia de conteúdo único neles. O relatório veio
confiante, com a maioria classificada como ruído puro. O método da triagem foi
`git diff`.

`git diff` não mostra arquivo não rastreado.

Havia arquivos staged e nunca commitados dentro de um dos worktrees — dois deles
testes reais, com `git log --all` retornando zero para os caminhos. Morreriam no
`worktree remove`, e o relatório teria continuado correto por construção, porque
só sabia enxergar o que o `git diff` mostra. Estão em quarentena hoje.

Isso é o modo 5 numa roupa nova. Não havia `2>/dev/null` em lugar nenhum: a
supressão estava embutida na escolha da ferramenta. Um verificador que não olha
para uma categoria inteira de estado reporta ausência com a mesma cara com que
reportaria vazio.

A conclusão que eu não queria: catalogar os cinco modos não me imunizou contra o
quinto, no mesmo dia, com o mesmo tipo de confiança. A taxonomia não é uma
vacina. É uma lista de perguntas para fazer antes de acreditar num verde — e
fazer a lista não é o mesmo que consultá-la.

## O que ainda não sei

Não sei se cinco é o número certo, ou se o modo 5 é só um guarda-chuva grande
demais ("o verificador não olhou") que vai se partir em três assim que eu tiver
mais casos. Não sei como pegar o modo 2 sem escrever um verificador por
mecanismo de wiring — hoje tenho um para `settings.json` e um para
`core.hooksPath`, e nenhuma ideia geral de como enumerar os outros. E não medi o
custo real do negativo plantado: sei que é caro em minutos, não sei se é caro o
bastante para eu parar de fazer quando ninguém estiver olhando.
