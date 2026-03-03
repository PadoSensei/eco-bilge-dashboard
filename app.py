import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from supabase import create_client

# 1. SETUP
load_dotenv()
st.set_page_config(page_title="Eco Bilge Research OS", layout="wide")

# Connect to Supabase
try:
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
except:
    st.error("Database connection failed. Please check your .env file.")

# 2. BILINGUAL CONTENT DICTIONARY
content = {
    "English": {
        "title": "Eco Bilge: Research Pipeline Storyboard",
        "subtitle": "A programmatic implementation of the PRISMA 2020 protocol",
        "tabs": ["The Challenge", "Tech & Scalability", "Search Strategy", "The Scoring Logic", "The Vault", "Data Architecture"],
        "t1_h": "The Challenge: Manual Review Bottleneck",
        "t1_p1": "Traditional keyword searches returned a massive 'ocean of noise' that would take a human team months to review manually. This creates a significant delay in global statistical validation.",
        "t1_p2": "We are implementing the **PRISMA Method** (Preferred Reporting Items for Systematic reviews and Meta-Analyses). This ensures every decision is recorded, creating a transparent, unbiased, and audit-ready 'Paper Trail' for high-impact journal publication.",
        "t2_h": "Tech Choice: Open Science First",
        "t2_p1": "This prototype is powered by [OpenAlex](https://openalex.org), an open-source index of 250M+ works. We chose it for its high-speed API and lack of restrictive institutional paywalls.",
        "t2_p2": "Future Scalability:",
        "t2_li": [
            "**Modular Design:** The pipeline is 'data-agnostic'. We can plug in Scopus or Web of Science as additional data streams once API access is secured.",
            "**Grey Literature:** OpenAlex captures NGO and Port Authority reports often missed by commercial indexes.",
            "**Internal Deduplication:** Most duplicates are merged at the source, ensuring a cleaner initial pool."
        ],
        "t3_h": "Strategy: The 4 Search Buckets",
        "t3_p1": "Instead of a single search, we cross-reference four distinct technical domains to capture the exact 'Research Gap' identified by the team:",
        "t3_b1": "Bucket 1 (Population): Vessels under 400 GT, yachts, and recreational craft.",
        "t3_b2": "Bucket 2 (Exposure): Chemical markers like TPH, PAH, and detergents.",
        "t3_b3": "Bucket 3 (Process): Generation rates, discharge volumes, and separation systems.",
        "t3_b4": "Bucket 4 (Context): Coastal marinas, estuaries, and lagoon environments.",
        "t4_h": "The Brain: AI-Powered Screening",
        "t4_p1": "We use Gemini 2.0 Flash to act as a clinical reviewer. Every article is analyzed through a 0-10 point PICO framework:",
        "t4_q1": "Q1 (Water): coastal/marina (2) vs deep sea (0)",
        "t4_q2": "Q2 (Vessel): <400GT (2) vs heavy shipping (0)",
        "t4_q3": "Q3 (Quant): Numbers/Stats (2) vs Policy/Review (0)",
        "t4_q4": "Q4 (Substance): Oil/Detergent (2) vs Metals/Plastics (0)",
        "t4_q5": "Q5 (Method): Empirical study (2) vs News/Editorial (0)",
        "t4_kill": "THE KILL SWITCH: If Q3 = 0 (No quantitative data), the paper is EXCLUDED regardless of total score.",
        "t5_h": "The Vault: Real-Time Results",
        "stat_total": "Total Screened",
        "stat_pass": "PASS (Gold)",
        "stat_doubt": "DOUBT (Review)",
        "stat_exclude": "EXCLUDED (Noise)",
        "perc_h": "Decision Distribution (%)",
        "table_h": "Passing Articles (Candidates for Extraction)",
        "t6_h": "Behind the Scenes: Data Structure",
        "t6_p1": "This is a live sample of our Supabase 'Research Vault', where every AI score and reason is documented.",
    },
    "Portuguese": {
        "title": "Eco Bilge: Storyboard do Pipeline de Pesquisa",
        "subtitle": "Uma implementação programática do protocolo PRISMA 2020",
        "tabs": ["O Desafio", "Tecnologia e Escala", "Estratégia de Busca", "Lógica de Pontuação", "O Cofre", "Arquitetura de Dados"],
        "t1_h": "O Desafio: O Gargalo da Revisão Manual",
        "t1_p1": "Buscas tradicionais retornaram um 'oceano de ruído' que levaria meses para uma equipe humana revisar manualmente. Isso cria um atraso na validação estatística global.",
        "t1_p2": "Estamos implementando o **Método PRISMA**. Isso garante que cada decisão seja registrada, criando uma trilha de auditoria transparente, imparcial e pronta para publicação em periódicos de alto impacto.",
        "t2_h": "Escolha Técnica: Ciência Aberta",
        "t2_p1": "Este protótipo é alimentado pelo [OpenAlex](https://openalex.org), um índice de código aberto com 250M+ obras. Escolhemos ele por sua API de alta velocidade e ausência de paywalls institucionais.",
        "t2_p2": "Escalabilidade Futura:",
        "t2_li": [
            "**Design Modular:** O pipeline é 'agnóstico a dados'. Podemos conectar o Scopus ou Web of Science como fluxos adicionais assim que o acesso à API for validado.",
            "**Literatura Cinzenta:** O OpenAlex captura relatórios de ONGs e autoridades portuárias ignorados por índices comerciais.",
            "**Desduplicação Interna:** A maioria das duplicatas é mesclada na origem, garantindo um pool inicial mais limpo."
        ],
        "t3_h": "Estratégia: Os 4 'Buckets' de Busca",
        "t3_p1": "Em vez de uma busca única, cruzamos quatro domínios técnicos distintos para capturar a 'Lacuna de Pesquisa' identificada:",
        "t3_b1": "Bucket 1 (População): Embarcações abaixo de 400 GT, iates e barcos de lazer.",
        "t3_b2": "Bucket 2 (Exposição): Marcadores químicos como TPH, PAH e detergentes.",
        "t3_b3": "Bucket 3 (Processo): Taxas de geração, volumes de descarga e sistemas de separação.",
        "t3_b4": "Bucket 4 (Contexto): Marinas costeiras, estuários e ambientes de lagoas.",
        "t4_h": "O Cérebro: Triagem por IA",
        "t4_p1": "Usamos o Gemini 2.0 Flash como revisor clínico. Cada artigo é analisado através de um framework PICO de 0 a 10 pontos:",
        "t4_q1": "Q1 (Água): costeira/marina (2) vs mar profundo (0)",
        "t4_q2": "Q2 (Vaso): <400GT (2) vs grandes navios (0)",
        "t4_q3": "Q3 (Quant): Números/Dados (2) vs Política/Revisão (0)",
        "t4_q4": "Q4 (Substância): Óleo/Detergente (2) vs Metais/Plásticos (0)",
        "t4_q5": "Q5 (Método): Estudo empírico (2) vs Notícias/Editorial (0)",
        "t4_kill": "KILL SWITCH: Se Q3 = 0 (Sem dados quantitativos), o artigo é EXCLUÍDO independentemente da pontuação.",
        "t5_h": "O Cofre: Resultados em Tempo Real",
        "stat_total": "Total Analisado",
        "stat_pass": "PASS (Ouro)",
        "stat_doubt": "DÚVIDA (Revisão)",
        "stat_exclude": "EXCLUÍDOS (Ruído)",
        "perc_h": "Distribuição de Decisões (%)",
        "table_h": "Artigos Aprovados (Candidatos para Extração)",
        "t6_h": "Bastidores: Estrutura de Dados",
        "t6_p1": "Amostra ao vivo do nosso 'Cofre de Pesquisa' no Supabase, onde cada pontuação e motivo da IA são documentados.",
    }
}

