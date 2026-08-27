---
tags: ["ai-agents", "testes", "observabilidade", "postmortem", "gates"]
description: "Treze instâncias, em um só sistema, de um check ficar verde sem provar nada — e o mecanismo por trás de cada uma. A pior foi a regra que eu mesmo escrevi para consertar as outras: ela nasceu com zero violações porque o único violador tinha perdido a capacidade de ser avaliado."
slug: "o-gate-mede-o-lado-que-nao-quebrou"
title: "O gate mede o lado que não quebrou"
date: "2026-08-26T21:48:26-04:00"
draft: false
summary: "Treze instâncias, em um só sistema, de um check ficar verde sem provar nada — e o mecanismo por trás de cada uma. A pior foi a regra que eu mesmo escrevi para consertar as outras: ela nasceu com zero violações porque o único violador tinha perdido a capacidade de ser avaliado."
cover:
  image: "/og/o-gate-mede-o-lado-que-nao-quebrou.png"
  alt: "O gate mede o lado que não quebrou"
  relative: false
  hiddenInList: true
  hiddenInSingle: true
ShowToc: true
TocOpen: false
---
Um gate verde não prova que não há defeito. Prova que o defeito não estava naquilo que ele mediu — e é nessa diferença que mora quase tudo.

Isso soa óbvio escrito assim. Não é. Gastei um dia atrás de um defeito específico: declarações de roteamento no lugar errado. Pins de modelo lidos por ninguém, ou em conflito com a política canônica do sistema. Achei o que procurava — e, no caminho, treze instâncias em que um check ficava verde sem provar nada. Todas com commit e código.

A que mais me incomodou foi a última: eu escrevi uma regra nova de gate, ela nasceu com zero violações em dado real, e por um instante li aquilo como sucesso.

## O problema não é errar o veredito

Se um gate desse o veredito errado, eu descobriria rápido. O modo de falha real é outro: o gate acerta o veredito — mas sobre a população errada.

São treze instâncias distintas, e eu as agrupei em oito mecanismos — vários aparecem mais de uma vez, com roupas diferentes. Vou pelos mecanismos, não pelas instâncias; a divisão em oito é minha, e não a testei.

**Vocabulário fechado.** Um check procurava pin de modelo numa lista literal: `{"model", "model_pin", "pinned_model", "runtime_model"}`. Bastava inventar um sufixo para sair do gate, e alguém inventou: `model-hint` passou em dezesseis arquivos. Enumeração é uma aposta de que você previu todos os nomes que alguém escreveria. Você não previu. O conserto foi trocar a lista por padrão:

```python
MODEL_PIN_KEY_RE = re.compile(
    r"^(?:[a-z0-9]+[-_])?model(?:[-_][a-z0-9]+)?$"
    r"|^(?:[a-z0-9]+[-_])effort(?:[-_][a-z0-9]+)?$"
    r"|^effort[-_][a-z0-9]+$",
    re.IGNORECASE,
)
```

**População parcial.** Os checks de agente varriam um diretório só. Os agentes que moravam fora dele nunca foram medidos, e o relatório não dizia "não medi" — dizia zero.

O caso mais fino dessa família foi o último a aparecer. Um arquivo declara `kind: reference` e `type: "agent"` ao mesmo tempo, e guarda a rota num campo aninhado, `route.profile`, em vez do `model-profile:` de topo que todo mundo usa. A população filtrava por `kind`. O arquivo se declarava agente pelo outro campo. Resultado: invisível para todos os checks de roteamento, citando três modelos diferentes no corpo, e indistinguível de um arquivo em conformidade — porque *conformidade* e *não medido* produzem exatamente o mesmo silêncio.

**Denominador que encolhe.** Este é o mais perigoso porque parece progresso. Havia uma allowlist com dez entradas isentando arquivos do gate de pin. A justificativa estava no comentário, escrita onze dias antes: "reflete o espelhamento real (verificado 2026-08-18: 25 arquivos)". Fui olhar. Eram quatro. As outras seis isentavam pin que runtime nenhum lia.

