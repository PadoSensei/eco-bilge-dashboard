# 🚤 Eco Bilge: AI Research Pipeline

### _Programmatic PRISMA 2020 Implementation for Global Marine Pollution Analysis_

**Eco Bilge** is a specialized "Research Operating System" developed to quantify and validate global oil and detergent pollution estimates from vessels under 400 Gross Tonnage (GT).

By replacing manual bibliometrics with a programmatic pipeline, this project bypasses the "ocean of noise" found in traditional academic databases, identifying high-value data points for statistical meta-analysis in record time.

---

## 🎯 Project Objectives

- **Quantification:** Validate the estimated 2.3 trillion liters of contaminated bilge water discharged annually.
- **Automation:** Use AI to screen thousands of articles based on strict **PICO** (Population, Intervention, Comparison, Outcome) criteria.
- **Scientific Rigor:** Maintain a transparent, unbiased audit trail compliant with the **PRISMA 2020** protocol for high-impact journal publication.
- **Scalability:** Build a modular system that can ingest data from **OpenAlex**, **Scopus**, and **Web of Science**.

---

## 🧠 The Methodology

### 1. Search Strategy (The "Buckets")

We utilize a multi-dimensional search strategy across four technical domains:

- **Population:** Vessels <400 GT, yachts, recreational craft.
- **Exposure:** Oil, TPH, PAH, surfactants, detergents.
- **Process:** Generation rates, discharge volumes, separation systems.
- **Context:** Coastal marinas, estuaries, lagoons.

### 2. AI Screening Logic (PICO Scoring)

Every identified article is scored from **0 to 10** by **Gemini 2.0 Flash** across 5 clinical questions:

- **Q1 (Water):** Direct receptors like marinas/estuaries.
- **Q2 (Vessel):** Specific focus on small craft.
- **Q3 (Quant):** **The Kill Switch.** Presence of hard numerical data (mg/L, ppm, liters).
- **Q4 (Substance):** Specific chemical markers (TPH/PAH).
- **Q5 (Method):** Original empirical studies vs. qualitative reviews.

> **Audit Rule:** If **Q3 = 0**, the article is automatically **EXCLUDED**, regardless of the total score.

---

## 🛠 Tech Stack

- **Data Source:** [OpenAlex API](https://openalex.org) (Open-source index of 250M+ works).
- **AI Engine:** Google Gemini 2.0 Flash (via `google-genai` SDK).
- **Database:** [Supabase](https://supabase.com) (PostgreSQL) for structured storage and audit logs.
- **Dashboard:** [Streamlit](https://streamlit.io) for real-time bilingual (EN/PT) visualization.
- **Language:** Python 3.12+

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/eco-bilge-pipeline.git
cd eco-bilge-pipeline
```

### 2. Set up Virtual Environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory:

```text
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_anon_key"
GEMINI_API_KEY="your_google_gemini_api_key"
OPEN_ALEX_EMAIL="your_email@university.edu"
```

---

## 📈 Pipeline Workflow

1.  **`ingest.py`**: Queries OpenAlex using keyword buckets and stores unique articles in Supabase (Deduplication via DOI).
2.  **`ai_screener.py`**: Batches "Pending" articles to Gemini for PICO scoring.
3.  **`fix_logic.py`**: A Python logic layer that recalculates math and enforces the Q3 Kill Switch to ensure data integrity.
4.  **`app.py`**: Launch the Streamlit dashboard to view results and the PRISMA funnel.

```bash
streamlit run app.py
```

---

## 📊 Current Progress (Phase 1)

- **Articles Identified:** 527
- **AI Exclusions:** ~65% (Filtered noise)
- **Gold Dataset:** 91 Articles ready for Phase 2 (Full-text data extraction).

---

## 👥 Contributors

- **Fina:** Lead Researcher / Environmental Parameters
- **Cléber:** Scientific Advisor / Methodology
- **Patrick:** Pipeline Development / AI Engineering
- **Thiago/Rômulo:** Statistical Validation & Meta-analysis

---

## 📜 License

This project is part of the **Ecobuilders** initiative. Software registration and academic licensing are currently under review.

_Copyright © 2026 - All Rights Reserved._
