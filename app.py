import streamlit as st
import pandas as pd
import plotly.express as px
import os
import psycopg2
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
st.set_page_config(page_title="Eco Bilge Research OS", layout="wide")

# Connection to Neon
@st.cache_resource
def get_neon_connection():
    return psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))

def fetch_data():
    conn = get_neon_connection()
    query = "SELECT * FROM public.screening_phase_1"
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
        "tabs": ["The Challenge", "Tech & Scalability", "Search Strategy", "The Scoring Logic", "The Vault", "Data Architecture"],
        "t1_h": "The Challenge: Manual Review Bottleneck",
        "t2_h": "Tech Choice: Open Science First",
        "t3_h": "Strategy: The 4 Search Buckets",
        "t4_h": "The Brain: AI-Powered Screening",
        "t5_h": "The Vault: Real-Time Results",
        "stat_total": "Total Screened",
        "stat_pass": "PASS (Gold)",
        "stat_doubt": "DOUBT (Review)",
        "stat_exclude": "EXCLUDED (Noise)",
        "table_h": "Passing Articles",
        "t6_h": "Behind the Scenes: Data Structure"
    },
    "Portuguese": {
        "title": "Eco Bilge: Storyboard do Pipeline de Pesquisa",
        "tabs": ["O Desafio", "Tecnologia e Escala", "Estratégia de Busca", "Lógica de Pontuação", "O Cofre", "Arquitetura de Dados"],
        "t1_h": "O Desafio: O Gargalo da Revisão Manual",
        "t2_h": "Escolha Técnica: Ciência Aberta",
        "t3_h": "Estratégia: Os 4 'Buckets' de Busca",
        "t4_h": "O Cérebro: Triagem por IA",
        "t5_h": "O Cofre: Resultados em Tempo Real",
        "stat_total": "Total Analisado",
        "stat_pass": "PASS (Ouro)",
        "stat_doubt": "DÚVIDA (Revisão)",
        "stat_exclude": "EXCLUÍDOS (Ruído)",
        "table_h": "Artigos Aprovados",
        "t6_h": "Bastidores: Estrutura de Dados"
    }
}

# 3. SIDEBAR
st.sidebar.title("Eco Bilge v1.0")
lang = st.sidebar.radio("Language / Idioma", ["Portuguese", "English"])
c = content[lang]

# 4. TABS (Defined globally for the page)
tabs = st.tabs(c["tabs"])

with tabs[0]:
    st.header(c["t1_h"])

with tabs[1]:
    st.header(c["t2_h"])

with tabs[2]:
    st.header(c["t3_h"])

with tabs[3]:
    st.header(c["t4_h"])

with tabs[4]: # The Vault (Neon Connected)
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

    st.header(c["table_h"])
    display_df = pass_df.sort_values(by='total_score', ascending=False).copy()
    
    # DOI Formatter
    def format_doi(doi):
        if not doi or pd.isna(doi) or doi == 'None': return "N/A"
        if str(doi).startswith("http"): return str(doi)
        if str(doi).startswith("10."): return f"https://doi.org/{doi}"
        return "N/A"
    
    display_df['doi_link'] = display_df['doi'].apply(format_doi)
    st.dataframe(
        display_df[['total_score', 'title', 'doi_link']], 
        use_container_width=True,
        column_config={"doi_link": st.column_config.LinkColumn("DOI")}
    )

with tabs[5]:
    st.header(c["t6_h"])
    st.dataframe(df.head(10), use_container_width=True)