Removi as seis. O check `AGENT_PIN_ALLOWLIST_DEAD_SYMLINK` foi para zero.

Zero symlink foi criado. Três das seis referências continuam mortas, com rotina ativa apontando para elas. Para as outras três, que ninguém invoca, tirar a isenção era mesmo o conserto — não havia symlink a criar. A conta não distingue os dois casos: amputação legítima e amputação disfarçada somam igual. Se eu tivesse escrito "resolvido, 0 achados" naquele momento, teria sido tecnicamente verdade e completamente falso.

A versão mais fina desse mecanismo não estava no sistema auditado. Estava no instrumento que eu usava para medir a auditoria.

O hook que registra economia de sessão grava um único `reason_code` por linha. Dez campos podem faltar; o código carimba o mesmo código para qualquer um deles, e o comentário admite:

```python
for field, code in RTK_REASON.items():
    if record.get(field) is None:
        reason_code = code  # any rtk miss marks the line; code is uniform
```

Os dez campos vêm da mesma ferramenta externa. Quando ela não está disponível no ambiente do hook, faltam todos juntos, e a linha sai com o carimbo único. Nas 126 linhas do log: setenta sem motivo, cinquenta e seis com o mesmo motivo, e o corte entre as duas metades é uma data — o dia em que o bloco entrou. Não é uma constante desde sempre. É uma constante desde anteontem, o que eu só soube depois de abrir o arquivo em vez de descrever o que lembrava dele.

O alarme que consome esse log é pior que o log. Ele deveria disparar quando mais de 20% da sessão tem motivo declarado:

```python
last_econ = economy[-1] if economy else {}
reason_rate = 1.0 if last_econ.get("reason_code") else 0.0
...
if reason_rate > 0.2:
```

Não existe percentual. `reason_rate` lê um registro — o último — e assume 0 ou 1. O `> 0.2` tem cara de limiar calibrado e é um `is not None` fantasiado: nenhum valor intermediário é alcançável, então o número 20% nunca participou de decisão nenhuma.

Foi por isso que abandonei a formulação que me ocorreu primeiro, "a métrica não tem denominador". O defeito é mais específico e pior: o suposto percentual é derivado de uma linha só, e o valor não distingue *a ferramenta não estava lá* de *houve um motivo real*. Um indicador que só assume dois valores não é um indicador ruim. É um enfeite com aparência de instrumento, e eu confiei nele o tempo inteiro.

**Severidade que anula a detecção.** Um check detectava a divergência corretamente e reportava com `severity="warning"`, num runner cujo exit code lê exatamente esse campo. Ele funcionava perfeitamente e devolvia `EXIT=0`: um agente podia declarar perfil desconhecido e o gate passava verde. Virei para blocking, e o passivo era zero no dia da virada — não havia débito legítimo sendo tolerado. A tolerância só protegia defeito futuro.

**Silêncio como sucesso.** Um `except` retornando lista vazia em vez de finding: quebrei o import de propósito, a rota inteira retornou zero achados e o gate ficou verde. E um scanner de rotas mortas cujo laço lia `d.get('agents', d.get('entries', []))` de um JSON cuja lista se chama `items` — nunca iterou nada, desde o dia em que foi escrito. Um no-op silencioso não se distingue de um sucesso: os dois produzem a mesma saída.

**Premissa expirada.** Uma docstring justificava uma tolerância com uma contagem de passivo que já não valia. O comentário da allowlist datava sua própria verificação e ninguém releu a data. Comentário não apodrece com barulho — ele fica ali, plausível, sustentando uma isenção que já perdeu o motivo.

