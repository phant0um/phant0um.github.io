---
description: "Converter wikilink parece formatação. É controle de acesso: o link carrega o título da nota, e título de nota privada já é informação."
slug: "gate-de-privacidade-wikilink"
title: "Todo exportador de vault tem um vazamento de privacidade"
tags: ["pkm", "obsidian", "publishing", "privacidade"]
date: "2026-08-16T23:58:35-04:00"
draft: false
summary: "Converter wikilink parece formatação. É controle de acesso: o link carrega o título da nota, e título de nota privada já é informação."
ShowToc: true
TocOpen: false
---
Publiquei um blog essa semana e a parte que me tomou mais tempo não foi o tema,
o deploy nem o CI. Foi decidir o que fazer com `[[colchete duplo]]`.

A tese: converter wikilink não é formatação, é controle de acesso. O link
carrega o **título** da nota destino, e título de nota privada já é informação.
"Vou escrever sobre X" e "não vou escrever sobre X" são fatos diferentes sobre
mim, e o segundo vaza pelo primeiro se eu deixar.

Isso soa exagerado até você olhar o que os exportadores fazem por padrão.

## O problema

Num vault, `[[nota]]` resolve porque existe um índice local. Fora dele, não
existe índice nenhum. O exportador precisa decidir, por link, entre quatro
saídas:

1. virar link para um post publicado
2. virar texto puro
3. virar link quebrado
4. recusar a conversão e devolver o problema para o autor

A saída 3 é a que a maioria produz, e é a pior de todas. Um link para
`/notas/terapia-2024` num artigo sobre Kubernetes não é um 404: é um anúncio.
O leitor vê o título no texto do link, vê a URL na barra de status ao passar o
mouse, e ambos vazam antes de qualquer clique. O 404 é o que acontece *depois*
de a informação já ter saído.

Meu vault tem nota sobre saúde, sobre dinheiro, sobre pessoas. Nenhuma delas vai
para um blog público. Mas todas são linkáveis de dentro de um rascunho, porque é
exatamente para isso que o vault serve: eu ligo o que penso ao que já pensei. O
artigo nasce enredado no material privado, por construção.

O caso que me convenceu foi banal. Escrevendo o rascunho deste texto, linkei
`[[nota-privada]]` só para testar. Se o conversor tivesse default aberto, ela
sairia como link no HTML final. Ninguém teria revisado, porque o build passa e
o site sobe verde.

## O que tentei antes

**Um campo `publish: true` no frontmatter de cada nota.** Descartei: exige que
eu marque nota por nota, e o default de um campo ausente é ambíguo. Pior, ele
inverte o ônus. A pergunta certa não é "esta nota foi liberada?" e sim "esta
nota já está publicada?" A primeira é intenção, e intenção não é verificável no
momento da conversão. A segunda é fato observável.

**Uma lista de publicados no vault.** Descartei por um motivo específico: toda
lista paralela diverge do que ela descreve. Um post renomeado no repo, um
despublicado à mão, um slug alterado, e a lista continua afirmando o que era
verdade semana passada. Divergência silenciosa aqui não gera erro visível: gera
link para post que não existe, ou pior, permissão para linkar algo que saiu do
ar. O modo de falha é exatamente aquele que o gate deveria impedir.

**Deixar o LLM decidir caso a caso.** Descartei porque decisão de privacidade
com resultado probabilístico não é gate. Um gate que acerta 97% das vezes num
artigo com 30 links erra quase um por artigo, e o erro é irreversível: conteúdo
público é indexado. Regra checável mecanicamente pertence ao código, não ao
prompt.

## A solução: default fechado, verdade lida do artefato

Duas decisões, uma linha de código cada.

**Primeira: o conjunto de publicados é lido do repositório do site**, não de uma
declaração no vault. O site é o artefato que responde a pergunta "isto é
público?", porque é literalmente o que está servido:

```python
def published_slugs(out_repo: Path) -> dict[str, str]:
    posts = out_repo / "content" / "posts"
    out = {}
    for p in posts.glob("*.md"):
        fm, _, _ = split_fm(p.read_text(encoding="utf-8"))
        if str(fm.get("draft", "")).lower() == "true":
            continue
        slug = fm.get("slug") or p.stem
        out[p.stem] = f"/posts/{slug}/"
    return out
```

Se o post não está lá, ele não é público. Não há segunda opinião a consultar.

**Segunda: link é opt-in por evidência.** O alvo vira link se, e somente se,
estiver nesse conjunto.

Minha primeira versão degradava todo link não resolvido para texto puro, e eu
achei que estava resolvido. Um revisor apontou o buraco: **texto puro ainda
vaza o rótulo.** Para uma nota de saúde, de dinheiro ou sobre uma pessoa, o
nome da nota *é* o segredo. Trocar `[[terapia-2024]]` por `terapia-2024` não
protege nada — destila o título em vez de linkar, o que é o mesmo vazamento com
um passo a menos.

A correção separa dois casos que eu tinha juntado:

