import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import yaml from "js-yaml";

// O build roda em site/; a raiz do repositório fica um nível acima.
const RAIZ = resolve(process.cwd(), "..");
export const PREVIEW = process.env.PREVIEW === "1";

const ler = (caminho: string) => yaml.load(readFileSync(caminho, "utf8"), { schema: yaml.CORE_SCHEMA }) as any;

export type CandidatoId = "flavio-bolsonaro" | "lula";

// Ordem fixa e igual em todas as páginas: alfabética pelo nome de urna (decisão P4).
export const CANDIDATOS: { id: CandidatoId; nome: string; partido: string; documento: string }[] = [
  { id: "flavio-bolsonaro", nome: "Flávio Bolsonaro", partido: "PL", documento: "plano-pl-2026" },
  { id: "lula", nome: "Lula", partido: "PT", documento: "plano-pt-2026" },
];

export interface Documento {
  id: string; candidato: CandidatoId; partido: string; titulo: string; arquivo_publico: string;
  url_tse: string; sha256: string; paginas: number; offset_pagina_impressa: number;
  data_obtencao: string; origem_do_arquivo: string; verificado_contra_tse: boolean;
}

export function documentos(): Record<string, Documento> {
  const m = ler(resolve(RAIZ, "data/fontes/manifest.yaml"));
  return Object.fromEntries(m.documentos.map((d: Documento) => [d.id, d]));
}

export interface Eixo {
  id: string; titulo: string; descricao: string; fase: "mvp" | "fase2"; ordem: number;
  topicos: { id: string; titulo: string }[];
  status: { propostas: string; acoes: string; falas: string };
  propostas: any[]; acoes: any[]; falas: any[];
}

const lista = (caminho: string) => (existsSync(caminho) ? ler(caminho) ?? [] : []);

export function eixos(): Eixo[] {
  const base = resolve(RAIZ, "content");
  return readdirSync(base, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => {
      const e = ler(resolve(base, d.name, "eixo.yaml"));
      return {
        ...e,
        propostas: lista(resolve(base, d.name, "propostas.yaml")),
        acoes: lista(resolve(base, d.name, "acoes.yaml")),
        falas: lista(resolve(base, d.name, "falas.yaml")),
      } as Eixo;
    })
    .sort((a, b) => a.ordem - b.ordem);
}

/** Uma camada só aparece ao público quando "publicado" (ou em build de pré-visualização). */
export const visivel = (status: string) => status === "publicado" || PREVIEW;

export function totalCompromissos(e: Eixo, candidato: CandidatoId) {
  return e.propostas.filter((p) => p.candidato === candidato && p.tipo === "compromisso").length;
}

/** Links para a página citada: cópia do PDF no próprio site e URL oficial do TSE. */
export function linksDaPagina(doc: Documento, paginaImpressa: number, base: string) {
  const pagina = paginaImpressa + doc.offset_pagina_impressa;
  return {
    pagina,
    local: `${base}fontes/${doc.arquivo_publico}#page=${pagina}`,
    tse: `${doc.url_tse}#page=${pagina}`,
  };
}
