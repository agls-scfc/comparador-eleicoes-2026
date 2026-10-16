"""Gerador auxiliar de content/<eixo>/propostas.yaml e eixo.yaml (a fonte de verdade continua sendo o YAML).

Uso: crie um arquivo de especificação fora do repositório (ex.: /tmp/eixo.py) com

    import sys; sys.path.insert(0, "<repo>/scripts/curadoria")
    from curar import *
    L, F = "lula", "flavio-bolsonaro"
    regs = [R(L, "topico-id", "Rótulo neutro (<=90 caracteres)", [T(34, "Seção", "Frase literal do plano.")]), ...]
    emitir("id-do-eixo", [("topico-id", "Título do tópico")], {"plano-pt-2026": ["34-40"], "plano-pl-2026": ["21"]}, regs)

Depois rode: python3 -I scripts/validar.py  (o literal precisa existir na página citada).
Reescreve content/<eixo>/propostas.yaml inteiro: ids são numerados na ordem dos registros de cada candidato.
"""
import pathlib, re, yaml
RAIZ = pathlib.Path(__file__).resolve().parents[2]
DOC = {"lula": ("pt", "plano-pt-2026"), "flavio-bolsonaro": ("pl", "plano-pl-2026")}

def R(cand, topico, rotulo, trechos, tipo="compromisso", meta=None, cond=None):
    assert len(rotulo) <= 90, (len(rotulo), rotulo)
    return dict(cand=cand, topico=topico, rotulo=rotulo, tipo=tipo, trechos=trechos, meta=meta, cond=cond)

def T(pag, secao, literal):
    return (pag, secao, re.sub(r"\s+", " ", literal).strip())

def emitir(eixo, topicos, paginas, registros, titulo=None, descricao=None):
    out, n = [], {"lula": 0, "flavio-bolsonaro": 0}
    for r in registros:
        pre, doc = DOC[r["cand"]]
        n[r["cand"]] += 1
        out.append({
            "id": f"{pre}-{eixo}-{n[r['cand']]:03d}", "candidato": r["cand"], "eixo": eixo,
            "topico": r["topico"], "rotulo": r["rotulo"], "tipo": r["tipo"],
            "trechos": [{"documento": doc, "pagina_impressa": p, "secao": s, "literal": l} for p, s, l in r["trechos"]],
            "meta": r["meta"], "condicionalidade": r["cond"],
        })
    ordem = {"lula": 0, "flavio-bolsonaro": 1}
    out.sort(key=lambda x: (ordem[x["candidato"]], x["id"]))
    pasta = RAIZ / "content" / eixo
    cab = "# Trechos literais dos planos registrados no TSE. Frases inteiras; [...] só entre frases; mesmo critério para os dois lados.\n\n"
    (pasta / "propostas.yaml").write_text(cab + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")
    e = yaml.safe_load((pasta / "eixo.yaml").read_text(encoding="utf-8"))
    e["topicos"] = [{"id": i, "titulo": t} for i, t in topicos]
    e["paginas_nos_planos"] = paginas
    (pasta / "eixo.yaml").write_text(yaml.safe_dump(e, allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")
    print(eixo, {c: sum(1 for x in out if x["candidato"] == c and x["tipo"] == "compromisso") for c in n}, "resultados:",
          {c: sum(1 for x in out if x["candidato"] == c and x["tipo"] == "resultado_declarado") for c in n})