**Auto-referência.** Uma contagem de invocadores somava a própria declaração de trigger do arquivo: todo agente tinha pelo menos um "invocador", ele mesmo. E, mais tarde, um registro gerado — compilado a partir dos frontmatters — foi promovido a fonte de autoridade sobre o estado daqueles mesmos frontmatters. Perguntar ao derivado se o original está certo é um círculo, não uma medição.

**Efeito colateral no teste.** Um teste criava um sentinel de push real como efeito colateral de rodar. O teste passava. Ele também destravava a trava que existia para me proteger.

## Três eixos que eu confundi o tempo todo

Metade dos meus próprios erros veio de tratar como uma pergunta o que eram três:

1. **O arquivo existe em disco?**
2. **O runtime o despacha?** (no meu caso: existe symlink em `~/.claude/agents`?)
3. **Alguém o cita por nome num documento?**

Eu media um eixo e concluía sobre outro, nas duas direções.

Marquei um agente como "morto" porque não tinha symlink — e ele era invocado por uma rotina agendada, como procedure lida por nome, coisa que nunca precisou de symlink. Depois, sobre o mesmo arquivo, li as sete citações que encontrei como prova de uso. Uma era a declaração de trigger dele mesmo. Das seis restantes, metade despacha e metade só o menciona num índice. Nas duas vezes eu tinha o número certo e a pergunta errada.

O teste que resolveu foi contar. A sintaxe `@nome` aparece em mais de trinta tokens distintos em arquivos ativos; quatro deles têm symlink. Um único nome aparece setenta vezes em trinta arquivos e nunca teve symlink — não são trinta arquivos quebrados, é uma procedure carregada por nome. Só que os quatro com symlink também aparecem como `@nome`. O token carrega os dois sentidos ao mesmo tempo, e nenhum gate que leia só o token distingue um do outro. Eu estava prestes a escrever um que produziria trinta falsos positivos e seria desligado na primeira rodada — não por medir errado, mas por medir o eixo que não estava no texto que eu mandei ele ler.

## O que eu tentei antes

**Confiar nos relatórios.** Boa parte da execução mecânica foi delegada. Os relatórios voltavam verdes. Oito vezes o verde não sobreviveu à verificação: um dizia "0 achados" enquanto o check tinha três erros; outro dizia "cobertura 9/9" com um décimo código bloqueante não registrado no denominador; outro declarava inconclusivo sobre um estado externo que estava snapshotado dentro do próprio repositório desde sempre. Relatório de agente é *claim*, não evidência. Isso vale para os meus também.

**Contar as coisas.** Tentei reconciliar uma mudança grande por contagem de edições e falhei — meu número não batia com o reportado. O que fechou a questão foi uma pergunta binária e direta: *todos os caminhos obsoletos foram editados depois deste commit?* Sim. Conclusão idêntica, métrica diferente. Quando a contagem briga com você, troque a contagem pela pergunta que você realmente quer responder.

**Rodar o gate para ver se passa.** É o pior de todos e é o mais natural. Rodar o gate mede o gate contra o mundo como ele está, e o mundo como está é justamente onde o defeito não aparece — senão você já o teria visto.

## O que funciona

**Negativo plantado pareado.** Plante o defeito *e* o caso legítimo. Se o gate dispara nos dois, ele não discrimina; ele só faz barulho. Fazer isso me pegou duas vezes: a primeira planta não disparou porque o arquivo estava na allowlist e eu quase li o silêncio como resultado; a segunda não disparou porque o arquivo não tinha o campo que meu padrão exigia. Só a terceira valeu. Um gate que nunca foi testado contra um negativo plantado não é um gate, é um enfeite.

**Mutação nos testes.** Reverta a mudança de produção e confirme que as asserções específicas morrem. Encontrei uma linha de produção que mutação nenhuma matava — ela isentava um termo que o padrão já excluía sozinho. Linha que nenhuma mutação mata é linha não testada. Removi.

**Nunca aceitar "0 X" sozinho.** Antes de fechar qualquer coisa com um zero, três perguntas:

