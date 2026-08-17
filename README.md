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
