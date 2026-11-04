"""
migrate_schema_16col.py
=======================
Schema Migration & Baseline Seeding Script for EcoBilge Research Pipeline.

16-Column Layout:
['ID', 'Category', 'Item', 'Company or publisher', 'Figure', 'Unit', 'Technology',
 'Target vessels', 'Price', 'Country', 'Year', 'Source type', 'Link', 'Found by',
 'What it means for EcoBilge', 'Gap?']

- Seeds Fina's 7 manual baseline rows with exact mappings (Found by = 'Manual').
- Migrates legacy dataset from snapshot/database with Found by = 'Script'.
- Saves result to data/eco_bilge_phase1_16col.csv as offline/resilient storage.
- If NEON_CONNECTION_STRING is present, runs PostgreSQL DDL/DML to update the remote database.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

COLUMNS_16 = [
    "ID",
    "Category",
    "Item",
    "Company or publisher",
    "Figure",
    "Unit",
    "Technology",
    "Target vessels",
    "Price",
    "Country",
    "Year",
    "Source type",
    "Link",
    "Found by",
    "What it means for EcoBilge",
    "Gap?"
]

# Fina's exact 7 manual baseline rows
BASELINE_ROWS = [
    {
        "ID": 1,
        "Category": "Competitors",
        "Item": "PureBilge Compact",
        "Company or publisher": "Alfa Laval",
        "Figure": "600",
        "Unit": "l/h",
        "Technology": "Centrifuge",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "n/a",
        "Year": "n/a",
        "Source type": "n/a",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "Benchmark compact centrifuge separation",
        "Gap?": "No"
    },
    {
        "ID": 2,
        "Category": "Competitors",
        "Item": "MiniBOSS",
        "Company or publisher": "Wave International",
        "Figure": "0.5",
        "Unit": "m³/h",
        "Technology": "Filter",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "n/a",
        "Year": "n/a",
        "Source type": "n/a",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "Recreational boat filter benchmark",
        "Gap?": "No"
    },
    {
        "ID": 3,
        "Category": "Competitors",
        "Item": "BISEP19",
        "Company or publisher": "Vetus",
        "Figure": "95",
        "Unit": "% oil removed",
        "Technology": "Filter",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "n/a",
        "Year": "n/a",
        "Source type": "n/a",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "Pleasure craft inline bilge filter benchmark",
        "Gap?": "No"
    },
    {
        "ID": 4,
        "Category": "Competitors",
        "Item": "US5277797A",
        "Company or publisher": "US patent",
        "Figure": "n/a",
        "Unit": "n/a",
        "Technology": "Separator",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "n/a",
        "Year": "n/a",
        "Source type": "n/a",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "Gravity oil-water separation patent reference",
        "Gap?": "No"
    },
    {
        "ID": 5,
        "Category": "Competitors",
        "Item": "Prices of products 1 to 3",
        "Company or publisher": "n/a",
        "Figure": "n/a",
        "Unit": "EUR",
        "Technology": "n/a",
        "Target vessels": "n/a",
        "Price": "Not public",
        "Country": "n/a",
        "Year": "n/a",
        "Source type": "n/a",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "Price comparison not yet possible",
        "Gap?": "Yes"
    },
    {
        "ID": 6,
        "Category": "Fleet",
        "Item": "Sport and leisure boats, Germany",
        "Company or publisher": "Federal Ministry of Transport",
        "Figure": "370,000",
        "Unit": "boats",
        "Technology": "n/a",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "Germany",
        "Year": "No year given",
        "Source type": "Estimate",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "An expert estimate, not a count",
        "Gap?": "No"
    },
    {
        "ID": 7,
        "Category": "Fleet",
        "Item": "Recreational boats, Germany",
        "Company or publisher": "EU Commission study, via Yacht",
        "Figure": "480,000",
        "Unit": "boats",
        "Technology": "n/a",
        "Target vessels": "n/a",
        "Price": "n/a",
        "Country": "Germany",
        "Year": "2025",
        "Source type": "Secondary",
        "Link": "n/a",
        "Found by": "Manual",
        "What it means for EcoBilge": "110,000 more than the ministry; log both",
        "Gap?": "Yes"
    }
]

def load_legacy_data():
    """Finds available legacy snapshot data to migrate."""
    candidates = [
        "data/eco_bilge_screening_snapshot_2026_03_03.csv",
        "eco_bilge_disciplined_2026_07_01.csv"
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"📄 Found legacy dataset at: {path}")
            return pd.read_csv(path)
    return pd.DataFrame()

def migrate_to_16_columns(legacy_df):
    """Transforms legacy dataset and prefixes Fina's 7 manual baseline rows."""
    migrated_rows = []

    # Add the 7 baseline rows first
    for row in BASELINE_ROWS:
        migrated_rows.append(row.copy())

    start_id = 8
    if not legacy_df.empty:
        for idx, row in legacy_df.iterrows():
            item_title = row.get("title") or row.get("name") or "n/a"

            raw_doi = str(row.get("doi") or "")
            link = row.get("url") or ("https://doi.org/" + raw_doi if raw_doi and raw_doi.startswith("10.") else raw_doi)
            if not link or link == "nan":
                link = "n/a"

            source_type = row.get("source_database") or row.get("journal") or "n/a"
            country = row.get("country") or "n/a"

            migrated_rows.append({
                "ID": start_id,
                "Category": "Academic Research",
                "Item": item_title,
                "Company or publisher": row.get("journal", "n/a") if pd.notna(row.get("journal")) else "n/a",
                "Figure": "n/a",
                "Unit": "n/a",
                "Technology": "n/a",
                "Target vessels": "n/a",
                "Price": "n/a",
                "Country": country if pd.notna(country) and str(country).strip() else "n/a",
                "Year": str(row.get("date", "n/a"))[:4] if pd.notna(row.get("date")) else "n/a",
                "Source type": source_type if pd.notna(source_type) else "n/a",
                "Link": link,
                "Found by": "Script",
                "What it means for EcoBilge": row.get("exclusion_reason") or "Legacy screened record",
                "Gap?": "No"
            })
            start_id += 1

    df_16 = pd.DataFrame(migrated_rows, columns=COLUMNS_16)
    return df_16

