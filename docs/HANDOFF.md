# Handoff — Comparador de propostas, Eleições 2026

Documento para retomar o desenvolvimento em outro chat sem perder contexto. Estado em **15/10/2026** (segundo turno em **25/10/2026**). Leia primeiro `docs/decisions.md` (regras oficiais do projeto) e depois este arquivo (estado e como continuar).

## 1. Quem é quem

- **Arthur** (arthursalazar891@gmail.com; Recife/Fortaleza, fuso America/Fortaleza): mantenedor e tomador de decisões. Estudante de Sistemas de Informação na UFPE.
- **Claude**: desenvolvedor de tudo (scripts, curadoria dos dados, site), sob direção do Arthur. Arthur só decide.
- **Preferências do Arthur:** português do Brasil; respostas concisas e diretas; comandos de terminal agrupados e, para funcionar no PowerShell do Windows, **um por linha, sem `&&`**. Não renomear variáveis nem encher de comentários.
- **Valores do projeto:** defesa da democracia e transparência. O site **não recomenda voto**; mostra fatos auditáveis e onde conferir.

## 2. O que é o produto

Site estático e público que compara lado a lado as propostas de governo de **Lula (PT)** e **Flávio Bolsonaro (PL)** para a Presidência em 2026, com:

1. **Propostas** — trechos **literais** dos PDFs do TSE, com página e link.
2. **Falas** — citações dos candidatos ao longo dos anos (para checar consistência com o plano). **Não** rotuladas como "coerente/divergente".
3. **Ações** — votos do candidato, **votos da bancada do partido** (Câmara e Senado), atos de governo e autoria, sempre dizendo **quem agiu**.

14 eixos (aprovados): **MVP (8)** segurança pública; economia, impostos e custo de vida; educação; saúde; trabalho, renda e previdência; meio ambiente, clima e energia; instituições, democracia e Judiciário; política externa e defesa. **Fase 2 (6)** mulheres e igualdade; moradia, cidades e saneamento; agro e segurança alimentar; infraestrutura e transportes; tecnologia e governo digital; cultura e esporte.

Design: segue o documento do projeto "Identidade visual para campanha política: como o design conquista votos" + pesquisa de confiança. Sem cores de partido como identidade visual.

## 3. Repositório e stack

