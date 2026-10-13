"""Testes do validador. Rodar: python3 -I -m unittest discover -s tests -v"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("validar", REPO / "scripts" / "validar.py")
validar = importlib.util.module_from_spec(_spec)
sys.modules["validar"] = validar  # dataclasses com anotações adiadas exigem o módulo registrado
_spec.loader.exec_module(validar)

EIXO = "seguranca-publica"

PAGINAS_PT = {
    1: "Capa do plano.",
    2: (
        "Criaremos o Ministério da Segurança Pública. Uma vez aprovada a PEC da Segurança\n"
        "Pública, o governo vai ampliar a formação de policiais, com meta de\n"
        "meio milhão de vagas e cursos de pós-\ngraduação para a carreira."
    ),
    3: "O plano “promete” investir em perícia e inteligência.\nTexto A. Outra frase. Texto B.",
}
PAGINAS_PL = {
    1: "Capa do plano.",
    2: "Vamos criar meio milhão de novas vagas no sistema prisional em 4 anos.",
    3: "Texto final do plano de governo.",
}


def _doc(doc_id, candidato, partido, paginas):
    arquivo = f"data/fontes/{doc_id}.pdf"
    return {
        "id": doc_id,
        "candidato": candidato,
        "partido": partido,
        "titulo": f"Plano {doc_id}",
        "arquivo": arquivo,
        "arquivo_publico": f"{doc_id}.pdf",
        "url_tse": f"https://www.tse.jus.br/exemplo/{doc_id}.pdf",
        "sha256": hashlib.sha256(doc_id.encode()).hexdigest(),
        "paginas": len(paginas),
        "offset_pagina_impressa": 0,
        "data_obtencao": "2026-10-09",
        "origem_do_arquivo": "copia_fornecida_pelo_mantenedor",
        "verificado_contra_tse": False,
    }


def _proposta(**sobre):
    base = {
        "id": f"pt-{EIXO}-001",
        "candidato": "lula",
        "eixo": EIXO,
        "topico": "forcas-de-seguranca",
        "rotulo": "Ministério da Segurança Pública",
        "tipo": "compromisso",
        "trechos": [
            {
                "documento": "plano-pt-2026",
                "pagina_impressa": 2,
                "secao": "3. Segurança pública",
                "literal": "Criaremos o Ministério da Segurança Pública.",
            }
        ],
        "meta": None,
        "condicionalidade": None,
    }
    base.update(sobre)
    return base


def _proposta_pl(**sobre):
    base = _proposta(
        id=f"pl-{EIXO}-001",
        candidato="flavio-bolsonaro",
        rotulo="Vagas no sistema prisional",
        trechos=[
            {
                "documento": "plano-pl-2026",
                "pagina_impressa": 2,
                "secao": "Brasil sem Medo",
                "literal": "Vamos criar meio milhão de novas vagas no sistema prisional em 4 anos.",
            }
        ],
    )
    base.update(sobre)
    return base


def _fala(candidato="lula", **sobre):
    pre = "pt" if candidato == "lula" else "pl"
    base = {
        "id": f"f-{pre}-{EIXO}-001",
        "candidato": candidato,
        "eixo": EIXO,
        "citacao": "Uma citação curta de teste sobre segurança pública.",
        "data": "2026-09-01",
        "veiculo": "Veículo de teste",
        "tipo_fonte": "entrevista",
        "url": "https://exemplo.org/fala",
    }
    base.update(sobre)
    return base


def _acao_bancada(candidato="lula", partido="PT", **sobre):
    pre = "pt" if candidato == "lula" else "pl"
    base = {
        "id": f"a-{pre}-{EIXO}-001",
        "candidato": candidato,
        "eixo": EIXO,
        "ator_tipo": "voto_da_bancada_do_partido",
        "ator": {"nome": f"Bancada do {partido} na Câmara", "partido": partido},
        "casa": "camara",
        "data": "2024-05-01",
        "descricao": "Votação de teste sobre segurança pública.",
        "votacao": {"id": "123-1", "proposicao": "PL 1/2024", "resultado": "Aprovado"},
        "bancada": {"orientacao": "Sim", "sim": 10, "nao": 2, "abstencao": 0, "ausentes": None},
        "estado": "nominal",
        "fonte_url": "https://exemplo.leg.br/votacao/123-1",
    }
    base.update(sobre)
    return base


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.raiz = Path(self._tmp.name)
        shutil.copytree(REPO / "schema", self.raiz / "schema")
        self.docs = [
            _doc("plano-pt-2026", "lula", "PT", PAGINAS_PT),
            _doc("plano-pl-2026", "flavio-bolsonaro", "PL", PAGINAS_PL),
        ]
        self._escrever_fontes(self.docs, {"plano-pt-2026": PAGINAS_PT, "plano-pl-2026": PAGINAS_PL})
        self.eixo = {
            "id": EIXO,
            "titulo": "Segurança pública",
            "descricao": "Policiamento, sistema prisional e combate ao crime.",
            "fase": "mvp",
            "ordem": 1,
            "paginas_nos_planos": {"plano-pt-2026": ["2-3"], "plano-pl-2026": ["2"]},
            "topicos": [
                {"id": "forcas-de-seguranca", "titulo": "Forças de segurança"},
                {"id": "sistema-prisional", "titulo": "Sistema prisional"},
            ],
            "status": {"propostas": "em_preparacao", "acoes": "em_preparacao", "falas": "em_preparacao"},
        }
        self.camadas = {"propostas": [_proposta(), _proposta_pl()], "acoes": [], "falas": []}

    def _escrever_fontes(self, docs, paginas_por_doc):
        (self.raiz / "data" / "fontes").mkdir(parents=True)
        for d in docs:
            (self.raiz / d["arquivo"]).write_bytes(d["id"].encode())
            pasta = self.raiz / "data" / "paginas" / d["id"]
            (pasta / "layout").mkdir(parents=True)
            for n, txt in paginas_por_doc[d["id"]].items():
                (pasta / f"{n:03d}.txt").write_text(txt, encoding="utf-8")
                (pasta / "layout" / f"{n:03d}.txt").write_text(txt, encoding="utf-8")
            (pasta / "_extracao.json").write_text(
                '{"sha256": "%s"}' % d["sha256"], encoding="utf-8"
            )
        (self.raiz / "data" / "fontes" / "manifest.yaml").write_text(
            yaml.safe_dump({"documentos": docs}, allow_unicode=True), encoding="utf-8"
        )

    def rodar(self):
        pasta = self.raiz / "content" / EIXO
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "eixo.yaml").write_text(yaml.safe_dump(self.eixo, allow_unicode=True), encoding="utf-8")
        for camada, registros in self.camadas.items():
            (pasta / f"{camada}.yaml").write_text(
                yaml.safe_dump(registros, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
        return validar.validar(self.raiz)

    def assertErro(self, rel, trecho):
        self.assertTrue(
            any(trecho in e for e in rel.erros),
            f"esperava erro contendo {trecho!r}; erros reais: {rel.erros}",
        )

    def assertSemErros(self, rel):
        self.assertEqual(rel.erros, [], f"erros inesperados: {rel.erros}")


class TestLiteral(Base):
    def test_conteudo_valido(self):
        self.assertSemErros(self.rodar())

    def test_literal_com_palavra_trocada_reprova(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "Criaremos o Ministério da Segurança Nacional."
        self.assertErro(self.rodar(), "NÃO encontrado")

    def test_quebra_de_linha_e_aspas_tipograficas(self):
        # a página quebra linha no meio e usa aspas curvas; o literal vem numa linha com aspas retas
        self.camadas["propostas"][0]["trechos"][0].update(
            pagina_impressa=3, literal='O plano "promete" investir em perícia e inteligência.'
        )
        self.assertSemErros(self.rodar())

    def test_hifenizacao_de_fim_de_linha_casa_sem_aviso(self):
        self.camadas["propostas"][0]["trechos"][0].update(
            pagina_impressa=2, literal="cursos de pós-graduação para a carreira"
        )
        rel = self.rodar()
        self.assertSemErros(rel)
        self.assertEqual(rel.avisos, [m for m in rel.avisos if "manifest" in m], "não deveria avisar sobre hífen")

    def test_hifen_perdido_na_extracao_gera_aviso_e_nao_erro(self):
        texto = "Cursos de pósgraduação para toda a carreira policial."
        for sub in ("", "layout/"):
            (self.raiz / f"data/paginas/plano-pt-2026/{sub}002.txt").write_text(texto, encoding="utf-8")
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "Cursos de pós-graduação para toda a carreira policial."
        rel = self.rodar()
        self.assertSemErros(rel)
        self.assertTrue(any("ignorando hifens" in a for a in rel.avisos), rel.avisos)

    def test_casa_so_na_extracao_padrao_gera_aviso(self):
        # texto justificado embaralhado no modo layout: o literal casa só no modo padrão
        (self.raiz / "data/paginas/plano-pt-2026/layout/002.txt").write_text("Ministério Criaremos o da Pública Segurança.", encoding="utf-8")
        rel = self.rodar()
        self.assertSemErros(rel)
        self.assertTrue(any("só casa na extração 'padrao'" in a for a in rel.avisos), rel.avisos)

    def test_casa_so_na_extracao_layout_gera_aviso(self):
        # o caso real da PT p.28: ordem de leitura embaralhada no modo padrão, correta no layout
        (self.raiz / "data/paginas/plano-pt-2026/002.txt").write_text("Ministério Criaremos o da Pública Segurança.", encoding="utf-8")
        rel = self.rodar()
        self.assertSemErros(rel)
        self.assertTrue(any("só casa na extração 'layout'" in a for a in rel.avisos), rel.avisos)

    def test_nao_casa_em_nenhuma_extracao_reprova(self):
        for sub in ("", "layout/"):
            (self.raiz / f"data/paginas/plano-pt-2026/{sub}002.txt").write_text("Outro conteúdo qualquer.", encoding="utf-8")
        self.assertErro(self.rodar(), "NÃO encontrado")

    def test_falta_de_extracao_layout_reprova(self):
        (self.raiz / "data/paginas/plano-pt-2026/layout/002.txt").unlink()
        self.assertErro(self.rodar(), "layout")

    def test_omissao_em_ordem_passa(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "Criaremos o Ministério [...] aprovada a PEC da Segurança"
        self.assertSemErros(self.rodar())

    def test_omissao_fora_de_ordem_reprova(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "aprovada a PEC da Segurança [...] Criaremos o Ministério"
        self.assertErro(self.rodar(), "NÃO encontrado")

    def test_literal_de_outra_pagina_reprova(self):
        # o texto existe na página 2, mas o registro cita a 3
        self.camadas["propostas"][0]["trechos"][0]["pagina_impressa"] = 3
        self.assertErro(self.rodar(), "NÃO encontrado")

    def test_diferenca_de_caixa_reprova(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "criaremos o ministério da segurança pública."
        self.assertErro(self.rodar(), "NÃO encontrado")

    def test_pagina_inexistente(self):
        self.camadas["propostas"][0]["trechos"][0]["pagina_impressa"] = 99
        self.assertErro(self.rodar(), "fora do documento")

    def test_literal_so_de_omissao_reprova(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "[...] [...] [...]"
        self.assertErro(self.rodar(), "literal vazio")


class TestProposta(Base):
    def test_documento_de_outro_candidato(self):
        self.camadas["propostas"][0]["trechos"][0]["documento"] = "plano-pl-2026"
        rel = self.rodar()
        self.assertErro(rel, "é de 'flavio-bolsonaro', não de 'lula'")

    def test_documento_fora_do_manifesto(self):
        self.camadas["propostas"][0]["trechos"][0]["documento"] = "plano-xx-2026"
        self.assertErro(self.rodar(), "não está no manifesto")

    def test_prefixo_do_id_incompativel_com_candidato(self):
        self.camadas["propostas"][0]["id"] = f"pl-{EIXO}-001"
        self.camadas["propostas"][1]["id"] = f"pl-{EIXO}-002"
        self.assertErro(self.rodar(), "prefixo do id")

    def test_slug_do_eixo_no_id_incompativel(self):
        self.camadas["propostas"][0]["id"] = "pt-outro-eixo-001"
        self.assertErro(self.rodar(), "slug do eixo no id")

    def test_id_duplicado(self):
        self.camadas["propostas"].append(copy.deepcopy(self.camadas["propostas"][0]))
        self.assertErro(self.rodar(), "id duplicado")

    def test_topico_inexistente(self):
        self.camadas["propostas"][0]["topico"] = "nao-existe"
        self.assertErro(self.rodar(), "não existe em")

    def test_sem_trechos_viola_schema(self):
        self.camadas["propostas"][0]["trechos"] = []
        self.assertErro(self.rodar(), "trechos")

    def test_tipo_invalido(self):
        self.camadas["propostas"][0]["tipo"] = "promessa_vaga"
        self.assertErro(self.rodar(), "tipo")

    def test_meta_com_expressao_no_literal(self):
        self.camadas["propostas"][1]["meta"] = {"valor": 500000, "unidade": "vagas prisionais", "prazo": "4 anos", "expressao_no_plano": "meio milhão"}
        self.assertSemErros(self.rodar())

    def test_meta_com_expressao_fora_do_literal(self):
        self.camadas["propostas"][1]["meta"] = {"valor": 500000, "unidade": "vagas prisionais", "prazo": "4 anos", "expressao_no_plano": "500 mil"}
        self.assertErro(self.rodar(), "expressao_no_plano")

    def test_condicionalidade_literal_passa(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "Uma vez aprovada a PEC da Segurança Pública, o governo vai ampliar"
        self.camadas["propostas"][0]["condicionalidade"] = "Uma vez aprovada a PEC da Segurança Pública"
        self.assertSemErros(self.rodar())

    def test_condicionalidade_parafraseada_reprova(self):
        self.camadas["propostas"][0]["trechos"][0]["literal"] = "Uma vez aprovada a PEC da Segurança Pública, o governo vai ampliar"
        self.camadas["propostas"][0]["condicionalidade"] = "aprovação da PEC da Segurança Pública"
        self.assertErro(self.rodar(), "condicionalidade")


class TestSimetria(Base):
    def test_publicado_com_os_dois_lados_passa(self):
        self.eixo["status"]["propostas"] = "publicado"
        self.assertSemErros(self.rodar())

    def test_publicado_so_com_um_lado_reprova(self):
        self.eixo["status"]["propostas"] = "publicado"
        self.camadas["propostas"] = [self.camadas["propostas"][0]]
        self.assertErro(self.rodar(), "simetria")

    def test_critica_ao_adversario_nao_conta_como_proposta(self):
        self.eixo["status"]["propostas"] = "publicado"
        self.camadas["propostas"][1]["tipo"] = "critica_ao_adversario"
        self.assertErro(self.rodar(), "flavio-bolsonaro")

    def test_em_preparacao_nao_exige_simetria(self):
        self.camadas["propostas"] = [self.camadas["propostas"][0]]
        self.assertSemErros(self.rodar())

    def test_falas_publicadas_so_de_um_lado_reprova(self):
        self.eixo["status"]["falas"] = "publicado"
        self.camadas["falas"] = [_fala("lula")]
        self.assertErro(self.rodar(), "simetria")


class TestAcoesEFalas(Base):
    def test_acao_de_bancada_valida(self):
        self.camadas["acoes"] = [_acao_bancada()]
        self.assertSemErros(self.rodar())

    def test_bancada_com_partido_trocado_reprova(self):
        self.camadas["acoes"] = [_acao_bancada(candidato="lula", partido="PL")]
        self.assertErro(self.rodar(), "esperado PT")

    def test_acao_de_bancada_sem_contagem_reprova(self):
        a = _acao_bancada()
        del a["bancada"]
        self.camadas["acoes"] = [a]
        self.assertErro(self.rodar(), "bancada")

    def test_acao_com_url_nao_https_reprova(self):
        self.camadas["acoes"] = [_acao_bancada(fonte_url="http://exemplo.leg.br/x")]
        self.assertErro(self.rodar(), "fonte_url")

    def test_fala_valida(self):
        self.camadas["falas"] = [_fala()]
        self.assertSemErros(self.rodar())

    def test_fala_com_citacao_longa_demais_reprova(self):
        self.camadas["falas"] = [_fala(citacao="x" * 401)]
        self.assertErro(self.rodar(), "citacao")

    def test_proposta_ids_inexistente(self):
        self.camadas["falas"] = [_fala(proposta_ids=["pt-seguranca-publica-999"])]
        self.assertErro(self.rodar(), "proposta_ids")

    def test_proposta_ids_apontando_para_outra_fala(self):
        self.camadas["falas"] = [_fala(), _fala(id=f"f-pt-{EIXO}-002", proposta_ids=[f"f-pt-{EIXO}-001"])]
        self.assertErro(self.rodar(), "proposta_ids")

    def test_proposta_ids_valido(self):
        self.camadas["falas"] = [_fala(proposta_ids=[f"pt-{EIXO}-001"])]
        self.assertSemErros(self.rodar())


class TestManifesto(Base):
    def test_sha256_divergente(self):
        (self.raiz / "data/fontes/plano-pt-2026.pdf").write_bytes(b"outro conteudo")
        self.assertErro(self.rodar(), "sha256 do PDF diverge")

    def test_texto_extraido_de_outro_pdf(self):
        (self.raiz / "data/paginas/plano-pt-2026/_extracao.json").write_text('{"sha256": "0"}', encoding="utf-8")
        self.assertErro(self.rodar(), "outro PDF")

    def test_numero_de_paginas_diferente(self):
        (self.raiz / "data/paginas/plano-pt-2026/003.txt").unlink()
        self.assertErro(self.rodar(), "arquivos de texto")

    def test_aviso_enquanto_nao_verificado_contra_tse(self):
        rel = self.rodar()
        self.assertTrue(any("TSE" in a for a in rel.avisos))


class TestRepositorioReal(unittest.TestCase):
    def test_conteudo_do_repo_nao_tem_erros(self):
        rel = validar.validar(REPO)
        self.assertEqual(rel.erros, [], "\n".join(rel.erros))


if __name__ == "__main__":
    unittest.main()
