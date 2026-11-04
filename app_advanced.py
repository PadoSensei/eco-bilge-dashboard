"""
Eco Bilge: Advanced Research OS Dashboard (Hour 9 Prep)

Features:
- Category Data Tabs: st.tabs() separating the 5 keyword categories:
  [Competitors, Fleet, Pollution, Rules, Customers]
- PRISMA Funnel Chart: Plotly attrition visualization
  (Identified -> Screened Out -> Relevant to EcoBilge)
- Interactive rule configuration viewer
- Fallback data support for offline coaching
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv

from prisma_screener import load_screening_rules
from validation import evaluate_baselines

# 1. SETUP & CONFIGURATION
load_dotenv()
st.set_page_config(page_title="Eco Bilge: Advanced PRISMA Pipeline", layout="wide")

CSV_FALLBACK_PATH = "data/eco_bilge_phase1_16col.csv"

# 2. DATABASE / CSV DATA LOADER
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

def fetch_data() -> pd.DataFrame:
    conn = get_neon_connection()
    if conn is not None:
        try:
            if conn.closed != 0:
                st.cache_resource.clear()
                conn = get_neon_connection()
            query = "SELECT * FROM public.eco_bilge_phase1_16col ORDER BY id ASC"
            remote_df = pd.read_sql_query(query, conn)
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
            pass

    if os.path.exists(CSV_FALLBACK_PATH):
        return pd.read_csv(CSV_FALLBACK_PATH)

    legacy_path = "data/eco_bilge_screening_snapshot_2026_03_03.csv"
    if os.path.exists(legacy_path):
        return pd.read_csv(legacy_path)

    raise FileNotFoundError("Neither Neon DB nor local CSV data file could be found.")

try:
    df = fetch_data()
except Exception as e:
    st.error(f"Data loading failed: {e}")
    st.stop()

# 3. SIDEBAR CONTROLS & SCREENING PROMPT INSPECTOR
st.sidebar.title("🚤 Eco Bilge Advanced")
st.sidebar.caption("PRISMA Systematic Review & 5-Category Architecture")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Active Screening Rules")
default_rules = load_screening_rules()

include_rule_input = st.sidebar.text_area(
    "Inclusion Criteria:",
    value=default_rules.get("include_rules", ""),
    height=90,
    help="Rules passed into the PRISMA LLM prompt wrapper."
)
exclude_rule_input = st.sidebar.text_area(
    "Exclusion Criteria:",
    value=default_rules.get("exclude_rules", ""),
    height=90,
    help="Rules used to disqualify non-target vessels or deep-sea scopes."
)

# Baseline target verification
validation_results = evaluate_baselines(df)
matched_count = validation_results["matched_count"]
st.sidebar.metric(
    label="Baseline Validation Target",
    value=f"{matched_count}/4",
    delta="Verified Target Competitors"
)

# 4. MAIN HEADER & PRISMA FUNNEL ATTRITION SECTION
st.title("🌊 Eco Bilge Research Operating System")
st.markdown("### *Advanced PRISMA 2020 Attrition & 5-Category Evidence Vault*")

col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
col_metric1.metric("Total Records Ingested", len(df))
col_metric2.metric("Manual Benchmarks", len(df[df.get("Found by", "") == "Manual"]))
col_metric3.metric("Automated Scripts", len(df[df.get("Found by", "") == "Script"]))
col_metric4.metric("Identified Research Gaps", len(df[df.get("Gap?", "") == "Yes"]))

st.markdown("---")

# PRISMA FUNNEL CHART BOILERPLATE
st.subheader("📊 PRISMA 2020 Systematic Review Funnel")
st.caption("Visualizing publication attrition from multi-source search to gold data extraction.")

funnel_stages = [
    "1. Records Identified (OpenAlex / Patents / Fleet)",
    "2. Filtered Out by PRISMA Rules (Tankers / Cargo >400 GT)",
    "3. Relevant to EcoBilge (Included for Synthesis)"
]
# Hardcoded boilerplate attrition counts for Hour 9 coaching prep
funnel_counts = [500, 300, 200]

funnel_fig = go.Figure(go.Funnel(
    y=funnel_stages,
    x=funnel_counts,
    textinfo="value+percent initial",
    marker={
        "color": ["#1f77b4", "#ff7f0e", "#2ca02c"],
        "line": {"width": 1, "color": "#444"}
    },
    connector={"line": {"color": "#888", "dash": "dot", "width": 1}}
))

funnel_fig.update_layout(
    margin=dict(l=40, r=40, t=20, b=20),
    height=320,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

col_chart, col_explain = st.columns([2, 1])
with col_chart:
    st.plotly_chart(funnel_fig, use_container_width=True)
with col_explain:
    st.info(
        "**PRISMA Attrition Highlights:**\n\n"
        f"- **Initial Retrieval:** {funnel_counts[0]} papers across all 5 keyword sets.\n"
        f"- **Screened Out:** {funnel_counts[1]} excluded by LLM screener rules.\n"
        f"- **Included:** {funnel_counts[2]} retained for meta-analysis.\n\n"
        "*Note: Dummy attrition figures will be connected to live AI screener logs in Hour 7.*"
    )

st.markdown("---")

# 5. FIVE CATEGORY DATA TABS (HOUR 9 ARCHITECTURE)
st.subheader("📑 5 Keyword Sets & Category Evidence Vault")
st.caption("Explore records partitioned across Fina's 5 core research categories.")

CATEGORIES = ["Competitors", "Fleet", "Pollution", "Rules", "Customers"]
tabs = st.tabs([f"📂 {cat}" for cat in CATEGORIES])

def render_category_tab(category_name: str):
    cat_df = df[df["Category"].astype(str).str.strip().str.lower() == category_name.lower()]

    # Also support alias or fallback category mapping
    if cat_df.empty and category_name == "Pollution":
        # 'Academic Research' in phase 1 16-col corresponds to Pollution studies
        cat_df = df[df["Category"].astype(str).str.strip().str.lower() == "academic research"]

    st.markdown(f"#### **{category_name} Evidence & Data Points**")

    if cat_df.empty:
        st.info(f"No records harvested yet for **{category_name}**. This category bucket will populate during Hour 8 keyword expansion.")
        st.dataframe(pd.DataFrame(columns=df.columns), use_container_width=True)
        return

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Category Records", len(cat_df))
    col_stat2.metric("Script Harvested", len(cat_df[cat_df.get("Found by", "") == "Script"]))
    col_stat3.metric("Research Gaps", len(cat_df[cat_df.get("Gap?", "") == "Yes"]))

    def highlight_manual(row):
        if row.get("Found by") == "Manual":
            return ["background-color: rgba(255, 193, 7, 0.25); font-weight: bold"] * len(row)
        return [""] * len(row)

    styled_df = cat_df.style.apply(highlight_manual, axis=1)

    column_config = {}
    if "Link" in cat_df.columns:
        column_config["Link"] = st.column_config.LinkColumn("Link / DOI")

    st.dataframe(styled_df, use_container_width=True, column_config=column_config)

for idx, category in enumerate(CATEGORIES):
    with tabs[idx]:
        render_category_tab(category)