- Qual era o tamanho da população antes e depois?
- Existe um negativo plantado que ainda dispara?
- Qual eixo foi medido, exatamente?

A primeira é a que mais dói. Quase todo conserto de gate encolhe a população de alguma forma — remover isenção morta, apertar filtro, tirar arquivo do escopo. Consertar o defeito e amputar a população produzem exatamente o mesmo número, e só a contagem antes/depois separa os dois.

## A instância que eu mesmo criei

No fim do dia escrevi uma regra nova: nenhum arquivo pode citar no corpo um modelo mais caro que o perfil declarado no frontmatter. Havia exatamente um violador conhecido — perfil `economy`, corpo citando o modelo mais caro duas vezes.

Rodei. Zero violações.

O motivo: horas antes, numa limpeza legítima de pins mortos, eu tinha removido o `model-profile: economy` daquele arquivo. O corpo continuava citando o modelo caro. O que sumiu foi a *declaração* que provava a contradição, não a contradição. A regra ficou verde porque o arquivo perdeu a capacidade de ser avaliado.

Ela só não nasceu morta porque, antes de escrevê-la, eu tinha exigido que arquivo com pin no corpo e nenhum perfil resolvível emitisse um achado explícito de **não-avaliável**, em vez de passar calado. Foi esse achado que apareceu. Foi a única coisa entre a regra e uma vida inteira de zeros.

A décima terceira instância apareceu enquanto eu revisava este texto.

Fui conferir um número do rascunho — quantas vezes um certo nome aparecia no vault — e o comando voltou `0 ocorrências`. Aspas faltando: o shell comeu o filtro de arquivos antes do `grep` ver. Rodei de novo, com aspas: setenta. Minutos depois, o linter de voz reportou `0 erros` sobre este mesmo artigo, porque a variável com o caminho estava vazia e ele havia julgado zero arquivos.

Dois zeros, com dez minutos de intervalo, verificando um texto sobre confundir zero-por-ausência com zero-por-instrumento-quebrado. Nos dois casos o comando saiu com sucesso. Nos dois casos a saída era plausível. O que me salvou não foi rigor: foi eu conhecer o número esperado no primeiro caso, e o segundo relatório trazer o campo `files_judged` ao lado do zero. Um número junto do denominador. Foi só isso.

Se há uma única lição operacional aqui, é essa: **todo gate precisa de um terceiro estado.** Passou, falhou, e *não consegui medir*. Sem o terceiro, ele não desaparece — ele colapsa no primeiro. O que não pôde ser medido passa a ser reportado como aprovado, e o silêncio de um arquivo em conformidade fica idêntico ao silêncio de um arquivo que ninguém olhou.

## O que isso custa

Muito. Verificar cada verde antes de aceitá-lo mais ou menos dobrou o tempo por correção. E boa parte do ganho veio de eu ter o repositório aberto e poder desconfiar de tudo — o que não escala para quem só recebe o relatório. Também produziu bastante trabalho que terminou em "não é isso": duas conclusões minhas foram refutadas por medição no meio do caminho, uma delas por um agente que eu tinha acabado de corrigir. Isso é saudável e é caro.

E o método tem um limite claro: ele encontra gates cegos. Não encontra o gate que ninguém escreveu.

## O que ainda não sei

Se os oito mecanismos são mesmo oito, ou três com variações — desconfio que "população errada", "denominador que encolhe" e "silêncio lido como sucesso" cubram quase tudo, mas não testei a redução.

Se a regra do denominador antes/depois pode ser automatizada. Suspeito que não: exige saber *por que* a população mudou, e isso parece julgamento, não contagem.

E se nada disto generaliza para além de um sistema pessoal, onde eu sou autor, operador e auditor ao mesmo tempo. Em CI de time, o incentivo para ler verde como pronto é maior, e a pessoa que verificaria costuma ser a que não escreveu o gate.
