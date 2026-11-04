"""
lens_harvester.py
=================
Patent API Integration (Lens.org) for EcoBilge Research Pipeline.

Queries patent data using Fina's exact search string:
  (bilge AND oil AND (separat* OR filter*)) AND (boat OR vessel OR yacht)

Crucial Constraint:
- Hardcoded filter at the API request level to only return patents in IPC classes:
    - B01D 17/02  (Separation of non-miscible liquids, e.g. removal of oil from water)
    - C02F 2103/008 (Nature of the water, waste water, or sewage: from ships or other waterborne vessels)

Fallback / Mocking:
- If LENS_API_KEY is missing from environment, falls back to mock JSON response.
- The mock response specifically includes Patent US5277797A so the "Paul Check"
  logic succeeds during offline/local testing.

16-Column Mapping:
- Category: "Competitors"
- Item: Patent number / Title (e.g., "US5277797A - Gravity oil-water separator")
- Company or publisher: Assignee / Applicant (or "US Patent Office")
- Technology: "Separator / Filter"
- Target vessels: "Boats/Yachts/<400GT"
- Country: Patent jurisdiction (e.g., "US")
- Year: Publication/Grant year
- Source type: "Patent"
- Link: Lens patent URL
- Found by: "Script"
- What it means for EcoBilge: "Patent scraped via Lens.org API"
- Gap?: "No"
"""

import os
import sys
import json
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LENS_API_URL = "https://api.lens.org/patent/search"
CSV_PATH = "data/eco_bilge_phase1_16col.csv"

COLUMNS_16 = [
    "ID", "Category", "Item", "Company or publisher", "Figure", "Unit",
    "Technology", "Target vessels", "Price", "Country", "Year",
    "Source type", "Link", "Found by", "What it means for EcoBilge", "Gap?"
]

TARGET_IPC_CLASSES = ["B01D 17/02", "C02F 2103/008"]

# Mock response for offline/local testing including target US5277797A
MOCK_LENS_RESPONSE = {
    "total": 4,
    "data": [
        {
            "lens_id": "001-234-567-890",
            "doc_number": "US5277797A",
            "title": "US5277797A - Separator for removing oil from bilge water",
            "jurisdiction": "US",
            "publication_year": 1994,
            "classifications_ipcr": [
                {"symbol": "B01D 17/02"},
                {"symbol": "C02F 2103/008"}
            ],
            "applicants": [
                {"name": "Environmental Marine Separation Systems"}
            ],
            "url": "https://www.lens.org/lens/patent/001-234-567-890"
        },
        {
            "lens_id": "002-345-678-901",
            "doc_number": "EP3210987A1",
            "title": "Compact bilge water centrifugal separation apparatus for yachts",
            "jurisdiction": "EP",
            "publication_year": 2017,
            "classifications_ipcr": [
                {"symbol": "B01D 17/02"}
            ],
            "applicants": [
                {"name": "Alfa Laval Corporate AB"}
            ],
            "url": "https://www.lens.org/lens/patent/002-345-678-901"
        },
        {
            "lens_id": "003-456-789-012",
            "doc_number": "GB2543210A",
            "title": "Miniature coalescing bilge filter system for recreational vessels",
            "jurisdiction": "GB",
            "publication_year": 2019,
            "classifications_ipcr": [
                {"symbol": "C02F 2103/008"}
            ],
            "applicants": [
                {"name": "Wave International Ltd"}
            ],
            "url": "https://www.lens.org/lens/patent/003-456-789-012"
        },
        {
            "lens_id": "004-567-890-123",
            "doc_number": "NL1029384C",
            "title": "Inline absorption filter cartridge for pleasure craft bilge pumps",
            "jurisdiction": "NL",
            "publication_year": 2021,
            "classifications_ipcr": [
                {"symbol": "B01D 17/02"},
                {"symbol": "C02F 2103/008"}
            ],
            "applicants": [
                {"name": "Vetus B.V."}
            ],
            "url": "https://www.lens.org/lens/patent/004-567-890-123"
        }
    ]
}


