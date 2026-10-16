# Comparador de propostas — Eleições 2026

Site informativo e **auditável** que compara lado a lado as propostas de governo de **Lula** e **Flávio Bolsonaro** para a Presidência da República, com as falas e o histórico de ações de cada lado.

Valores: **defesa da democracia** e **transparência**. O site não recomenda voto. Ele mostra o que está nos documentos oficiais e onde conferir.

## Como o conteúdo é feito

- **Propostas:** trechos **literais** dos planos de governo registrados no TSE, cada um com documento, página e link. O texto exibido precisa existir na página citada; um validador confere isso antes de qualquer publicação.
- **Falas:** citações curtas dos candidatos, com data, veículo e link. O site não classifica uma fala como coerente ou divergente do plano.
- **Ações:** votos do próprio candidato, votos da **bancada do partido** (Câmara e Senado), atos de governo e autoria, sempre identificando **quem agiu**.

As regras completas estão em [`docs/decisions.md`](docs/decisions.md).

## Estrutura

```
data/fontes/        PDFs dos planos (originais do TSE) + manifest.yaml (URL, sha256, páginas)
data/paginas/       texto extraído de cada página (gerado por scripts/extrair_paginas.py)
schema/             JSON Schemas de documento, eixo, proposta, fala e ação
scripts/            extração, verificação das fontes e validação
content/<eixo>/     propostas.yaml, acoes.yaml, falas.yaml
site/               site estático
docs/               decisões e documentação
```

## Rodando localmente

Requisitos: **Node.js 20+**, **Python 3.11+** e **git**. Os comandos abaixo são um por linha, para funcionar em qualquer terminal (inclusive o PowerShell do Windows, que não aceita `&&` nas versões antigas).

**Windows (PowerShell)**

```powershell
git clone https://github.com/agls-scfc/comparador-eleicoes-2026.git
cd comparador-eleicoes-2026
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/validar.py
python -m unittest discover -s tests
cd site
npm ci
npm run dev
```

Se o PowerShell bloquear o `Activate.ps1`, rode antes `Set-ExecutionPolicy -Scope Process Bypass`. Se `py` não existir, use `python`.

**macOS / Linux**

```bash
git clone https://github.com/agls-scfc/comparador-eleicoes-2026.git
cd comparador-eleicoes-2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/validar.py
python3 -m unittest discover -s tests
cd site
npm ci
npm run dev
```

O esperado é `0 erro(s)` no validador e o site em **http://localhost:4321/**.

Comandos do site (rodar dentro de `site/`, iguais em todos os sistemas):

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor local em **modo pré-visualização**: mostra também o que está “em preparação”, com aviso na página. Alterou um YAML em `content/`? Recarregue a página. |
| `npm run build` e depois `npm run preview` | O que seria publicado hoje. Eixos e camadas ainda não marcados como `publicado` aparecem como “em preparação”. |
| `npm run build:preview` e depois `npm run preview` | Site completo, incluindo o que está em preparação. |
| `npm run validar` | Só o validador de trechos literais. |

O `build` roda o validador antes; se algum trecho citado não existir na página do plano, o build falha e indica qual.

Para simular a hospedagem em subpasta (como no GitHub Pages): no PowerShell, `$env:SITE_BASE="/comparador-eleicoes-2026/"` e depois `npm run build` e `npm run preview` (abra `http://localhost:4321/comparador-eleicoes-2026/`); no bash, `SITE_BASE=/comparador-eleicoes-2026/ npm run build`.

## CI e deploy

- **CI** (`.github/workflows/ci.yml`): a cada push em `main` e a cada pull request, roda o validador, os testes e o build com `SITE_BASE=/comparador-eleicoes-2026/`.
- **Deploy** (`.github/workflows/deploy.yml`): publica no GitHub Pages. **Só roda manualmente** (aba Actions > Deploy > *Run workflow*), porque publicar depende de aprovação do mantenedor. Antes do primeiro deploy, ative o Pages em *Settings > Pages > Source: GitHub Actions*. O caminho base vem do próprio Pages, então um domínio próprio passa a funcionar sem mudar o workflow.

O que conferir antes do deploy: (1) a home lista os 14 eixos; (2) em um eixo, os dois lados aparecem com o mesmo critério e o botão “Inverter os lados” funciona; (3) cada trecho abre a página certa no PDF (“ver a página no PDF”); (4) a página Metodologia; (5) celular (modo responsivo do navegador).

## Conferindo as fontes

```bash
pip install -r requirements.txt
python3 scripts/extrair_paginas.py   # regenera o texto por página (confere o sha256 antes)
python3 scripts/verificar_fontes.py  # baixa os PDFs do TSE e compara o sha256
```

Estado atual da verificação: ver `verificado_contra_tse` em [`data/fontes/manifest.yaml`](data/fontes/manifest.yaml).

## Erro ou omissão?

Abra uma *issue* indicando o eixo, a proposta (`id`) e a página do plano. Correções de fato entram com a fonte; discordâncias de opinião não alteram o conteúdo.

## Licenças

Código: MIT ([`LICENSE`](LICENSE)). Curadoria: CC BY 4.0 ([`LICENSE-CONTEUDO.md`](LICENSE-CONTEUDO.md)). Os textos dos planos e os dados de votação pertencem aos seus autores e órgãos de origem.