# 3. SIDEBAR
st.sidebar.title("Eco Bilge v1.0")
lang = st.sidebar.radio("Language / Idioma", ["Portuguese", "English"])
c = content[lang]

# 4. TABS
tabs = st.tabs(c["tabs"])

with tabs[0]:
    st.header(c["t1_h"])
    st.write(c["t1_p1"])
    st.info(c["t1_p2"])

with tabs[1]:
    st.header(c["t2_h"])
    st.markdown(c["t2_p1"])
    st.subheader(c["t2_p2"])
    for item in c["t2_li"]:
        st.write(f"- {item}")

with tabs[2]:
    st.header(c["t3_h"])
    st.write(c["t3_p1"])
    col1, col2 = st.columns(2)
    col1.success(f"🚤 {c['t3_b1']}")
    col1.success(f"🧪 {c['t3_b2']}")
    col2.success(f"⚙️ {c['t3_b3']}")
    col2.success(f"🌊 {c['t3_b4']}")

with tabs[3]:
    st.header(c["t4_h"])
    st.write(c["t4_p1"])
    st.warning(c["t4_kill"])
    st.write("---")
    st.write(f"- {c['t4_q1']}")
    st.write(f"- {c['t4_q2']}")
    st.write(f"- {c['t4_q3']}")
    st.write(f"- {c['t4_q4']}")
    st.write(f"- {c['t4_q5']}")

with tabs[4]:
    res = supabase.table("screening_phase_1").select("decision, total_score, title, doi").execute()
    df = pd.DataFrame(res.data)
    
    total = len(df)
    pass_df = df[df['decision'] == 'PASS']
    doubt_df = df[df['decision'] == 'DOUBT']
    exclude_df = df[df['decision'] == 'EXCLUDE']

    st.header(c["t5_h"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(c["stat_total"], total)
    m2.metric(c["stat_pass"], len(pass_df))
    m3.metric(c["stat_doubt"], len(doubt_df))
    m4.metric(c["stat_exclude"], len(exclude_df))

    st.write("---")
    c_left, c_right = st.columns([1.5, 1])
    with c_left:
        funnel_data = dict(
            number=[total, (len(pass_df) + len(doubt_df)), len(pass_df)],
            stage=["Identified", "Screened", "Included"]
        )
        fig = px.funnel(funnel_data, x='number', y='stage', color_discrete_sequence=['#03dac6'])
        st.plotly_chart(fig, use_container_width=True)
    with c_right:
        st.subheader(c["perc_h"])
        pie_df = df['decision'].value_counts().reset_index()
        fig_pie = px.pie(pie_df, values='count', names='decision', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.write("---")
    st.header(c["table_h"])
    display_df = pass_df.sort_values(by='total_score', ascending=False).copy()
    def format_doi(doi):
        if not doi or pd.isna(doi) or doi == 'None': return "N/A"
        if str(doi).startswith("http"): return str(doi)
        if str(doi).startswith("10."): return f"https://doi.org/{doi}"
        return "N/A"
    display_df['doi_link'] = display_df['doi'].apply(format_doi)
    st.dataframe(display_df[['total_score', 'title', 'doi_link']], use_container_width=True, hide_index=True,
        column_config={"doi_link": st.column_config.LinkColumn("DOI Link")})

with tabs[5]:
    st.header(c["t6_h"])
    st.write(c["t6_p1"])
    raw_sample = supabase.table("screening_phase_1").select(
        "title, doi, q1_score, q2_score, q3_score, q4_score, q5_score, total_score, decision, exclusion_reason"
    ).limit(5).execute()
    st.dataframe(pd.DataFrame(raw_sample.data), use_container_width=True)