```python
url = pub.get(name) or pub.get(target)
if url:
    return f"[{label}]({url})"
if alias:
    # Alias é decisão editorial explícita: o autor já escolheu o texto
    # que vai a público, então degradar para ele não revela nada novo.
    warnings.append(f"wikilink '[[{target}|{alias}]]' -> texto puro")
    return label
# Sem alias, o rótulo seria o próprio nome da nota. Barra e força a escolha.
errors.append(f"wikilink '[[{target}]]' sem alias e sem alvo publicado: ...")
```

Com alias, o autor já decidiu o que o público lê, então degradar é seguro.
**Sem alias, o gate barra** e me obriga a escolher: dar um rótulo público ou
tirar a referência. O silêncio falha fechado.

E aí o mesmo revisor apontou o buraco seguinte, que é o preço de qualquer regra
que exige uma decisão humana: decisão exigida trinta vezes vira reflexo, e o
caminho mais curto para destravar o build é parafrasear o nome da nota.
`[[terapia-2024|terapia 2024]]` satisfaz a exigência de alias e vaza
exatamente aquilo que a exigência protege. Fica com aparência de deliberação,
que é pior que o vazamento cru, porque o gate agora atesta.

A defesa é comparar formas canônicas: sem acento, sem caixa, sem pontuação. Se
o alias é o nome do alvo reescrito — igual, contido nele, ou contendo ele — não
é rótulo, é paráfrase.

```python
def alias_leaks(alias: str, target: str) -> bool:
    a, t = norm(alias), norm(target)
    return a == t or a in t or t in a
```

Contenção nos dois sentidos porque tanto encurtar quanto enfeitar preserva o
segredo. `terapia` e `minhas anotações de terapia-2024` vazam o mesmo token.

Rodando nos quatro casos:

```
[[Por que este blog existe]]           ->  [Por que este blog existe](/posts/hello/)
[[financas|um registro interno]]       ->  um registro interno   (aviso)
[[terapia-2024]]                       ->  BLOQUEADO (sem alias)
[[terapia-2024|Terapia 2024]]          ->  BLOQUEADO (alias é paráfrase)
```

O primeiro resolveu porque o post existe no repo. O segundo saiu com o rótulo
que eu escolhi. Os dois últimos não saíram.

Isso é heurística sintática defendendo contra intenção, e heurística assim erra
para os dois lados: alias legítimo que por acaso repete uma palavra do nome vai
barrar. Aceitei o falso positivo porque o custo dele é reescrever meia frase, e
o custo do falso negativo é irreversível.

Estendi o mesmo princípio ao frontmatter, que tem o mesmo formato de risco.
Em vez de listar as chaves internas a remover, listei as que podem sair:

```python
HUGO_KEYS = {"title", "date", "description", "summary", "tags", "categories", "slug"}
```

Allowlist e denylist parecem intercambiáveis e não são. Com denylist, uma chave
nova no vault vaza para o site até alguém lembrar de bloqueá-la; o silêncio
falha para o lado aberto. Com allowlist, ela é descartada por omissão e o
silêncio falha para o lado fechado. A diferença só aparece no dia em que você
esqueceu, que é o único dia que importa.

## O trade-off

Isso custa algo real, e o custo cai sobre a escrita.

Como qualquer link para nota não publicada some, o parágrafo precisa fechar
sozinho. Não dá para escrever `como argumentei em [[X]]` e seguir adiante: na
saída vira "como argumentei em X", uma referência a lugar nenhum. O contexto
tem que estar no próprio artigo.

Descobri isso pelos avisos. O conversor não barra link não resolvido, só
reporta, e a primeira rodada cuspiu uma lista maior do que eu esperava. Cada
aviso era uma frase minha apoiada em algo que o leitor não pode ver.

Passei a tratar isso como sinal de qualidade, não como atrito. Artigo que
depende do meu grafo para fazer sentido é anotação, não artigo. O gate de
privacidade acabou funcionando como gate editorial, o que não era o objetivo.

O custo restante é chato: republicar um artigo antigo pode mudar links de
artigos novos, porque o conjunto de publicados cresceu. Aceitei porque a
alternativa é cache, e cache é a lista paralela de novo, com outro nome.

## O que ainda não sei

Se resolver por título, além de nome de arquivo, foi acerto. Dois posts com
títulos parecidos ainda não colidiram, mas nada impede: hoje o segundo
sobrescreveria o primeiro no mapa, em silêncio. Suspeito que precise de detecção
de colisão antes de o blog passar de uns 20 posts, e prefiro descobrir por gate
do que por link errado no ar.

Até onde a checagem de alias preguiçoso vai. Ela pega paráfrase léxica e só
isso. `[[terapia-2024|as sessões de terça]]` passa limpo e vaza tanto quanto,
para quem já sabe o suficiente para juntar as peças. Comparar strings não
alcança sinônimo, e a alternativa — comparar sentido — devolve o problema ao
julgamento probabilístico que descartei lá em cima por bons motivos. Minha
leitura é que existe um teto aqui e que já encostei nele.

E continua havendo o caso da frase oca: uma sentença construída inteiramente
sobre o link fica gramaticalmente válida e sem conteúdo depois da degradação.
Para o link com alias o gate deixa passar, porque não existe erro a detectar —
só um parágrafo pior. Isso ainda depende de eu ler os avisos, e leitura minha
é a parte mais frágil de qualquer desenho neste texto.