def run_neon_migration(df_16):
    """Executes ALTER TABLE / CREATE TABLE in Neon PostgreSQL if connection is provided."""
    neon_url = os.getenv("NEON_CONNECTION_STRING")
    if not neon_url:
        print("ℹ️ NEON_CONNECTION_STRING not configured; skipping remote PostgreSQL push.")
        return

    try:
        import psycopg2
        from psycopg2.extras import execute_values
        print("🔌 Connecting to Neon PostgreSQL...")
        conn = psycopg2.connect(neon_url)
        cur = conn.cursor()

        # DDL: Create the 16-column table if not exists
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.eco_bilge_phase1_16col (
            id SERIAL PRIMARY KEY,
            category TEXT,
            item TEXT,
            company_or_publisher TEXT,
            figure TEXT,
            unit TEXT,
            technology TEXT,
            target_vessels TEXT,
            price TEXT,
            country TEXT,
            year TEXT,
            source_type TEXT,
            link TEXT,
            found_by TEXT,
            what_it_means_for_ecobilge TEXT,
            gap TEXT
        );
        """
        cur.execute(create_table_sql)
        conn.commit()
        print("✅ Remote table 'public.eco_bilge_phase1_16col' verified/created.")

        # Insert or update baseline and records
        insert_sql = """
        INSERT INTO public.eco_bilge_phase1_16col (
            id, category, item, company_or_publisher, figure, unit, technology,
            target_vessels, price, country, year, source_type, link, found_by,
            what_it_means_for_ecobilge, gap
        ) VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            category = EXCLUDED.category,
            item = EXCLUDED.item,
            company_or_publisher = EXCLUDED.company_or_publisher,
            figure = EXCLUDED.figure,
            unit = EXCLUDED.unit,
            technology = EXCLUDED.technology,
            target_vessels = EXCLUDED.target_vessels,
            price = EXCLUDED.price,
            country = EXCLUDED.country,
            year = EXCLUDED.year,
            source_type = EXCLUDED.source_type,
            link = EXCLUDED.link,
            found_by = EXCLUDED.found_by,
            what_it_means_for_ecobilge = EXCLUDED.what_it_means_for_ecobilge,
            gap = EXCLUDED.gap;
        """
        tuples = [
            (
                int(r["ID"]), r["Category"], r["Item"], r["Company or publisher"],
                r["Figure"], r["Unit"], r["Technology"], r["Target vessels"],
                r["Price"], r["Country"], r["Year"], r["Source type"],
                r["Link"], r["Found by"], r["What it means for EcoBilge"], r["Gap?"]
            ) for _, r in df_16.iterrows()
        ]
        execute_values(cur, insert_sql, tuples)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Neon PostgreSQL database successfully synced with 16-column dataset.")
    except Exception as e:
        print(f"⚠️ Remote migration encountered error: {e}")

def main():
    print("🚀 Starting Schema Migration & Baseline Seeding...")
    os.makedirs("data", exist_ok=True)

    legacy_df = load_legacy_data()
    print(f"📊 Loaded {len(legacy_df)} legacy rows.")

    df_16 = migrate_to_16_columns(legacy_df)
    output_path = "data/eco_bilge_phase1_16col.csv"
    df_16.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"💾 Successfully saved {len(df_16)} rows to '{output_path}'.")

    # Display the first 7 rows to verify baseline seeding
    print("\n🔍 Verification of Seeded Baseline Rows (1-7):")
    print(df_16.head(7)[["ID", "Category", "Item", "Company or publisher", "Figure", "Unit", "Found by", "Gap?"]])

    # Attempt remote sync if environment configured
    run_neon_migration(df_16)
    print("\n🏁 Migration and Seeding Complete!")

if __name__ == "__main__":
    main()
