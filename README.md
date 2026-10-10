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
