---
date: "2026-09-01"
description: "Um eval que nunca reprovou não mede nada. Plantei negativos em dois evals que rodavam verdes há semanas e achei cinco defeitos — nenhum era bug na lógica do sistema avaliado."
tags: ["agentes", "evals", "harness", "testes", "falso-verde"]
slug: "o-denominador-mente"
title: "O denominador mente: cinco defeitos que passaram verdes"
draft: false
summary: "Um eval que nunca reprovou não mede nada. Plantei negativos em dois evals que rodavam verdes há semanas e achei cinco defeitos — nenhum era bug na lógica do sistema avaliado."
cover:
  image: "/og/o-denominador-mente.png"
  alt: "O denominador mente: cinco defeitos que passaram verdes"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
# O denominador mente: cinco defeitos que passaram verdes

Um eval que nunca reprovou não mede nada. Isso soa óbvio escrito assim, e mesmo assim eu mantive dois evals rodando verdes por semanas sem nunca ter checado se eles eram capazes de reprovar. Quando finalmente plantei negativos, achei cinco defeitos. Nenhum era bug na lógica do sistema que estava sendo avaliado. Os bugs estavam no avaliador. Todos os cinco eram defeitos na **medição** — e quatro deles tinham a mesma forma: o denominador estava errado.

O caso concreto: dois scripts no meu vault, `eval-f1-corpus.py` e `eval-memory-retrieval.py`. Ambos rodavam, imprimiam número, saíam com exit 0. Ambos estavam quebrados de um jeito que nenhuma execução verde revelaria.

## O problema: verde não é evidência

Um gate tem dois estados que se parecem de fora. Ele pode estar passando porque o sistema está correto, ou passando porque ele perdeu a capacidade de reprovar. A saída é idêntica: exit 0.

A única forma de distinguir é sabotar o sistema de propósito e exigir que o gate reprove. Eu chamo isso de negativo plantado, e a regra que uso é: **um gate só conta depois de ter reprovado um negativo plantado**. Antes disso ele é decoração com exit code.

Isso já estava escrito na constituição do meu vault desde maio. O que eu não tinha feito era aplicar a regra aos evals que mediam o resto — os medidores não estavam sendo medidos.

## O que tentei antes: contar

A primeira coisa que fiz foi errada, e vale mais que o conserto.

Duas skills do vault carregavam esta instrução em prosa:

```
hill-climb:          NUNCA remova um probe existente para fazer o rate subir
complexity-ratchet:  NUNCA remova um teste existente para subir a coverage
```

Duas regras corretas, escritas, e sem nenhum verificador. Então escrevi uma catraca: um script que conta probes declarados por arquivo e compara contra um baseline versionado. Encolher exige atualizar o baseline no mesmo commit, o que torna a remoção visível em code review em vez de silenciosa.

Rodei: 57 arquivos, 840 probes, verde. Plantei um negativo — renomeei um caso de teste real para que ele deixasse de ser coletado:

```
ENCOLHEU  test-eval-action-gate.py  7 -> 6
```

Funcionou. Mas ao escrever os plantados da própria catraca, escrevi um caso que afirmava que os arquivos `eval-*.py` deviam aparecer no baseline de contagem. Ele reprovou. Minha reação inicial foi alargar a catraca até o caso passar.

Isso teria sido o erro exato que a catraca existe para impedir. Fui checar: os `eval-*.py` não declaram função de probe nenhuma, por desenho. A população deles é corpus e cenário, e é guardada por outros testes. Meu caso plantado afirmava uma forma que aqueles arquivos nunca tiveram.

O conserto foi reescrever o caso para o invariante verdadeiro — que todo `eval-*.py` tenha um teste plantado pareado — em vez de mexer no medidor até ele concordar comigo. E foi esse caso reescrito que expôs o buraco real: dois evals sem par.

## A solução: plantar antes de acreditar

Escrevi plantados para os dois órfãos. Cada defeito abaixo foi achado assim: eu escrevia o caso que *deveria* reprovar, ele passava quando não devia, e ao investigar por que, o defeito aparecia.

### Defeito 1 — o alvo usava o denominador errado

`eval-f1-corpus.py` — F1 é a fase de triagem do pipeline, não a métrica F1-score — compara predições de triagem contra rótulos reais e declara se a meta foi atingida. A meta: ≥90% de acurácia em N=200.

O código comparava contra `sample_size` — o tamanho do sorteio — e não contra `matched`, o número de predições que efetivamente casaram com a amostra. Consequência medida:

```
Exact-match accuracy: 1/1 = 100.0%
Alvo SMART: >=90% em N=200. ATINGIDO
```

Uma predição. Uma. O sorteio tinha 200 itens, então `sample_size >= 200` era verdade, e a meta aparecia como batida com uma amostra efetiva de um único arquivo.

### Defeito 2 — a meta ficava abaixo do chute

Este é o mais desconfortável, porque o número estava certo e a meta é que era inútil.

O corpus tem 7.471 arquivos rotulados: 7.241 `approved`, 229 `disapproved`. Chutar sempre "approved", sem olhar para nada, acerta 96,9%. A meta era 90%.

Um classificador que ignora completamente o conteúdo bateria a meta com folga. O alvo não media classificação — media desbalanceamento do corpus.

Corrigi exigindo acurácia acima da classe majoritária. Rodei o plantado do chute constante. **Ainda passou.** A amostra sorteada de 200 tinha 98% de approved contra 96,9% do corpus inteiro, então o chute batia a baseline global.

