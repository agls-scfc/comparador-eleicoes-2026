# Decisões do projeto

Registro das decisões que definem o que o site mostra e como. Toda mudança de regra entra aqui, com data.

- **Mantenedor / tomador de decisões:** Arthur
- **Desenvolvimento (scripts, curadoria de dados, site):** Claude, sob direção do mantenedor
- **Valores:** defesa da democracia e transparência. O site existe para dar acesso a fatos auditáveis, não para orientar voto.

## 1. Decisões do mantenedor

| # | Decisão | Data |
|---|---------|------|
| D1 | O site compara lado a lado as propostas de **Lula** (coligação liderada pelo PT) e **Flávio Bolsonaro** (PL) para a Presidência em 2026. | 2026-10-09 |
| D2 | As propostas vêm **literalmente** dos PDFs de plano de governo do TSE, com link para a página citada. Os PDFs do repo são os da página oficial do TSE; **a página impressa é igual à página do PDF** (offset 0). | 2026-10-09 |
| D3 | Cada **eixo** reúne **várias** propostas e citações, para dar um entendimento geral do tema. | 2026-10-09 |
| D4 | Há 14 eixos. **MVP (8):** segurança pública; economia, impostos e custo de vida; educação; saúde; trabalho, renda e previdência; meio ambiente, clima e energia; instituições, democracia e Judiciário; política externa e defesa. **Fase 2 (6, também entram no produto):** mulheres e igualdade; moradia, cidades e saneamento; agro e segurança alimentar; infraestrutura e transportes; tecnologia e governo digital; cultura e esporte. | 2026-10-09 |
| D5 | Cada eixo tem seção de **falas** (para checar consistência com o plano) e de **ações passadas**. | 2026-10-09 |
| D6 | Ações incluem **como o partido do candidato votou** (Câmara e Senado), não só atos do próprio candidato, e tudo é **claramente rotulado** (quem agiu: candidato, bancada do partido, governo, autoria). | 2026-10-09 |
| D7 | Levantar o **máximo possível** de dados públicos de votação da Câmara e do Senado. | 2026-10-09 |
| D8 | Visual segue as diretrizes de design político do documento do projeto, somadas a pesquisa sobre confiança e relevância. | 2026-10-09 |
| D9 | Claude atua como desenvolvedor de tudo; o mantenedor decide. | 2026-10-09 |

## 2. Padrões de desenvolvimento (propostos pelo desenvolvedor; valem até o mantenedor discordar)

| # | Padrão |
|---|--------|
| P1 | Repositório **público**, para que código e dados também sejam auditáveis. |
| P2 | Scripts em **Python 3**; site estático em **Astro**; conteúdo em **YAML** versionado; identificadores e campos em pt-BR. |
| P3 | Licenças: **MIT** para o código; **CC BY 4.0** para a curadoria (rótulos, classificações, organização). Os trechos dos planos pertencem aos seus autores e são citados como documentos públicos registrados no TSE. |
| P4 | **Ordem dos candidatos:** alfabética pelo nome de urna (Flávio Bolsonaro, depois Lula), igual em todas as páginas, com botão para inverter os lados. Sem cores de partido como identidade visual. |
| P5 | Publicação **por camada** (1 propostas, 2 ações, 3 falas) e **por eixo**, com status visível ("em preparação"). |

## 3. Regras de exibição

1. **Só `compromisso` aparece na comparação principal.** É o que o plano promete fazer.
2. `resultado_declarado` (o que o plano diz que o governo já fez) fica numa seção recolhível, marcada como **não verificada**, a menos que esteja ligada a uma ação verificada.
3. `critica_ao_adversario` **não é exibida**. A metodologia explica o motivo: não é proposta de governo.
4. **Falas** trazem citação curta, data, veículo, contexto e link (com minutagem, quando for vídeo ou áudio). O site **não** classifica uma fala como "coerente" ou "divergente" do plano; mostra os dois lados e deixa o leitor concluir.
5. **Ações** sempre dizem quem agiu (`ator_tipo`): voto do candidato, voto da bancada do partido, ato do governo do candidato ou autoria. Votos usam selos fixos e legenda fixa. Votação simbólica sem voto individual é mostrada como tal, nunca como "apoiou".
6. **Nenhum índice agregado de "alinhamento"** sem método declarado e reproduzível.
7. **Seleção neutra de votações:** parte-se das leis e proposições **citadas pelos próprios planos**, mostrando o voto das duas bancadas em todas elas. Qualquer outra votação entra por critério escrito, aplicado aos dois lados.
8. **Simetria:** nada é publicado para um candidato numa camada e eixo sem o equivalente para o outro. O validador impede isso.

## 4. Regras de integridade dos dados

1. Todo documento citado está em `data/fontes/manifest.yaml`, com URL oficial, `sha256` e página total.
2. Toda proposta tem pelo menos um trecho com documento, página impressa, seção e **literal**.
3. O **validador** (`scripts/validar.py`) falha o build se: o literal não está na página citada; a página não existe; o documento é de outro candidato; falta fonte; `meta.expressao_no_plano` ou `condicionalidade` não aparece num literal; um eixo "publicado" não tem os dois candidatos.
4. O casamento do literal ignora quebras de linha, espaços repetidos, aspas tipográficas e hifens de fim de linha. Quando só casa ignorando hifens, o validador emite **aviso** para revisão humana.
5. **Extração dupla:** cada página é extraída em dois modos (`pdftotext` padrão e `-layout`). O literal precisa casar em pelo menos um; se casar em só um, o validador emite **aviso** e a página deve ser conferida no PDF (caso real: PT p.28, texto justificado embaralhado no modo padrão).
6. **Frases inteiras:** o literal é composto de frases completas, sem cortes internos; `[...]` só entre frases. Retórica ou crítica dentro de uma frase de compromisso permanece, porque é a palavra do plano. Mesmo critério para os dois lados.
7. Um literal cobre **uma página**. Trecho que atravessa páginas vira dois `trechos`.
8. `condicionalidade` é **trecho literal** do plano, não paráfrase.
9. Dados brutos de votação são guardados **como vieram**, com data de coleta, em `data/votacoes/raw/`. A curadoria nunca altera o bruto.

## 5. Limitações conhecidas

- **Hash dos PDFs ainda não conferido contra o TSE.** Os arquivos foram fornecidos pelo mantenedor, que declarou serem os da página oficial. O ambiente de desenvolvimento não alcança `tse.jus.br`. Conferir com `python3 scripts/verificar_fontes.py` e então marcar `verificado_contra_tse: true`.
- **APIs de votação da Câmara e do Senado não são alcançáveis do ambiente de desenvolvimento.** A coleta roda em outro lugar (workflow do GitHub ou máquina do mantenedor).
- Fontes divergem sobre a disponibilidade de votos nominais da Câmara após 2024 e sobre lacunas do Senado em 2015–2018. A coleta registra o estado de cada votação (`nominal`, `simbolica_sem_voto_individual`, `sem_registro`) e a metodologia informa as lacunas.
- Falas e ações ainda em preparação em todos os eixos.

## 6. Em aberto (decisão do mantenedor)

- Confirmar ou trocar a **ordem dos candidatos** (P4).
- Hospedagem e domínio.
- Quem faz a **revisão cruzada** da curadoria antes de cada eixo ser publicado (uma segunda pessoa, idealmente sem filiação declarada).
