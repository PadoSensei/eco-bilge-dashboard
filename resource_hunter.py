"""
resource_hunter.py
==================
OpenAlex Multi-Pass Harvesting Engine for EcoBilge Research Pipeline.

Implements Fina's 3 distinct passes:
- Pass 1 (Products): ("bilge water" OR "oily bilge" OR "bilge oil") AND
                    (separator OR filter OR treatment OR "oil removal") AND
                    (boat OR yacht OR "small vessel" OR "recreational craft" OR marina OR "fishing vessel")
- Pass 2 (Exclusions): ("oily water separator" OR "bilge separator")
                      NOT (tanker OR "cargo ship" OR "offshore platform")
                      (Positive broad query via OpenAlex API, programmatically filtered in Python post-fetch)
- Pass 3 (Method): ("gravity separator" OR "gravity separation" OR coalescing) AND
                  (bilge OR "oily water") AND
                  (boat OR vessel)

Schema: Standard 16-Column Layout
Appends unique records directly into data/eco_bilge_phase1_16col.csv
and optionally syncs to Neon DB.
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OPEN_ALEX_EMAIL = os.getenv("OPEN_ALEX_EMAIL", "padraigo.donoghue@gmail.com")
BASE_URL = "https://api.openalex.org/works"
CSV_PATH = "data/eco_bilge_phase1_16col.csv"

COLUMNS_16 = [
    "ID", "Category", "Item", "Company or publisher", "Figure", "Unit",
    "Technology", "Target vessels", "Price", "Country", "Year",
    "Source type", "Link", "Found by", "What it means for EcoBilge", "Gap?"
]

PASS_DEFINITIONS = [
    {
        "pass_name": "Pass 1 (Products)",
        "query": 'title_and_abstract.search:("bilge water" OR "oily bilge" OR "bilge oil") AND (separator OR filter OR treatment OR "oil removal") AND (boat OR yacht OR "small vessel" OR "recreational craft" OR marina OR "fishing vessel")',
        "exclusions": []
    },
    {
        "pass_name": "Pass 2 (Exclusions)",
        # Native broad query; exclusions handled post-fetch
        "query": 'title_and_abstract.search:("oily water separator" OR "bilge separator")',
        "exclusions": ["tanker", "cargo ship", "offshore platform"]
    },
    {
        "pass_name": "Pass 3 (Method)",
        "query": 'title_and_abstract.search:("gravity separator" OR "gravity separation" OR coalescing) AND (bilge OR "oily water") AND (boat OR vessel)',
        "exclusions": []
    }
]


def reconstruct_abstract(inverted_index):
    """Rebuilds full text abstract from OpenAlex position dictionary."""
    if not inverted_index:
        return ""
    word_index = {}
    try:
        for word, positions in inverted_index.items():
            for pos in positions:
                word_index[pos] = word
        return " ".join([word_index[i] for i in sorted(word_index.keys())])
    except Exception:
        return ""


def get_primary_country(authorships):
    if not authorships or not isinstance(authorships, list):
        return "n/a"
    try:
        first_author = authorships[0]
        inst = first_author.get("institutions", [])
        return inst[0].get("country_code", "n/a") if inst else "n/a"
    except Exception:
        return "n/a"


def fetch_page(params):
    try:
        response = requests.get(BASE_URL, params=params, timeout=45)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            print("   ⚠️ Server Busy (503). Waiting 15s...")
            time.sleep(15)
            return None
        print(f"   ⚠️ API Status {response.status_code}")
        return None
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return None


def sync_to_neon(df_16):
    neon_url = os.getenv("NEON_CONNECTION_STRING")
    if not neon_url:
        return
    try:
        import psycopg2
        from psycopg2.extras import execute_values
        conn = psycopg2.connect(neon_url)
        cur = conn.cursor()
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
        print("✅ Neon PostgreSQL database successfully synced.")
    except Exception as e:
        print(f"⚠️ Neon DB sync skipped/error: {e}")


def load_existing_dataset(csv_path=CSV_PATH):
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame(columns=COLUMNS_16)


def run_multi_pass_search(max_pages_per_pass=3, csv_path=CSV_PATH):
    """
    Executes Fina's 3-pass search against OpenAlex.
    Filters exclusions in Python post-fetch.
    Appends new unique records into the 16-column dataset.
    """
    existing_df = load_existing_dataset(csv_path)

    # Set up deduplication tracking by Link (DOI/URL) and Item (Title)
    existing_links = set(existing_df["Link"].dropna().str.strip().str.lower())
    existing_items = set(existing_df["Item"].dropna().str.strip().str.lower())
    
    current_max_id = int(existing_df["ID"].max()) if not existing_df.empty and "ID" in existing_df.columns else 0

    new_rows = []
    print(f"🚀 Starting OpenAlex Multi-Pass Harvesting: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📚 Existing database records: {len(existing_df)}")

    for pass_info in PASS_DEFINITIONS:
        pass_name = pass_info["pass_name"]
        filter_query = pass_info["query"]
        exclusions = [ex.lower() for ex in pass_info["exclusions"]]

        print(f"\n🔍 Executing {pass_name}...")
        cursor = '*'
        page = 0

        while cursor and page < max_pages_per_pass:
            page += 1
            params = {
                'filter': f'{filter_query},publication_year:2000-2026',
                'mailto': OPEN_ALEX_EMAIL,
                'per_page': 50,
                'cursor': cursor
            }

            data = fetch_page(params)
            if not data:
                break

            results = data.get('results', [])
            if not results:
                break

            for work in results:
                title = work.get('display_name') or "n/a"
                doi = work.get('doi')
                link = doi if doi else work.get('id') or "n/a"
                abstract = reconstruct_abstract(work.get('abstract_inverted_index'))

                # Check Python-level exclusions (for Pass 2: tanker, cargo ship, offshore platform)
                combined_text = f"{title} {abstract}".lower()
                if any(ex in combined_text for ex in exclusions):
                    continue

                # Deduplication check against existing dataset and newly harvested rows
                clean_link = link.strip().lower()
                clean_title = title.strip().lower()
                if clean_link in existing_links or clean_title in existing_items:
                    continue

                primary_loc = work.get('primary_location') or {}
                source_info = primary_loc.get('source') or {}
                journal = source_info.get('display_name', 'OpenAlex') if source_info else 'OpenAlex'

                pub_date = work.get('publication_date')
                year = str(pub_date)[:4] if pub_date else "n/a"
                country = get_primary_country(work.get('authorships'))

                current_max_id += 1
                row = {
                    "ID": current_max_id,
                    "Category": "Competitors",
                    "Item": title,
                    "Company or publisher": journal if journal else "n/a",
                    "Figure": "n/a",
                    "Unit": "n/a",
                    "Technology": "Separator/Filter",
                    "Target vessels": "Boats/Yachts/<400GT",
                    "Price": "n/a",
                    "Country": country,
                    "Year": year,
                    "Source type": "Academic / OpenAlex",
                    "Link": link,
                    "Found by": "Script",
                    "What it means for EcoBilge": f"Scraped via OpenAlex {pass_name}",
                    "Gap?": "No"
                }

                new_rows.append(row)
                existing_links.add(clean_link)
                existing_items.add(clean_title)

            print(f"   Batch {page}: New records added in pass: {len(new_rows)}")
            cursor = data.get('meta', {}).get('next_cursor')
            time.sleep(0.7)

    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=COLUMNS_16)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        combined_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n💾 Appended {len(new_rows)} new records to {csv_path}. Total rows: {len(combined_df)}")
        sync_to_neon(combined_df)
    else:
        print("\nℹ️ Multi-pass search finished. No new records to append.")

    return new_rows


if __name__ == "__main__":
    pages = 1
    if len(sys.argv) > 1:
        pages = int(sys.argv[1])
    run_multi_pass_search(max_pages_per_pass=pages)
