# phant0um.github.io

Blog técnico. Artigos longos sobre verificação, agentes e engenharia de
contexto — o que não cabe numa thread.

**No ar:** https://phant0um.github.io/

## Este repo não é a fonte do texto

Os posts em `content/posts/` são **gerados**. A fonte editorial mora num vault
Obsidian e é convertida por um script que também serve de gate de privacidade.
Editar um `.md` aqui funciona até a próxima republicação sobrescrever.

```
vault/01-PROJECTS/blog/{drafts,published}/<slug>.md
        ↓  blog-publish.py   (converte wikilink, filtra frontmatter, barra)
content/posts/<slug>.md
        ↓  git push          (gate humano)
GitHub Actions → Pages
```

O conversor resolve wikilink contra **este repo**: um link só é emitido se o
alvo já está publicado aqui. Repo é a fonte de verdade sobre o que é público,
justamente para não existir uma lista paralela que diverge em silêncio.

## Boletins

Site: https://phant0um.github.io/boletins/ — edições automáticas de boletins temáticos (IA, três poderes, finanças BR–EUA, licitações e outros).

Também gerados: `content/boletins/<slug>/<AAAA-MM-DD>.md` vêm do vault e são sobrescritos no próximo sync; não edite aqui.

```
feeds públicos (RSS/Atom, APIs PNCP/BCB)
        ↓  boletim-feed.py      (coleta, ranqueia, renderiza)
modelo sem ferramentas          (escreve só resumo e "por que importa")
        ↓  boletim-check.py verify  (cada fonte citada, cotações batem com snapshot)
vault/06-GENERATED/boletins/<slug>/<data>.md
        ↓  boletim-publish.py sync  (só boletins públicos e edições verificadas)
content/boletins/
        ↓  git push          (gate humano)
GitHub Actions → Pages
```

Boletins com dado pessoal (carteira) ou de trabalho ficam fora por allowlist no script.

### Layout de jornal (`/boletins/`)

- Templates em `layouts/boletins/` (`list.html` para a capa e as listas, `single.html` para a edição). Partials de apoio em `layouts/partials/boletins/`.
- Estilo em `assets/css/extended/boletins.css`. Toda regra começa em `.bol-root` (o wrapper que os layouts criam) ou em `body:has(.bol-root)`, então as páginas de artigo não recebem o estilo.
- Nome do boletim sem o prefixo "Boletim " só na exibição (nav, eyebrow, módulos). O título da página e o SEO não mudam.
- Meta description das edições: a primeira bullet de "Em resumo". Sobrescrita em `layouts/partials/head.html` (cópia do head do PaperMod com uma linha trocada).
- Páginas de apoio em `content/boletins-info/` (Sobre os boletins, Fontes, Padrões editoriais, Correções). Não moram em `content/boletins/`, que o sync sobrescreve. Os links ficam no rodapé de `.bol-root`.

### Artigos (`/posts/`)

A lista de `/posts/` tem layout próprio em `layouts/posts/list.html`: título "Artigos", uma linha por artigo. O endereço e as páginas de artigo continuam PaperMod.

## Série 1 — verde que mente

Cinco casos em que um sistema meu declarou estar verificado e não estava, mais
a régua que tentei extrair deles. Cada artigo se sustenta sozinho; a ordem
abaixo é a de leitura.

| # | Post | Assunto |
|---|---|---|
| 1 | `false-green-cobertura` | cobertura derivada do exit code |
| 2 | `relogio-de-revisao` | `updated` no lugar de `reviewed` |
| 3 | `claude-md-e-firmware` | instrução sempre-carregada é imposto |
| 4 | `auditoria-descartada` | o que fazer quando o resultado está contaminado |
| 5 | `gate-de-privacidade-wikilink` | default fechado como controle de acesso |
| 6 | `limiar-de-verificacao` | quanta verificação cada mudança merece |

A ordem não é decorativa: 2–5 citam o artigo 1, o 3 depende do 4 para o leitor
saber por que a validação daquele corte foi refeita, e o 6 cita os cinco.

O campo `date` de cada post é **declarado** na fonte, no vault, um dia por
artigo. Antes ele vinha do horário de execução do script, o que deixava cinco
posts a segundos de distância e a ordem da listagem à mercê da ordem do loop.

## Stack

| Peça | Escolha |
|---|---|
| Gerador | Hugo extended (versão fixada em `.github/workflows/hugo.yaml`) |
| Tema | PaperMod, como submódulo git |
| Deploy | GitHub Actions → Pages (`build_type: workflow`, não Jekyll) |
| Busca | Fuse.js, via output JSON da home |

## Rodar local

```bash
git clone --recurse-submodules git@github.com:phant0um/phant0um.github.io.git
cd phant0um.github.io
hugo server -D
```

Sem `--recurse-submodules` o tema não vem e o build quebra com erro que não
menciona submódulo. O workflow usa `submodules: recursive` pelo mesmo motivo.

## Publicar

Não faça `hugo new` nem escreva post aqui. O fluxo é o do vault: artigo vira
`status: ready`, o script converte, o push é confirmação humana explícita.
Deploy só conta com Actions `success` **e** HTTP 200 na URL final — build verde
não é página no ar.
