#!/usr/bin/env python3
"""Baixa cada PDF da URL oficial do TSE e compara o sha256 com o manifesto.

Uso: python3 scripts/verificar_fontes.py
Sai com código 1 se algum hash divergir ou se o download falhar.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
MANIFESTO = RAIZ / "data" / "fontes" / "manifest.yaml"


def baixar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "comparador-eleicoes-2026/verificar-fontes"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> int:
    manifesto = yaml.safe_load(MANIFESTO.read_text(encoding="utf-8"))
    falhas = 0
    for doc in manifesto["documentos"]:
        try:
            conteudo = baixar(doc["url_tse"])
        except Exception as e:  # noqa: BLE001
            print(f"FALHA {doc['id']}: não foi possível baixar ({e})")
            falhas += 1
            continue
        h = hashlib.sha256(conteudo).hexdigest()
        if h == doc["sha256"]:
            print(f"OK    {doc['id']}: sha256 igual ao do TSE ({h[:12]}…)")
        else:
            print(f"DIVERGE {doc['id']}: manifesto {doc['sha256'][:12]}… / TSE {h[:12]}…")
            falhas += 1
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