A comparação só é honesta contra a maioria do **mesmo conjunto** em que a acurácia foi calculada. Comparar com a estatística do corpus inteiro é misturar duas populações — e o vencedor dessa mistura é sempre o chute.

Adicionei também recall da classe minoritária ao relatório. Num corpus 7241/229, acurácia agregada esconde exatamente a classe que importa: acertar 0% dos `disapproved` custa 3,1 pontos de acurácia agregada, porque essa classe representa apenas 3,1% do corpus — dentro do ruído de qualquer amostra de 200.

### Defeito 3 — 109 arquivos fora da medição, em silêncio

O parser lia `decision:` do frontmatter com uma regex que capturava o valor cru. Onde o YAML trazia `decision: "approved"` com aspas, o rótulo virava a string `"approved"` — com as aspas dentro — e caía num balde chamado "outro/inesperado".

São 109 de 7.471 arquivos. Eles nunca casariam com uma predição `approved`.

A parte que importa: **a população reportada continuava 7.471**. O número grande no topo do relatório estava certo. O número que entrava na conta era menor, e nada no output dizia isso.

### Defeito 4 — `--seed` não era reprodutível

O script sorteia a amostra com `random.Random(seed).sample(paths, N)`, e `paths` vinha da ordem de inserção de um dicionário populado por `rglob`. Ou seja: a ordem do filesystem.

`--seed 42` dava amostras diferentes em máquinas diferentes, e diferentes na mesma máquina depois de qualquer arquivo novo entrar no corpus. Seed sem ordem canônica não é reprodutibilidade; é a aparência dela.

Descobri isso porque meu plantado passava 200 predições e o eval reportava 8 casadas. Meu teste ordenava os paths; o eval não.

### Defeito 5 — o cenário negativo não reprovava

Este é do outro eval, `eval-memory-retrieval.py`, que testa um retriever de memória. A propriedade central: entrada com `valid_until` vencido nunca volta, e a flag `--fresh` corta entradas velhas por data.

Plantei duas sabotagens no retriever real. Remover o filtro de `valid_until` reprovou, como esperado. Remover o filtro de `--fresh` **não reprovou**.

A causa: os cenários que testam corte esperam zero resultado. O eval comparava `len(relevant) != len(expected)`. Com zero esperado e o corte desativado, o retriever devolvia cinco resultados, mas nenhum deles estava na lista de esperados, então `len(relevant)` era zero, `len(expected)` era zero, e os dois batiam.

Os resultados indevidos eram contados numa variável `fp` somada a cada cenário: esse acumulador nunca participava da condição de falha.

Cenário negativo que não reprova quando o corte some é cenário decorativo. Um dos dois cenários da dupla `--fresh` estava medindo nada.

## O padrão

Quatro dos cinco defeitos são o mesmo mecanismo: **a população medida encolheu, e o número não disse**.

Acurácia sobe quando o denominador cai. Cobertura sobe quando o teste sai. Taxa de erro cai quando a varredura para de enxergar arquivo. Em todos os casos o output fica melhor, e a melhora é a medição escapando, não o sistema consertando.

Isso torna o falso-verde por denominador especialmente difícil de pegar por leitura de código: nada está errado localmente. A divisão está correta. A regex funciona. O `rglob` faz o que promete. O erro é a relação entre o que foi contado e o que foi afirmado — e essa relação não aparece em nenhuma linha, ela aparece na diferença entre duas.

O único detector que conheço para isso é a sabotagem. Você quebra a coisa de propósito e exige que o número mude. Se ele não muda, o número nunca esteve olhando para lá.

## Trade-off

Isso custa. Três coisas, concretamente.

**Plantar é mais caro que testar.** Um teste comum afirma que a saída certa acontece. Um plantado precisa modificar o artefato real no disco, rodar o sistema inteiro, verificar a mudança de veredito, e restaurar o arquivo num `finally` — porque uma falha no meio deixa o repositório sabotado.

Plantar num mock não vale: mediria a lógica de comparação do próprio teste. Foi o erro que cometi numa versão anterior e que só apareceu porque o mock passava enquanto o artefato real não passaria.

**Baseline de regressão adia decisão.** Quando achei os dois evals sem par, o conserto era fora do escopo daquela rodada. Registrei os dois numa lista de exceção datada, com um guard próprio impedindo a lista de crescer. Isso mantém o gate honesto, mas cria uma dívida com nome e sem prazo. Se a lista virar hábito, ela é o novo lugar onde as coisas se escondem.

**Custa aceitar que a métrica estava mentindo.** O `eval-f1-corpus` já tinha reportado meta atingida antes. Aquele relatório era falso, e não há como saber quantas decisões passaram por ele. Consertar o medidor invalida o histórico dele — e essa é a parte que dá vontade de não olhar.

## O que ainda não sei

Não sei quanto disso generaliza. Meu corpus é um vault pessoal, os plantados são meus, e cinco defeitos em dois scripts é uma amostra pequena demais para virar taxa. Suspeito que a proporção — quatro de cinco defeitos sendo de denominador e não de lógica — seja alta demais para ser coincidência, mas não testei em nenhum outro repositório.

Também não sei onde parar. A catraca protege as contagens de probe, mas quem protege a catraca é outro plantado, e quem protege esse é ninguém. A regressão é infinita e em algum ponto ela tem que terminar num teste que alguém leu com atenção e resolveu confiar. Não tenho critério para dizer onde esse ponto deve ficar; escolhi um por instinto.

E não sei se a lista de exceção datada é solução ou adiamento com boa aparência. Ela tem guard, tem data, e não pode crescer. Mas essas três propriedades também descrevem um débito que nunca vence.