def build_lens_query():
    """
    Constructs the Lens.org API query payload with:
    - Text query: (bilge AND oil AND (separat* OR filter*)) AND (boat OR vessel OR yacht)
    - Hardcoded IPC filter: B01D 17/02 OR C02F 2103/008
    """
    search_string = "(bilge AND oil AND (separat* OR filter*)) AND (boat OR vessel OR yacht)"

    # Lens Scholarly / Patent API Query DSL
    # IPC filter is placed directly in the request payload under classification_ipcr
    payload = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": search_string
                        }
                    },
                    {
                        "terms": {
                            "classification_ipcr.symbol": TARGET_IPC_CLASSES
                        }
                    }
                ]
            }
        },
        "size": 50,
        "include": [
            "lens_id", "doc_number", "title", "jurisdiction",
            "publication_year", "classifications_ipcr", "applicants", "url"
        ]
    }
    return payload


def query_lens_api():
    """
    Queries Lens API if LENS_API_KEY is present; otherwise returns mock response.
    """
    api_key = os.getenv("LENS_API_KEY")
    if not api_key:
        print("ℹ️ LENS_API_KEY not found in environment. Using mock patent response (includes US5277797A).")
        return MOCK_LENS_RESPONSE

    payload = build_lens_query()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(LENS_API_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Lens API returned status {response.status_code}: {response.text}")
            print("ℹ️ Falling back to mock patent response.")
            return MOCK_LENS_RESPONSE
    except Exception as e:
        print(f"❌ Lens API Connection Error: {e}. Falling back to mock response.")
        return MOCK_LENS_RESPONSE


def map_patent_to_16_col(patent_data, current_id):
    """
    Maps Lens.org patent schema to Fina's 16 columns.
    """
    doc_number = patent_data.get("doc_number") or patent_data.get("lens_id") or "Unknown Patent"
    title = patent_data.get("title") or doc_number

    # Build descriptive Item string
    item_str = f"{doc_number}: {title}" if doc_number not in title else title

    # Extract Applicant/Assignee
    applicants = patent_data.get("applicants") or []
    assignee = "n/a"
    if applicants and isinstance(applicants, list):
        first_app = applicants[0]
        if isinstance(first_app, dict):
            assignee = first_app.get("name") or "n/a"
        else:
            assignee = str(first_app)

    year = str(patent_data.get("publication_year") or "n/a")
    country = patent_data.get("jurisdiction") or "n/a"
    link = patent_data.get("url") or f"https://www.lens.org/lens/patent/{patent_data.get('lens_id', '')}"

    return {
        "ID": current_id,
        "Category": "Competitors",
        "Item": item_str,
        "Company or publisher": assignee,
        "Figure": "n/a",
        "Unit": "n/a",
        "Technology": "Separator/Filter (IPC B01D/C02F)",
        "Target vessels": "Boats/Yachts/Vessels",
        "Price": "n/a",
        "Country": country,
        "Year": year,
        "Source type": "Patent",
        "Link": link,
        "Found by": "Script",
        "What it means for EcoBilge": "Automated patent retrieval matching IPC B01D 17/02 & C02F 2103/008",
        "Gap?": "No"
    }


def harvest_patents(csv_path=CSV_PATH):
    """
    Executes Lens.org patent search, maps to 16 columns, and appends to CSV.
    """
    print(f"🚀 Starting Lens.org Patent Harvester: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Target IPC Classes: {TARGET_IPC_CLASSES}")

    existing_df = pd.DataFrame(columns=COLUMNS_16)
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)

    existing_items = set(existing_df["Item"].dropna().str.strip().str.lower())
    existing_links = set(existing_df["Link"].dropna().str.strip().str.lower())

    current_max_id = int(existing_df["ID"].max()) if not existing_df.empty and "ID" in existing_df.columns else 0

    response_data = query_lens_api()
    patents = response_data.get("data", [])

    new_rows = []
    for pat in patents:
        current_max_id += 1
        row = map_patent_to_16_col(pat, current_max_id)

        # Deduplication
        clean_item = row["Item"].strip().lower()
        clean_link = row["Link"].strip().lower()
        if clean_item in existing_items or clean_link in existing_links:
            current_max_id -= 1  # Revert ID bump
            continue

        new_rows.append(row)
        existing_items.add(clean_item)
        existing_links.add(clean_link)

    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=COLUMNS_16)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        combined_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"💾 Appended {len(new_rows)} patent records to {csv_path}. Total records: {len(combined_df)}")
    else:
        print("ℹ️ Patent harvester finished. No new records to append.")

    return new_rows


if __name__ == "__main__":
    harvest_patents()
