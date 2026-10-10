#!/usr/bin/env python3
"""Extrai o texto de cada página dos PDFs listados em data/fontes/manifest.yaml.

Saída: data/paginas/<id-do-documento>/NNN.txt (NNN = página do PDF, 3 dígitos)
       data/paginas/<id-do-documento>/_extracao.json (hash, ferramenta e versão)

Requer poppler-utils (pdftotext) e PyYAML.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
MANIFESTO = RAIZ / "data" / "fontes" / "manifest.yaml"
SAIDA = RAIZ / "data" / "paginas"


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def versao_pdftotext() -> str:
    r = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True, check=True)
    return (r.stderr or r.stdout).splitlines()[0].strip()


def texto_da_pagina(pdf: Path, pagina: int) -> str:
    r = subprocess.run(
        ["pdftotext", "-f", str(pagina), "-l", str(pagina), "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout


def main() -> int:
    manifesto = yaml.safe_load(MANIFESTO.read_text(encoding="utf-8"))
    versao = versao_pdftotext()
    for doc in manifesto["documentos"]:
        pdf = RAIZ / doc["arquivo"]
        if not pdf.is_file():
            print(f"ERRO: {pdf} não existe", file=sys.stderr)
            return 1
        hash_real = sha256_arquivo(pdf)
        if hash_real != doc["sha256"]:
            print(
                f"ERRO: sha256 de {doc['arquivo']} diverge do manifesto\n"
                f"  manifesto: {doc['sha256']}\n  arquivo:   {hash_real}",
                file=sys.stderr,
            )
            return 1
        destino = SAIDA / doc["id"]
        destino.mkdir(parents=True, exist_ok=True)
        for antigo in destino.glob("*.txt"):
            antigo.unlink()
        for n in range(1, doc["paginas"] + 1):
            texto = texto_da_pagina(pdf, n)
            (destino / f"{n:03d}.txt").write_text(texto, encoding="utf-8")
        meta = {
            "documento": doc["id"],
            "sha256": hash_real,
            "paginas": doc["paginas"],
            "ferramenta": "pdftotext",
            "versao_ferramenta": versao,
        }
        (destino / "_extracao.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{doc['id']}: {doc['paginas']} páginas extraídas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
