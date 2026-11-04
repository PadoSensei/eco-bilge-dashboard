import os
import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv

from validation import evaluate_baselines

# 1. SETUP
load_dotenv()
st.set_page_config(page_title="Eco Bilge Research OS", layout="wide")

CSV_FALLBACK_PATH = "data/eco_bilge_phase1_16col.csv"

# Connect to Neon
@st.cache_resource
def get_neon_connection():
    neon_url = os.getenv("NEON_CONNECTION_STRING")
    if not neon_url:
        return None
    try:
        return psycopg2.connect(neon_url)
    except Exception as e:
        st.sidebar.warning(f"Database connection offline, using CSV fallback: {e}")
        return None

def fetch_data():
    conn = get_neon_connection()
    if conn is not None:
        try:
            if conn.closed != 0:
                st.cache_resource.clear()
                conn = get_neon_connection()
            query = "SELECT * FROM public.eco_bilge_phase1_16col ORDER BY id ASC"
            remote_df = pd.read_sql_query(query, conn)
            # Rename postgres snake_case to Fina's exact 16 columns if needed
            col_map = {
                "id": "ID", "category": "Category", "item": "Item",
                "company_or_publisher": "Company or publisher", "figure": "Figure",
                "unit": "Unit", "technology": "Technology", "target_vessels": "Target vessels",
                "price": "Price", "country": "Country", "year": "Year",
                "source_type": "Source type", "link": "Link", "found_by": "Found by",
                "what_it_means_for_ecobilge": "What it means for EcoBilge", "gap": "Gap?"
            }
            remote_df = remote_df.rename(columns=col_map)
            return remote_df
        except Exception:
            # Table might not exist yet on Neon; fallback to CSV
            pass

    # CSV Fallback for local coaching & offline mode
    if os.path.exists(CSV_FALLBACK_PATH):
        return pd.read_csv(CSV_FALLBACK_PATH)

    # Legacy fallback if 16-col hasn't been generated
    legacy_path = "data/eco_bilge_screening_snapshot_2026_03_03.csv"
    if os.path.exists(legacy_path):
        return pd.read_csv(legacy_path)

    raise FileNotFoundError("Neither Neon DB nor local CSV data file could be found.")

# Load data safely
try:
    df = fetch_data()
except Exception as e:
    st.error(f"Data loading failed: {e}")
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
        "t5_h": "The Vault: Real-Time Results & Baseline Inventory",
        "stat_total": "Total Records",
        "stat_manual": "Manual Baseline",
        "stat_script": "Automated (Script)",
        "stat_gaps": "Identified Research Gaps",
        "table_h": "Integrated Research Inventory (16-Column Layout)",
        "table_sub": "💡 Manual baseline rows seeded by Fina are highlighted in amber. New automated script records populate around them.",
        "filter_cat": "Filter by Category:",
        "filter_found": "Filter by Origin (Found by):",
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
        "t5_h": "O Cofre: Resultados em Tempo Real & Linha de Base",
        "stat_total": "Total de Registros",
        "stat_manual": "Linha de Base Manual",
        "stat_script": "Automatizados (Script)",
        "stat_gaps": "Lacunas Identificadas (Gaps)",
        "table_h": "Inventário Integrado de Pesquisa (Layout 16 Colunas)",
        "table_sub": "💡 As linhas manuais de referência inseridas por Fina estão destacadas em âmbar. Novos registros automatizados aparecem ao redor.",
        "filter_cat": "Filtrar por Categoria:",
        "filter_found": "Filtrar por Origem (Found by):",
        "t6_h": "Bastidores: Estrutura de Dados"
    }
}

# 3. SIDEBAR
st.sidebar.title("Eco Bilge v2.0")
lang = st.sidebar.radio("Language / Idioma", ["Portuguese", "English"])
c = content[lang]

# 3.1 PAUL CHECK BASELINE VALIDATION (Top of Dashboard)
validation_results = evaluate_baselines(df)
matched_x = validation_results["matched_count"]

if lang == "Portuguese":
    v_label = "Validação de Linha de Base (Alvo: 4)"
    v_delta = "Concorrentes conhecidos encontrados"
else:
    v_label = "Baseline Validation (Target: 4)"
    v_delta = "Known competitors found"

st.metric(
    label=v_label,
    value=f"{matched_x}/4",
    delta=v_delta
)

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
    st.header(c["t5_h"])
    
    # 16-Column Layout Presentation with Highlighting
    has_16_cols = "Found by" in df.columns

    if has_16_cols:
        manual_count = len(df[df["Found by"] == "Manual"])
        script_count = len(df[df["Found by"] == "Script"])
        gaps_count = len(df[df["Gap?"] == "Yes"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(c["stat_total"], len(df))
        m2.metric(c["stat_manual"], manual_count)
        m3.metric(c["stat_script"], script_count)
        m4.metric(c["stat_gaps"], gaps_count)

        st.subheader(c["table_h"])
        st.caption(c["table_sub"])

        # Interactive Filtering
        col_f1, col_f2 = st.columns(2)
        categories = ["All"] + sorted([x for x in df["Category"].dropna().unique()])
        selected_cat = col_f1.selectbox(c["filter_cat"], categories)

        origins = ["All"] + sorted([x for x in df["Found by"].dropna().unique()])
        selected_origin = col_f2.selectbox(c["filter_found"], origins)

        filtered_df = df.copy()
        if selected_cat != "All":
            filtered_df = filtered_df[filtered_df["Category"] == selected_cat]
        if selected_origin != "All":
            filtered_df = filtered_df[filtered_df["Found by"] == selected_origin]

        # Highlight manual rows with amber tint
        def highlight_manual_rows(row):
            if row.get("Found by") == "Manual":
                return ["background-color: rgba(255, 193, 7, 0.25); font-weight: bold"] * len(row)
            return [""] * len(row)

        styled_df = filtered_df.style.apply(highlight_manual_rows, axis=1)

        column_config = {}
        if "Link" in filtered_df.columns:
            column_config["Link"] = st.column_config.LinkColumn("Link / DOI")

        st.dataframe(styled_df, use_container_width=True, column_config=column_config)
    else:
        # Fallback view for legacy schema
        pass_df = df[df['decision'] == 'PASS'] if 'decision' in df.columns else df
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Screened", len(df))
        m2.metric("PASS", len(pass_df))
        m3.metric("DOUBT", len(df[df['decision'] == 'DOUBT']) if 'decision' in df.columns else 0)
        st.dataframe(df, use_container_width=True)

with tabs[5]:
    st.header(c["t6_h"])
    st.write("Current Schema Details:")
    st.write(f"Columns ({len(df.columns)}): `{list(df.columns)}`")
    st.dataframe(df.head(10), use_container_width=True)
