📋 Protocolo de Triagem: Fase 1 (Títulos)

Projeto: Eco-Bilge Dashboard / Automação SLR
Metodologia: PRISMA / PICO
Versão: 1.0 (Março 2026)
🎯 Lógica do Sistema de Pontuação

A triagem inicial é baseada nos elementos PICO mapeados a partir do título do artigo. Cada artigo pode somar até 10 pontos.
PONTUAÇÃO DECISÃO ENCAMINHAMENTO
8 – 10 pontos ✅ AVANÇAR Prossegue para Fase 2 (Análise do Abstract)
5 – 7 pontos ⚠️ DÚVIDA Requer revisão por um segundo avaliador humano
0 – 4 pontos ❌ EXCLUIR Artigo descartado; motivo registrado no log PRISMA

    [!IMPORTANT]
    REGRA ABSOLUTA (Kill Switch): Se Q3 = 0 (ausência de dados quantitativos), o artigo é EXCLUÍDO IMEDIATAMENTE, independentemente da pontuação total. Isso ocorre porque o desfecho (Outcome) não atende aos requisitos da meta-análise.

🔍 As 5 Questões de Classificação
Q1 — Elemento P (Population): Corpo d'água receptor

Avalia se o ambiente é um receptor direto de poluição por atividade náutica.

    2 Pontos (Sim): Menciona explicitamente laguna, mar costeiro, rio, estuário, marina, porto ou zona portuária.

    1 Ponto (Parcial): Termos genéricos como "ambiente aquático", "água" ou "sistema costeiro".

    0 Pontos (Não): Ambiente terrestre, solo, atmosfera, laboratório puro ou águas profundas sem conexão náutica.

Q2 — Elemento I (Intervention): Embarcações / Atividade Náutica

Identifica se a fonte poluidora são embarcações ou tráfego marítimo.

    2 Pontos (Sim): Menciona barcos, navios, boating, vessels, ships, bilge water, recreational craft, etc.

    1 Ponto (Parcial): Menciona tráfego marítimo ou atividade portuária/marina onde a fonte é implícita.

    0 Pontos (Não): Fonte terrestre (indústria, agricultura, esgoto urbano) ou fonte não identificada.

Q3 — Elemento O (Outcome): Dados Quantitativos (CRÍTICA) ⚠️

Avalia se o desfecho é mensurável e extraível para meta-análise.

    2 Pontos (Sim): Termos de medição: concentration, discharge, volume, load, level, measurement, ppm, mg/L.

    1 Ponto (Parcial): Termos genéricos como "pollution", "contamination" ou "impact" sem especificar a abordagem.

    0 Pontos (Não): Abordagem qualitativa: governance, policy, management, review, perception, legal framework, case study. (GATILHO DE EXCLUSÃO)

Q4 — Elemento I+O (Substância): Óleo ou Detergentes

Foco específico em hidrocarbonetos e surfactantes.

    2 Pontos (Sim): Menciona oil, petroleum, hydrocarbon, TPH, PAH, bilge, fuel, diesel, detergent, surfactant, dispersant.

    1 Ponto (Parcial): Menciona "pollution" ou "contamination" sem especificar a substância química.

    0 Pontos (Não): Outros poluentes (metais pesados, plásticos, ruído, espécies invasoras, esgoto).

Q5 — Elemento Metodológico: Tipo de Estudo

Avalia o rigor e a origem do dado.

    2 Pontos (Sim): Artigo empírico original em periódico revisado por pares (field study, experimental, monitoring).

    1 Ponto (Parcial): Revisão sistemática, meta-análise, tese acadêmica ou relatório técnico de órgãos oficiais (IMO, EPA).

    0 Pontos (Não): Editorial, carta ao editor, notícia, blog, resumo de congresso ou revisão narrativa qualitativa.

📝 Modelo de Ficha de Triagem (Para Registro)
code Text

ID: [Inserir ID/DOI]
Título: [Inserir Título Original]
Base: [OpenAlex/Scopus/WoS]

[ ] Q1: Receptor (0-2)
[ ] Q2: Fonte (0-2)
[ ] Q3: Quantitativo (0-2) ⚠️ (Se 0 = EXCLUIR)
[ ] Q4: Substância (0-2)
[ ] Q5: Metodologia (0-2)

TOTAL: [ ] / 10

DECISÃO: [PASS / DOUBT / EXCLUDE]
MOTIVO: ****************\_****************
