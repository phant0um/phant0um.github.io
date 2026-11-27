#!/usr/bin/env python3
"""blog-nav-check.py — confere menu e front page dos boletins no site Hugo já buildado.

Uso:
  blog-nav-check.py --blog <dir>        # builda num tempdir e confere
  blog-nav-check.py --blog <dir> --site <public>   # confere build já feito

Regras (cada violação vira um achado):
  NAV_MISSING   seção pública sem link no menu. Seção = content/boletins/<sub>/_index.md
                e content/briefing/_index.md (o briefing mora fora de /boletins/).
  NAV_DATED     rótulo do menu com data (17/10/2026, 2026-11-23): título de edição
                vazou para o _index da subseção.
  NAV_LOWERCASE rótulo começa minúsculo ("de Concursos"): o replaceRE "^Boletim "
                do layout cortou só a palavra e sobrou a preposição.
  RAW_MARKDOWN  link markdown "[3](https://...)" literal no HTML da front page: o
                partial resumo.html não reconheceu o formato da citação.

Saída: JSON {nav, expected, findings}. Exit 0 sem achado, 1 com achado, 2 uso/build.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

DATED = re.compile(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}")
# Por que procurar no HTML e não no markdown: no markdown o link é legítimo; só vira
# bug quando um template copia o texto cru para fora do render (Hugo não converte).
RAW_LINK = re.compile(r"\[\d+\]\(https?://[^)\s]+\)")


class _NavParser(HTMLParser):
    """Junta (href, texto) dos <a> dentro de <nav class="bol-nav">.

    Por que HTMLParser e não regex: o minify do Hugo tira aspas dos atributos
    (class=bol-nav), e regex sobre HTML quebraria com essa variação.
    """

    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.href = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "nav" and "bol-nav" in (a.get("class") or "").split():
            self.in_nav = True
        elif tag == "a" and self.in_nav:
            self.href = a.get("href") or ""
            self.links.append([self.href, ""])

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False
        elif tag == "a":
            self.href = None

    def handle_data(self, data):
        if self.href is not None and self.links:
            self.links[-1][1] += data


def parse_nav(html: str) -> list[tuple[str, str]]:
    p = _NavParser()
    p.feed(html)
    return [(h, t.strip()) for h, t in p.links]


def expected_sections(blog: Path) -> list[str]:
    """Paths que o menu precisa ter, derivados do conteúdo (não de lista fixa).

    WHY: lista fixa envelhece igual ao menu; derivar das pastas pega seção nova.
    """
    out = sorted(f"/boletins/{d.name}/" for d in (blog / "content/boletins").iterdir()
                 if (d / "_index.md").is_file())
    if (blog / "content/briefing/_index.md").is_file():
        out.append("/briefing/")
    return out


def check(nav: list[tuple[str, str]], expected: list[str]) -> list[dict]:
    findings = []
    # HOW: compara pelo fim do href; o link pode vir relativo ou absoluto.
    hrefs = [h for h, _ in nav]
    for path in expected:
        if not any(h.endswith(path) for h in hrefs):
            findings.append({"code": "NAV_MISSING", "path": path})
    for href, label in nav:
        if DATED.search(label):
            findings.append({"code": "NAV_DATED", "path": href, "label": label})
        if label[:1].islower():
            findings.append({"code": "NAV_LOWERCASE", "path": href, "label": label})
    return findings


def build(blog: Path, dest: Path) -> None:
    p = subprocess.run(["hugo", "--quiet", "-s", str(blog), "-d", str(dest)],
                       capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"hugo rc={p.returncode}: {p.stderr[-300:]}")


def raw_markdown(html: str) -> list[dict]:
    return [{"code": "RAW_MARKDOWN", "text": m} for m in sorted(set(RAW_LINK.findall(html)))]


def run(blog: Path, site: Path) -> dict:
    html = (site / "boletins/index.html").read_text(encoding="utf-8")
    nav = parse_nav(html)
    exp = expected_sections(blog)
    return {"nav": nav, "expected": exp, "findings": check(nav, exp) + raw_markdown(html)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blog", required=True, type=Path)
    ap.add_argument("--site", type=Path, help="pasta public/ já buildada")
    a = ap.parse_args()
    if not (a.blog / "content/boletins").is_dir():
        print(f"blog inválido: {a.blog}", file=sys.stderr)
        return 2
    try:
        if a.site:
            res = run(a.blog, a.site)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                build(a.blog, Path(tmp))
                res = run(a.blog, Path(tmp))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        print(str(e), file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if res["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
