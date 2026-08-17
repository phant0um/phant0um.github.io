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
