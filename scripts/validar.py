#!/usr/bin/env python3
"""Valida manifesto, conteúdo curado e regras de simetria.

Uso:
    python3 -I scripts/validar.py [--raiz CAMINHO] [--relatorio]

Sai com código 1 se houver qualquer erro. Avisos não reprovam, mas aparecem na saída.

O que reprova:
  - documento/PDF fora do manifesto, hash diferente, texto extraído de outro PDF
  - registro fora do schema, id duplicado ou inconsistente com candidato/eixo
  - trecho cujo literal não está na página citada, ou página inexistente
  - meta.expressao_no_plano ou condicionalidade que não aparecem num literal
  - camada "publicado" sem os dois candidatos (simetria)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

CANDIDATO_POR_PREFIXO = {"pt": "lula", "pl": "flavio-bolsonaro"}
PARTIDO_POR_CANDIDATO = {"lula": "PT", "flavio-bolsonaro": "PL"}
CAMADAS = ("propostas", "acoes", "falas")
OMISSAO = "[...]"

_ASPAS = str.maketrans(
    {"‘": "'", "’": "'", "‚": "'", "“": '"', "”": '"', "„": '"', "«": '"', "»": '"'}
)
_TRACOS = str.maketrans(
    {"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-"}
)


class _Loader(yaml.SafeLoader):
    """SafeLoader que não converte datas: 2026-10-09 continua string."""


_Loader.yaml_implicit_resolvers = {
    chave: [(tag, rx) for tag, rx in regras if tag != "tag:yaml.org,2002:timestamp"]
    for chave, regras in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def carregar_yaml(caminho: Path):
    return yaml.load(caminho.read_text(encoding="utf-8"), Loader=_Loader)


# ---------------------------------------------------------------- texto


def normalizar(texto: str) -> str:
    """Normalização aplicada aos dois lados da comparação (página e literal)."""
    t = unicodedata.normalize("NFKC", texto)
    t = t.replace("­", "")
    t = t.translate(_ASPAS).translate(_TRACOS)
    return re.sub(r"\s+", " ", t).strip()


def _sem_hifens(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("-", "")).strip()


def _variantes_da_pagina(pagina: str) -> list[str]:
    base = normalizar(pagina)
    juntar = re.sub(r"(?<=\w)- (?=\w)", "", base)  # hifenização de fim de linha: "inter- nacional"
    manter = re.sub(r"(?<=\w)- (?=\w)", "-", base)  # composto quebrado: "pós- graduação"
    return [base, juntar, manter]


def segmentos(literal: str) -> list[str]:
    """Divide o literal nas omissões [...]; ignora segmentos vazios."""
    return [s for s in (normalizar(p) for p in literal.split(OMISSAO)) if s]


def _achar_em_ordem(segs: list[str], texto: str) -> bool:
    pos = 0
    for s in segs:
        i = texto.find(s, pos)
        if i < 0:
            return False
        pos = i + len(s)
    return True


def casar_literal(literal: str, pagina: str) -> str | None:
    """Retorna 'exato', 'sem_hifen' ou None.

    'exato': todos os segmentos aparecem na página, em ordem, ignorando espaços, quebras de linha,
             aspas/traços tipográficos e hifenização de fim de linha.
    'sem_hifen': só casa se hifens forem ignorados dos dois lados (revisão humana recomendada).
    """
    segs = segmentos(literal)
    if not segs:
        return None
    for variante in _variantes_da_pagina(pagina):
        if _achar_em_ordem(segs, variante):
            return "exato"
    pagina_sh = _sem_hifens(normalizar(pagina))
    if _achar_em_ordem([_sem_hifens(s) for s in segs], pagina_sh):
        return "sem_hifen"
    return None


def contido_em_literais(trecho: str, literais: list[str]) -> bool:
    """O trecho (expressão ou condicionalidade) precisa constar em algum literal do mesmo registro."""
    alvo = normalizar(trecho)
    alvo_sh = _sem_hifens(alvo)
    for lit in literais:
        for seg in segmentos(lit):
            if alvo in seg or alvo_sh in _sem_hifens(seg):
                return True
        # a expressão pode atravessar uma omissão? não: exigimos dentro de um segmento contínuo.
    return False


def expandir_paginas(spec: str) -> range:
    if "-" in spec:
        a, b = spec.split("-", 1)
        return range(int(a), int(b) + 1)
    return range(int(spec), int(spec) + 1)


# ---------------------------------------------------------------- relatório


@dataclass
class Relatorio:
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    contagens: dict = field(default_factory=dict)  # (eixo, camada, candidato) -> n

    def erro(self, onde: str, msg: str) -> None:
        self.erros.append(f"{onde}: {msg}")

    def aviso(self, onde: str, msg: str) -> None:
        self.avisos.append(f"{onde}: {msg}")

    def info(self, onde: str, msg: str) -> None:
        self.infos.append(f"{onde}: {msg}")


def _schemas(raiz: Path) -> dict[str, Draft202012Validator]:
    out = {}
    for nome in ("documento", "eixo", "proposta", "fala", "acao"):
        esquema = json.loads((raiz / "schema" / f"{nome}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(esquema)
        out[nome] = Draft202012Validator(esquema)
    return out


def _erros_schema(validador: Draft202012Validator, instancia) -> list[str]:
    msgs = []
    for e in sorted(validador.iter_errors(instancia), key=lambda e: list(e.absolute_path)):
        caminho = "/".join(str(p) for p in e.absolute_path) or "(raiz)"
        msgs.append(f"{caminho}: {e.message}")
    return msgs


# ---------------------------------------------------------------- manifesto


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def validar_manifesto(raiz: Path, schemas, rel: Relatorio) -> dict[str, dict]:
    caminho = raiz / "data" / "fontes" / "manifest.yaml"
    if not caminho.is_file():
        rel.erro("manifest.yaml", "arquivo não existe")
        return {}
    dados = carregar_yaml(caminho)
    docs: dict[str, dict] = {}
    for doc in (dados or {}).get("documentos", []):
        onde = f"manifest:{doc.get('id', '?') if isinstance(doc, dict) else '?'}"
        msgs = _erros_schema(schemas["documento"], doc)
        for m in msgs:
            rel.erro(onde, m)
        if msgs:
            continue
        if doc.get("id") in docs:
            rel.erro(onde, "id de documento duplicado")
            continue
        docs[doc.get("id")] = doc
        pdf = raiz / doc.get("arquivo", "")
        if not pdf.is_file():
            rel.erro(onde, f"PDF não encontrado: {doc.get('arquivo')}")
            continue
        if sha256_arquivo(pdf) != doc.get("sha256"):
            rel.erro(onde, "sha256 do PDF diverge do manifesto")
        meta = raiz / "data" / "paginas" / doc["id"] / "_extracao.json"
        if not meta.is_file():
            rel.erro(onde, "texto extraído ausente (rode scripts/extrair_paginas.py)")
        else:
            m = json.loads(meta.read_text(encoding="utf-8"))
            if m.get("sha256") != doc.get("sha256"):
                rel.erro(onde, "texto extraído é de outro PDF (sha256 diferente); reextraia")
            for sub, rotulo in (("", "padrão"), ("layout", "layout")):
                n = len(list((raiz / "data" / "paginas" / doc["id"] / sub).glob("[0-9][0-9][0-9].txt")))
                if n != doc.get("paginas"):
                    rel.erro(onde, f"manifesto diz {doc.get('paginas')} páginas, há {n} arquivos de texto ({rotulo})")
        if not doc.get("verificado_contra_tse"):
            rel.aviso(onde, "hash ainda não conferido contra o download direto do TSE")
    return docs


MODOS = ("padrao", "layout")


class _Paginas:
    """Cache do texto por página e por modo de extração ('padrao' ou 'layout')."""

    def __init__(self, raiz: Path):
        self.raiz = raiz
        self._c: dict[tuple[str, int, str], str | None] = {}

    def texto(self, doc_id: str, pagina_pdf: int, modo: str = "padrao") -> str | None:
        chave = (doc_id, pagina_pdf, modo)
        if chave not in self._c:
            pasta = self.raiz / "data" / "paginas" / doc_id
            if modo == "layout":
                pasta = pasta / "layout"
            p = pasta / f"{pagina_pdf:03d}.txt"
            self._c[chave] = p.read_text(encoding="utf-8") if p.is_file() else None
        return self._c[chave]


def conferir_literal(literal: str, textos: dict[str, str | None]) -> tuple[str | None, str | None]:
    """Casa o literal nas duas extrações. Retorna (erro, aviso).

    - casa nas duas (ao menos uma de forma exata): ok
    - casa em apenas uma extração: aviso para conferir no PDF
    - só casa ignorando hifens (nas duas ou na única que casa): aviso de grafia
    - não casa em nenhuma: erro
    """
    resultados = {m: (casar_literal(literal, t) if t is not None else None) for m, t in textos.items()}
    casou = {m: r for m, r in resultados.items() if r}
    if not casou:
        return "NÃO_ENCONTRADO", None
    if len(casou) < len(resultados):
        so_em = "/".join(sorted(casou))
        return None, f"literal só casa na extração '{so_em}'; conferir a página no PDF"
    if all(r == "sem_hifen" for r in casou.values()):
        return None, "literal só casa ignorando hifens; revisar a grafia"
    return None, None


# ---------------------------------------------------------------- conteúdo


def _lista(caminho: Path, rel: Relatorio) -> list[dict]:
    """Lê uma camada (lista de registros). Arquivo ausente ou vazio = camada vazia."""
    if not caminho.is_file():
        return []
    dados = carregar_yaml(caminho)
    if dados is None:
        return []
    onde = f"{caminho.parent.name}/{caminho.name}"
    if not isinstance(dados, list):
        rel.erro(onde, "o arquivo deve conter uma lista de registros")
        return []
    registros = []
    for i, r in enumerate(dados):
        if isinstance(r, dict):
            registros.append(r)
        else:
            rel.erro(onde, f"item {i} não é um registro (mapa)")
    return registros


def _checar_id(onde, rid, candidato, eixo, rel: Relatorio):
    m = re.match(r"^(?:[af]-)?(pt|pl)-(.+)-(\d{3})$", rid or "")
    if not m:
        return
    if CANDIDATO_POR_PREFIXO[m.group(1)] != candidato:
        rel.erro(onde, f"prefixo do id ('{m.group(1)}') não corresponde ao candidato '{candidato}'")
    if m.group(2) != eixo:
        rel.erro(onde, f"slug do eixo no id ('{m.group(2)}') difere do eixo '{eixo}'")


def validar_propostas(raiz, eixo, topicos, docs, paginas: _Paginas, schemas, rel: Relatorio, ids: dict):
    caminho = raiz / "content" / eixo / "propostas.yaml"
    citadas: dict[str, set[int]] = {}
    for p in _lista(caminho, rel):
        pid = p.get("id", "?")
        onde = f"{eixo}/propostas.yaml:{pid}"
        for m in _erros_schema(schemas["proposta"], p):
            rel.erro(onde, m)
        if pid in ids:
            rel.erro(onde, f"id duplicado (também em {ids[pid]})")
        ids[pid] = onde
        cand = p.get("candidato")
        if p.get("eixo") != eixo:
            rel.erro(onde, f"campo eixo ('{p.get('eixo')}') difere da pasta '{eixo}'")
        _checar_id(onde, pid, cand, eixo, rel)
        if p.get("topico") not in topicos:
            rel.erro(onde, f"tópico '{p.get('topico')}' não existe em {eixo}/eixo.yaml")
        literais = []
        for i, t in enumerate(p.get("trechos") or []):
            ondet = f"{onde} trecho[{i}]"
            d = docs.get(t.get("documento"))
            if d is None:
                rel.erro(ondet, f"documento '{t.get('documento')}' não está no manifesto")
                continue
            if d.get("candidato") != cand:
                rel.erro(ondet, f"documento '{d['id']}' é de '{d.get('candidato')}', não de '{cand}'")
            pag_impressa = t.get("pagina_impressa")
            if not isinstance(pag_impressa, int):
                continue
            pag_pdf = pag_impressa + d.get("offset_pagina_impressa", 0)
            if not 1 <= pag_pdf <= d.get("paginas", 0):
                rel.erro(ondet, f"página {pag_impressa} fora do documento ({d.get('paginas')} páginas)")
                continue
            citadas.setdefault(d["id"], set()).add(pag_impressa)
            literal = t.get("literal") or ""
            literais.append(literal)
            textos = {m: paginas.texto(d["id"], pag_pdf, m) for m in MODOS}
            faltando = [m for m, t in textos.items() if t is None]
            if faltando:
                rel.erro(ondet, f"texto da página {pag_impressa} não foi extraído (modo {', '.join(faltando)})")
                continue
            if not segmentos(literal):
                rel.erro(ondet, "literal vazio")
                continue
            erro, aviso = conferir_literal(literal, textos)
            if erro:
                rel.erro(ondet, f"literal NÃO encontrado na página {pag_impressa} de {d['id']}")
            elif aviso:
                rel.aviso(ondet, f"{aviso} (página {pag_impressa} de {d['id']})")
        meta = p.get("meta")
        if isinstance(meta, dict) and meta.get("expressao_no_plano"):
            if not contido_em_literais(meta["expressao_no_plano"], literais):
                rel.erro(onde, f"meta.expressao_no_plano '{meta['expressao_no_plano']}' não consta em nenhum literal")
        cond = p.get("condicionalidade")
        if cond and not contido_em_literais(cond, literais):
            rel.erro(onde, "condicionalidade não é trecho literal de nenhum dos literais do registro")
        if cand in PARTIDO_POR_CANDIDATO:
            chave = (eixo, "propostas", cand)
            if p.get("tipo") == "compromisso":
                rel.contagens[chave] = rel.contagens.get(chave, 0) + 1
    return citadas


def validar_falas(raiz, eixo, topicos, schemas, rel: Relatorio, ids: dict):
    for f in _lista(raiz / "content" / eixo / "falas.yaml", rel):
        fid = f.get("id", "?")
        onde = f"{eixo}/falas.yaml:{fid}"
        for m in _erros_schema(schemas["fala"], f):
            rel.erro(onde, m)
        if fid in ids:
            rel.erro(onde, f"id duplicado (também em {ids[fid]})")
        ids[fid] = onde
        if f.get("eixo") != eixo:
            rel.erro(onde, f"campo eixo ('{f.get('eixo')}') difere da pasta '{eixo}'")
        _checar_id(onde, fid, f.get("candidato"), eixo, rel)
        if f.get("topico") and f["topico"] not in topicos:
            rel.erro(onde, f"tópico '{f['topico']}' não existe em {eixo}/eixo.yaml")
        chave = (eixo, "falas", f.get("candidato"))
        rel.contagens[chave] = rel.contagens.get(chave, 0) + 1


def validar_acoes(raiz, eixo, topicos, schemas, rel: Relatorio, ids: dict):
    for a in _lista(raiz / "content" / eixo / "acoes.yaml", rel):
        aid = a.get("id", "?")
        onde = f"{eixo}/acoes.yaml:{aid}"
        for m in _erros_schema(schemas["acao"], a):
            rel.erro(onde, m)
        if aid in ids:
            rel.erro(onde, f"id duplicado (também em {ids[aid]})")
        ids[aid] = onde
        if a.get("eixo") != eixo:
            rel.erro(onde, f"campo eixo ('{a.get('eixo')}') difere da pasta '{eixo}'")
        _checar_id(onde, aid, a.get("candidato"), eixo, rel)
        if a.get("topico") and a["topico"] not in topicos:
            rel.erro(onde, f"tópico '{a['topico']}' não existe em {eixo}/eixo.yaml")
        if a.get("ator_tipo") == "voto_da_bancada_do_partido":
            esperado = PARTIDO_POR_CANDIDATO.get(a.get("candidato"))
            partido = (a.get("ator") or {}).get("partido")
            if esperado and partido != esperado:
                rel.erro(onde, f"bancada de '{partido}' associada a '{a.get('candidato')}' (esperado {esperado})")
        chave = (eixo, "acoes", a.get("candidato"))
        rel.contagens[chave] = rel.contagens.get(chave, 0) + 1


def validar_referencias(raiz, eixos: list[str], ids: dict, rel: Relatorio):
    """proposta_ids de falas e ações precisam existir e ser propostas."""
    for eixo in eixos:
        for camada in ("falas", "acoes"):
            for r in _lista(raiz / "content" / eixo / f"{camada}.yaml", Relatorio()):
                for pid in r.get("proposta_ids") or []:
                    # ids de proposta começam com pt-/pl-; "a-" e "f-" são ações e falas
                    if pid not in ids or pid.startswith(("a-", "f-")):
                        rel.erro(f"{eixo}/{camada}.yaml:{r.get('id', '?')}", f"proposta_ids referencia '{pid}', que não é uma proposta existente")


def validar_simetria(eixo_dados: dict, rel: Relatorio):
    eixo = eixo_dados["id"]
    for camada in CAMADAS:
        if eixo_dados["status"].get(camada) != "publicado":
            continue
        for cand in PARTIDO_POR_CANDIDATO:
            if rel.contagens.get((eixo, camada, cand), 0) < 1:
                rel.erro(f"{eixo}", f"camada '{camada}' está 'publicado' mas '{cand}' não tem nenhum registro (simetria)")


def validar_conteudo(raiz: Path, docs: dict, schemas, rel: Relatorio) -> None:
    base = raiz / "content"
    if not base.is_dir():
        rel.erro("content/", "pasta não existe")
        return
    paginas = _Paginas(raiz)
    ids: dict[str, str] = {}
    eixos_ok: list[str] = []
    ordens: dict[int, str] = {}
    for pasta in sorted(p for p in base.iterdir() if p.is_dir()):
        eixo_yaml = pasta / "eixo.yaml"
        if not eixo_yaml.is_file():
            rel.erro(f"content/{pasta.name}", "falta eixo.yaml")
            continue
        e = carregar_yaml(eixo_yaml)
        onde = f"{pasta.name}/eixo.yaml"
        msgs = _erros_schema(schemas["eixo"], e)
        for m in msgs:
            rel.erro(onde, m)
        if msgs:
            continue
        if e["id"] != pasta.name:
            rel.erro(onde, f"id '{e['id']}' difere do nome da pasta '{pasta.name}'")
            continue
        if e["ordem"] in ordens:
            rel.erro(onde, f"ordem {e['ordem']} repetida (também em {ordens[e['ordem']]})")
        ordens[e["ordem"]] = e["id"]
        for doc_id in e["paginas_nos_planos"]:
            if doc_id not in docs:
                rel.erro(onde, f"paginas_nos_planos cita documento '{doc_id}' fora do manifesto")
        topicos = {t["id"] for t in e["topicos"]}
        if len(topicos) != len(e["topicos"]):
            rel.erro(onde, "ids de tópico repetidos")
        eixos_ok.append(e["id"])
        citadas = validar_propostas(raiz, e["id"], topicos, docs, paginas, schemas, rel, ids)
        validar_falas(raiz, e["id"], topicos, schemas, rel, ids)
        validar_acoes(raiz, e["id"], topicos, schemas, rel, ids)
        validar_simetria(e, rel)
        # cobertura: páginas do eixo (guia de curadoria) sem nenhum trecho citado
        for doc_id, specs in e["paginas_nos_planos"].items():
            todas = [n for s in specs for n in expandir_paginas(s)]
            faltam = [n for n in todas if n not in citadas.get(doc_id, set())]
            cand_doc = docs.get(doc_id, {}).get("candidato")
            if faltam and rel.contagens.get((e["id"], "propostas", cand_doc), 0):
                rel.info(f"{e['id']}", f"{doc_id}: páginas do eixo sem trecho citado: {faltam}")
    validar_referencias(raiz, eixos_ok, ids, rel)


def validar(raiz: Path) -> Relatorio:
    rel = Relatorio()
    schemas = _schemas(raiz)
    docs = validar_manifesto(raiz, schemas, rel)
    validar_conteudo(raiz, docs, schemas, rel)
    return rel


def imprimir_relatorio(rel: Relatorio, completo: bool) -> None:
    if completo:
        eixos = sorted({k[0] for k in rel.contagens})
        if eixos:
            print("Contagem por eixo (propostas = só 'compromisso'):")
            print(f"  {'eixo':42} {'camada':10} {'lula':>5} {'flávio':>7}")
            for e in eixos:
                for c in CAMADAS:
                    a = rel.contagens.get((e, c, "lula"), 0)
                    b = rel.contagens.get((e, c, "flavio-bolsonaro"), 0)
                    if a or b:
                        print(f"  {e:42} {c:10} {a:>5} {b:>7}")
        for i in rel.infos:
            print("INFO  ", i)
    for a in rel.avisos:
        print("AVISO ", a)
    for e in rel.erros:
        print("ERRO  ", e)
    print(f"\n{len(rel.erros)} erro(s), {len(rel.avisos)} aviso(s)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--relatorio", action="store_true", help="imprime contagens e cobertura")
    args = ap.parse_args(argv)
    rel = validar(args.raiz.resolve())
    imprimir_relatorio(rel, args.relatorio)
    return 1 if rel.erros else 0


if __name__ == "__main__":
    sys.exit(main())
