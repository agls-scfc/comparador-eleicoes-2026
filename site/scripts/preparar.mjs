// Copia os PDFs oficiais para public/fontes/ (links "página N" do site apontam para eles).
import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const manifesto = yaml.load(readFileSync(resolve(raiz, "data/fontes/manifest.yaml"), "utf8"), { schema: yaml.CORE_SCHEMA });
const destino = resolve(raiz, "site/public/fontes");
mkdirSync(destino, { recursive: true });
for (const d of manifesto.documentos) copyFileSync(resolve(raiz, d.arquivo), resolve(destino, d.arquivo_publico));
console.log(`PDFs copiados: ${manifesto.documentos.map((d) => d.arquivo_publico).join(", ")}`);