- **Repo público:** `github.com/agls-scfc/comparador-eleicoes-2026` (branch `main`). Licenças: MIT (código), CC BY 4.0 (curadoria).
- **Site:** Astro 7.4.0 + js-yaml 4.3.2 (Node 22.22+) (CORE_SCHEMA: datas YAML ficam texto). Conteúdo em YAML em `content/<eixo>/`.
- **Scripts:** Python 3 (PyYAML, jsonschema), sempre rodados com `python3 -I`. Testes: `unittest` (46 testes, todos passam).
- **Estrutura:** `data/fontes/` (PDFs + `manifest.yaml`), `data/paginas/<doc>/NNN.txt` (texto por página, extração padrão) e `.../layout/NNN.txt` (modo `-layout`), `schema/*.json`, `scripts/` (`extrair_paginas.py`, `verificar_fontes.py`, `validar.py`, `curadoria/curar.py`), `content/`, `site/`, `docs/`, `tests/`.
- **Rodar localmente:** ver "Rodando localmente" no `README.md` (Windows/PowerShell e macOS/Linux). Resumo: `python3 scripts/validar.py` deve dar `0 erro(s)`; no `site/`: `npm ci` e `npm run dev` (http://localhost:4321/, modo pré-visualização).
- `site/package.json` chama `site/scripts/tarefa.mjs` (tarefas em Node, independentes de sistema). `npm run build` roda o validador antes e falha se um literal não existir na página citada.

### Últimos commits (todos em `main`, enviados)

```
a4be2a3 Curadoria: eixo Política externa e defesa; scripts/curadoria/curar.py
9df46f1 Curadoria: eixo Instituições, democracia e Judiciário
fc2b503 Curadoria: eixo Meio ambiente, clima e energia
79ed5b9 Curadoria: eixo Trabalho, renda e previdência
d998af3 Execução local independente de sistema (Windows/PowerShell)
0bfa015 Curadoria: eixo Saúde; README: passo a passo para rodar localmente
84808b9 Curadoria: eixo Educação
0628e60 Curadoria: eixo Economia, impostos e custo de vida
15fe8bf Site Astro: home por eixos, página de eixo lado a lado e metodologia
22c6d11 Validador de literais, extração dupla e curadoria de Segurança pública
3fce65f Base do projeto: fontes, schemas, decisões e extração por página
```

Trailers obrigatórios nos commits: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` e `Claude-Session: <url da sessão>`. Descrição de PR termina com `🤖 Generated with [Claude Code](https://claude.com/claude-code)` + URL da sessão.

## 4. Estado da curadoria de propostas

Todos os eixos estão com `status: em_preparacao` (nada "publicado" ainda; publicar depende de aprovação do Arthur, ver seção 9).

| # | Eixo | Fase | Lula: compromissos / resultados | Flávio: compromissos / resultados |
|---|------|------|------|------|
| 1 | seguranca-publica | MVP | 16 / 3 | 19 / 0 |
| 2 | economia-impostos-custo-de-vida | MVP | 11 / 3 | 13 / 3 |
| 3 | educacao | MVP | 15 / 4 | 14 / 1 |
| 4 | saude | MVP | 30 / 10 | 17 / 1 |
| 5 | trabalho-renda-previdencia | MVP | 21 / 5 | 16 / 3 |
| 6 | meio-ambiente-clima-energia | MVP | 31 / 10 | 17 / 2 |
| 7 | instituicoes-democracia-judiciario | MVP | 14 / 3 | 13 / 2 |
| 8 | politica-externa-defesa | MVP | 21 / 4 | 10 / 0 |
| 9 | mulheres-igualdade | fase 2 | 44 / 9 | 17 / 1 |
| 10 | moradia-cidades-saneamento | fase 2 | 17 / 9 | 6 / 1 |
| 11 | agro-seguranca-alimentar | fase 2 | 35 / 6 | 11 / 1 |
| 12 | infraestrutura-transportes | fase 2 | 8 / 2 | 14 / 0 |
| 13 | tecnologia-governo-digital | fase 2 | 22 / 1 | 18 / 3 |
| 14 | cultura-esporte | fase 2 | 23 / 9 | 9 / 0 |

Os 14 eixos estão curados (propostas). Os 6 da fase 2 foram curados em 16/10/2026 com a mesma receita (seção 6), seguidos de uma revisão cruzada automática: nenhuma frase do plano aparece em dois registros (mesmo documento e página), em nenhum eixo.

Validador: 0 erros, 5 avisos (2 de hash; 3 de "só casa em layout", todos conferidos visualmente no PDF: PT p.28, PL p.57 e PT p.46).

### Critérios fixados na curadoria da fase 2

- **Mesma promessa repetida pelo plano em duas seções** (ex.: PL p.27 "como detalhado no Brasil que Cresce" e PL p.54): **um registro** com vários `trechos`, não dois registros no mesmo eixo. Em eixos diferentes, a mesma promessa pode aparecer se a frase for outra (ex.: ClarIA e pacotes de internet do PL em mulheres-igualdade, p.18, e em tecnologia, pp.24-25; tornozeleira em segurança e em mulheres).
- **Assistência social (SUAS), idosos, pessoas com deficiência, juventude, infância, povos indígenas e quilombolas**: em mulheres-igualdade.
- **Licenciamento ambiental e segurança jurídica de grandes projetos** (PL pp.49-50): em infraestrutura.
- **ECA Digital** (PT p.24): em tecnologia. **Produção cultural das juventudes** (PT p.25): em cultura-esporte.
- "Gov. br" (PT p.17): o PDF quebra a linha entre "Gov." e "br"; o literal fica com espaço.

### Pontos para a revisão humana (fase 2)

- **Turismo** não tem eixo. Há frases nos dois planos (PT pp.56-57; PL pp.59-60) e partes já estão em meio ambiente e política externa. Decidir se entra em algum eixo.
- `pl-cultura-esporte-006` (categoria feminina disputada por atletas do sexo feminino, PL p.41): tema sensível; rótulo segue o literal.
- `pl-moradia-cidades-saneamento-004`: o trecho da p.48 inclui uma frase retórica inteira porque a sobra da frase anterior ("céu aberto.") tem menos de 12 caracteres.
- `pt-infraestrutura-transportes-009` (PT p.56): literal começa com frase sem verbo principal, como no original.

## 5. Regras de dados (resumo; a versão oficial está em `docs/decisions.md`)

**Exibição**
1. Só `compromisso` aparece na comparação principal.
2. `resultado_declarado` (o que o plano diz que já foi feito) fica recolhível e marcado como **não verificado** até haver ação verificada.
3. `critica_ao_adversario` **não é exibida**.
4. Falas: citação curta + data + veículo + contexto + link (minutagem se áudio/vídeo). Sem rótulo de coerência.
5. Ações dizem sempre `ator_tipo`: `voto_do_candidato`, `voto_da_bancada_do_partido`, `ato_do_governo_do_candidato`, `autoria`. Votação simbólica sem voto individual é mostrada como tal, nunca como "apoiou".
6. Nenhum índice agregado de "alinhamento".
7. Seleção neutra de votações: parte-se das leis citadas pelos **próprios planos**, mostrando as duas bancadas.
8. **Simetria:** camada "publicado" exige ≥1 registro para cada candidato (para propostas só conta `compromisso`).

**Integridade / curadoria**
- Toda proposta tem `trechos[{documento, pagina_impressa, secao, literal}]`; página impressa = página do PDF (offset 0).
- **Frases inteiras**; `[...]` só **entre** frases; mesmo critério para os dois lados; retórica dentro de uma frase de compromisso permanece (é a palavra do plano).
- Trecho que atravessa páginas vira **dois `trechos`** (um por página). Literal mínimo de 12 caracteres; máximo de 900.
- `rotulo`: 3–90 caracteres, **neutro**, sem adjetivo de avaliação (o gerador tem `assert`).
- `meta` só quando o plano traz número/prazo (`expressao_no_plano` precisa estar num literal). `condicionalidade` é **trecho literal** (ex.: "mantida a tarifa social", "sempre condicionado à viabilidade…", "conforme a demanda").
- Extração dupla (padrão e `-layout`): o literal precisa casar em pelo menos um modo; se casar só em um, o validador dá **aviso** e a página deve ser conferida visualmente no PDF.

**Validador (`scripts/validar.py`)** confere: schemas; ids (`^(pt|pl)-<eixo>-NNN`) coerentes com candidato/eixo; ids únicos; documento do mesmo candidato; página no intervalo; literal presente na página (normaliza NFKC, aspas/travessões, espaços, hífen de fim de linha); `meta.expressao_no_plano` e `condicionalidade` dentro de um literal; `proposta_ids` apontando para propostas reais; partido da bancada coerente; simetria; manifesto (sha256, total de páginas).

Estado atual: **0 erros, 4 avisos** — 2 de "hash ainda não conferido contra o TSE", e 2 de "literal só casa em `layout`", ambos **já conferidos visualmente**: `pt-seguranca-publica-008` (PT p.28) e `pl-meio-ambiente-clima-energia-010` (PL p.57).

## 6. Como curar um eixo (receita usada nos 8 eixos prontos)

1. `cat data/paginas/plano-pt-2026/NNN.txt` e `.../plano-pl-2026/NNN.txt` das páginas do eixo (em `content/<eixo>/eixo.yaml`). Use `grep -il` por palavras-chave para achar itens do tema fora do intervalo.
2. Definir 5–8 **tópicos** que sirvam aos dois lados (tópico sem itens de um candidato é aceito; a tela mostra "Nenhuma proposta registrada neste tópico").
3. Escrever um arquivo de especificação **fora do repo** (scratchpad) usando `scripts/curadoria/curar.py`: `R(cand, topico, rotulo, [T(pagina, secao, literal)], tipo, meta, cond)` e `emitir(eixo, topicos, paginas, registros)`. Copiar os literais **exatamente** do texto lido (o texto extraído às vezes embaralha palavras em parágrafos justificados; nesses casos confira no modo layout em `data/paginas/<doc>/layout/NNN.txt`).
4. Rodar o arquivo, depois `python3 -I scripts/validar.py`. Se algum literal falhar, corrigir pelo texto da página (causas comuns: palavra trocada, número da página no meio da frase, ponto final que não existe no original, aspas).
5. Para aviso "só casa em layout": `pdftoppm -f N -l N -r 80 -png data/fontes/proposta-pl.pdf /tmp/x` e olhar a imagem.
6. `python3 -I -m unittest discover -s tests` e commit **um por eixo**: `Curadoria: eixo <Nome>` + contagens + trailers. `git push`.

**Atenção:** `emitir` **reescreve** `propostas.yaml` inteiro e as especificações **não ficam no repo**. Não regerar um eixo já curado; edite o YAML à mão (a fonte de verdade é o YAML).

Critério de seleção usado: compromissos = frases de futuro/intenção do plano ("vamos", "continuaremos", "criaremos", metas); `resultado_declarado` = balanço do que "já fizemos" (com números); críticas e retórica sem proposta ficam de fora. Mesmo critério aplicado aos dois planos.

## 7. Site (resumo técnico)

- `site/src/lib/dados.ts`: lê `content/` e `data/fontes/manifest.yaml`; `CANDIDATOS` em ordem alfabética (Flávio, depois Lula); `visivel(status)` (publicado, ou tudo no modo pré-visualização); `totalCompromissos`; `linksDaPagina` (PDF local `fontes/<arquivo>#page=N` + original TSE `#page=N`).
- Páginas: `index.astro` (grade de eixos; só mostra contagem quando publicado e os dois lados têm propostas), `eixos/[eixo].astro` (tópicos lado a lado, resultados recolhíveis "não verificados", botão **Inverter os lados** com `localStorage` em try/catch, avisos "em preparação" para falas e ações), `metodologia.astro`.
- `PREVIEW=1` (usado por `npm run dev` e `build:preview`) mostra o que ainda não foi publicado; o build normal esconde.
- 16 páginas geradas hoje (home, metodologia, 14 eixos).
- Itens de produto ainda **não** feitos: tela de falas, tela de ações/votos (selos fixos + legenda), busca, versão para impressão, revisão final de design/acessibilidade e teste em celular.

## 8. Ambiente de desenvolvimento (limites que já causaram problema)

- Sessão em container na nuvem; saída de rede **por allowlist**. `tse.jus.br`, Câmara, Senado e Congresso retornam **403** no CONNECT: **não contornar**. npm e pip funcionam. `gh` com token inválido; `git push` funciona pela credencial injetada.
- Por isso **não foi possível conferir o sha256 dos PDFs contra o TSE** nem coletar votações aqui. Isso deve rodar no GitHub Actions ou na máquina do Arthur (`python3 scripts/verificar_fontes.py`).
- Ferramentas: `pdftotext`/`pdftoppm`, Python 3.13, Node 22; Chromium/Playwright em `/opt/npm-tools/node_modules/playwright` com `executablePath: '/opt/pw-browsers/chromium'`.
- **Nunca** use `pkill -f` com padrão que case com o próprio comando (já matou o shell). Para o preview, `nohup` em segundo plano.
- Uma chamada Bash falhou uma vez com "classifier timed out"; repetir resolve.
- Scripts Python rodam com `python3 -I`. Arquivos baixados/extraídos ficam em diretório próprio e não são executados.

## 9. Pendências, em ordem sugerida

1. **Curar os 6 eixos da fase 2**: feito em 16/10/2026 (ver seção 4). Falta a revisão humana dos pontos listados lá.
2. **Camada de falas** (por eixo): pesquisar fontes reais (WebSearch/WebFetch), registrar `fala` com data, veículo, URL e **citação só quando verificada no texto buscado**. Sem inventar nem parafrasear como citação. Schema em `schema/fala.schema.json`; arquivo `content/<eixo>/falas.yaml`; incluir `proposta_ids` apenas para propostas reais (nunca para ids de ação/fala). Falas dos **dois** candidatos, mesmo critério.
3. **Camada de ações/votos** (`content/<eixo>/acoes.yaml`, schema `schema/acao.schema.json`): sementes = leis citadas pelos próprios planos (ex.: Lei Antifacção 2026, PEC da Segurança, reforma tributária, novo arcabouço fiscal, nova lei do ensino médio, MP 871/2019, fim dos descontos associativos do INSS em nov/2025, PEC do fim da reeleição de autoria de Flávio Bolsonaro, escala 6x1 na Câmara). Precisa de **coletor de dados** (APIs da Câmara e do Senado) que rode fora deste ambiente; guardar o **bruto** em `data/votacoes/raw/` com data de coleta; estado do voto: `nominal`, `simbolica_sem_voto_individual` ou `sem_registro`. Há uma divergência não testada entre fontes sobre votos nominais da Câmara depois de maio/2024 (vazio vs. 115 nominais) e lacunas do Senado em 2015–2018: testar na coleta e documentar.
4. **GitHub Actions:** feito. `ci.yml` (validar + testes + build em push/PR) e `deploy.yml` (GitHub Pages, **só manual**, até o Arthur aprovar a publicação). Falta ativar o Pages em *Settings > Pages > Source: GitHub Actions*.
5. **Verificação dos PDFs contra o TSE** e marcar `verificado_contra_tse: true` no manifesto (após conferir os hashes). Em 15/10/2026 o TSE também respondeu **403** ao download automático a partir de uma máquina local (não é só o container), então um workflow de verificação provavelmente seria bloqueado. Caminho: baixar os PDFs pelo navegador e comparar o sha256 (`Get-FileHash` / `sha256sum`).
6. **Revisão cruzada** da curadoria por uma segunda pessoa (idealmente sem filiação declarada) antes de publicar cada eixo.
7. **Publicar eixos:** trocar `status.propostas` para `publicado` em cada `eixo.yaml` (e as outras camadas quando prontas). **Só com aprovação do Arthur.** A simetria é exigida pelo validador.
8. Atualizar `README.md` (tabela de status), `docs/decisions.md` (itens 5 e 6) e a página de metodologia (falas, ações, limites); adicionar página de "como corrigir erros" apontando para as issues.

### Decisões em aberto (do Arthur)

- Confirmar ou trocar a **ordem dos candidatos** (padrão atual: alfabética pelo nome de urna, Flávio antes de Lula, com botão para inverter).
- **Hospedagem e domínio.**
- Quem faz a **revisão cruzada**.
- Aprovar a **publicação** dos eixos do MVP.

## 10. Armadilhas já encontradas

- Texto extraído de parágrafos justificados sai embaralhado no modo padrão (ex.: PT p.28, PL p.57): usar o modo `layout` e conferir visualmente.
- Frases sem ponto final no original (ex.: PL p.26 "…protocolos de segurança", PT p.72 "…proteção contra cheias e enchentes"): o literal **não** leva ponto.
- Uma frase que começa na última linha de uma página e continua na seguinte vira dois trechos, e o trecho curto precisa ter ≥ 12 caracteres (se a sobra tiver menos, não use essa frase).
- O número da página aparece no meio do texto extraído quando a frase atravessa páginas; o literal de cada página não inclui esse número.
- Rótulo > 90 caracteres derruba o gerador (assert) — o esquema também recusa.
- Cabeçalho "P R O G R A M A D E G O V E R N O" aparece no topo das páginas pares do PT; ignore.
- Hifenização em fim de linha ("PPA 2028-\n2031"): o validador tem variantes de junção; escreva o literal como na versão legível.

## 11. Prompt sugerido para iniciar o novo chat

> Você é o desenvolvedor do projeto "site eleições 2026" (repo `agls-scfc/comparador-eleicoes-2026`). Eu, Arthur, decido; você desenvolve tudo. Leia `docs/HANDOFF.md` e `docs/decisions.md` no repositório antes de agir. O MVP de propostas (8 eixos) está curado; continue pelos 6 eixos da fase 2 (um commit por eixo, validador com 0 erros), depois falas e ações, depois workflows e publicação, conforme a seção 9 do handoff. Respostas curtas, em português; comandos um por linha. Não contorne bloqueios de rede; o que não puder ser feito aqui (hash contra o TSE, coleta de votações) vai para GitHub Actions ou para a minha máquina.
