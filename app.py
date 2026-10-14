import streamlit as st
import pandas as pd
import plotly.express as px
import os
import psycopg2
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
st.set_page_config(page_title="Eco Bilge Research OS", layout="wide")

# Connect to Neon
@st.cache_resource
def get_neon_connection():
    # Return the connection object
    return psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))

def fetch_data():
    conn = get_neon_connection()
    
    # 1. Check if connection is closed
    if conn.closed != 0:
        st.cache_resource.clear()  # Clear the bad connection
        conn = get_neon_connection() # Reconnect
        
    # 2. Check if the transaction is aborted (e.g. after a bad query)
    try:
        query = "SELECT * FROM public.screening_phase_1 ORDER BY created_at DESC"
        return pd.read_sql_query(query, conn)
    except psycopg2.InterfaceError:
        # If it failed, clear cache and try one more time
        st.cache_resource.clear()
        conn = get_neon_connection()
        return pd.read_sql_query(query, conn)



# Load data
try:
    df = fetch_data()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

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
        "t2_li": ["Modular Design: The pipeline is 'data-agnostic'.", "Grey Literature: Captures NGO/Port reports.", "Internal Deduplication: Merged at source."],
        "t3_h": "Strategy: The 4 Search Buckets",
        "t3_p1": "Instead of a single search, we cross-reference four distinct technical domains:",
        "t3_b1": "Population: Vessels <400 GT, yachts, recreational craft.",
        "t3_b2": "Exposure: Oil, TPH, PAH, surfactants, detergents.",
        "t3_b3": "Process: Generation rates, discharge volumes, separation systems.",
        "t3_b4": "Context: Coastal marinas, estuaries, lagoons.",
        "t4_h": "The Brain: AI-Powered Screening",
        "t4_p1": "We use Gemini 2.0 Flash to act as a clinical reviewer. Every article is analyzed through a PICO framework:",
        "t4_q1": "Q1 (Water): coastal/marina (2) vs deep sea (0)",
        "t4_q2": "Q2 (Vessel): <400GT (2) vs heavy shipping (0)",
        "t4_q3": "Q3 (Quant): Numbers/Stats (2) vs Policy/Review (0)",
        "t4_q4": "Q4 (Substance): Oil/Detergent (2) vs Metals/Plastics (0)",
        "t4_q5": "Q5 (Method): Empirical study (2) vs News/Editorial (0)",
        "t4_kill": "THE KILL SWITCH: If Q3 = 0, the paper is EXCLUDED.",
        "t5_h": "The Vault: Real-Time Results",
        "stat_total": "Total Screened",
        "stat_pass": "PASS (Gold)",
        "stat_doubt": "DOUBT (Review)",
        "stat_exclude": "EXCLUDED (Noise)",
        "perc_h": "Decision Distribution (%)",
        "table_h": "Passing Articles",
        "t6_h": "Behind the Scenes: Data Structure"
    },
    "Portuguese": {
        "title": "Eco Bilge: Storyboard do Pipeline de Pesquisa",
        "subtitle": "Uma implementação programática do protocolo PRISMA 2020",
        "tabs": ["O Desafio", "Tecnologia e Escala", "Estratégia de Busca", "Lógica de Pontuação", "O Cofre", "Arquitetura de Dados"],
        "t1_h": "O Desafio: O Gargalo da Revisão Manual",
        "t1_p1": "Buscas tradicionais retornaram um 'oceano de ruído' que levaria meses para uma equipe humana revisar manualmente.",
        "t1_p2": "Estamos implementando o **Método PRISMA**. Isso garante que cada decisão seja registrada, criando uma trilha de auditoria transparente.",
        "t2_h": "Escolha Técnica: Ciência Aberta",
        "t2_p1": "Este protótipo é alimentado pelo [OpenAlex](https://openalex.org), um índice de código aberto com 250M+ obras.",
        "t2_p2": "Escalabilidade Futura:",
        "t2_li": ["Design Modular: Pipeline agnóstico a dados.", "Literatura Cinzenta: Relatórios de ONGs/Portos.", "Desduplicação Interna: Mesclagem na origem."],
        "t3_h": "Estratégia: Os 4 'Buckets' de Busca",
        "t3_p1": "Cruzamos quatro domínios técnicos distintos:",
        "t3_b1": "População: Embarcações <400 GT, iates, barcos de lazer.",
        "t3_b2": "Exposição: Óleo, TPH, PAH, detergentes.",
        "t3_b3": "Processo: Taxas de geração, volumes de descarga.",
        "t3_b4": "Contexto: Marinas costeiras, estuários, lagoas.",
        "t4_h": "O Cérebro: Triagem por IA",
        "t4_p1": "Usamos o Gemini 2.0 Flash com framework PICO:",
        "t4_q1": "Q1 (Água): costeira/marina (2) vs mar profundo (0)",
        "t4_q2": "Q2 (Vaso): <400GT (2) vs grandes navios (0)",
        "t4_q3": "Q3 (Quant): Números/Dados (2) vs Política/Revisão (0)",
        "t4_q4": "Q4 (Substância): Óleo/Detergente (2) vs Metais/Plásticos (0)",
        "t4_q5": "Q5 (Método): Estudo empírico (2) vs Notícias/Editorial (0)",
        "t4_kill": "KILL SWITCH: Se Q3 = 0, artigo EXCLUÍDO.",
        "t5_h": "O Cofre: Resultados em Tempo Real",
        "stat_total": "Total Analisado",
        "stat_pass": "PASS (Ouro)",
        "stat_doubt": "DÚVIDA (Revisão)",
        "stat_exclude": "EXCLUÍDOS (Ruído)",
        "perc_h": "Distribuição de Decisões (%)",
        "table_h": "Artigos Aprovados",
        "t6_h": "Bastidores: Estrutura de Dados"
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
    for item in c["t2_li"]: st.write(f"- {item}")

with tabs[2]:
    st.header(c["t3_h"])
    st.write(c["t3_p1"])
    col1, col2 = st.columns(2)
    col1.success(f"🚤 {c['t3_b1']}"); col1.success(f"🧪 {c['t3_b2']}")
    col2.success(f"⚙️ {c['t3_b3']}"); col2.success(f"🌊 {c['t3_b4']}")

with tabs[3]:
    st.header(c["t4_h"])
    st.write(c["t4_p1"])
    st.warning(c["t4_kill"])
    for q in ['t4_q1', 't4_q2', 't4_q3', 't4_q4', 't4_q5']: st.write(f"- {c[q]}")

with tabs[4]:
    pass_df = df[df['decision'] == 'PASS']
    st.header(c["t5_h"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(c["stat_total"], len(df))
    m2.metric(c["stat_pass"], len(pass_df))
    m3.metric(c["stat_doubt"], len(df[df['decision'] == 'DOUBT']))
    m4.metric(c["stat_exclude"], len(df[df['decision'] == 'EXCLUDE']))
    
    st.header(c["table_h"])
    display_df = pass_df.sort_values(by='total_score', ascending=False).copy()
    display_df['doi_link'] = display_df['doi'].apply(lambda x: f"https://doi.org/{x}" if x and str(x).startswith("10.") else "N/A")
    st.dataframe(display_df[['total_score', 'title', 'doi_link']], use_container_width=True, column_config={"doi_link": st.column_config.LinkColumn("DOI")})

with tabs[5]:
    st.header(c["t6_h"])
    st.dataframe(df.head(10), use_container_width=True)