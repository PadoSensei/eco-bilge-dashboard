import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION ---
EMAIL = "padraigo.donoghue@gmail.com" 
BASE_URL = "https://api.openalex.org/works"

# We use "Anchor Pairs" to ensure relevance and avoid 503 timeouts
STRICT_FILTERS = [
    'title_and_abstract.search:"oily bilge water"',
    'title_and_abstract.search:"bilge water" AND title_and_abstract.search:recreational',
    'title_and_abstract.search:"bilge discharge" AND title_and_abstract.search:yacht',
    'title_and_abstract.search:"bilge water" AND title_and_abstract.search:detergent',
    'title_and_abstract.search:"bilge water" AND title_and_abstract.search:surfactant',
    'title_and_abstract.search:marina AND title_and_abstract.search:hydrocarbon',
    'title_and_abstract.search:"vessels under 400 GT"',
    'title_and_abstract.search:"small vessels" AND title_and_abstract.search:bilge'
]

def reconstruct_abstract(inverted_index):
    if not inverted_index: return "No abstract available"
    word_index = {}
    try:
        for word, positions in inverted_index.items():
            for pos in positions: word_index[pos] = word
        return " ".join([word_index[i] for i in sorted(word_index.keys())])
    except: return "Error reconstructing abstract"

def get_primary_country(authorships):
    if not authorships or not isinstance(authorships, list): return "Unknown"
    try:
        first_author = authorships[0]
        inst = first_author.get('institutions', [])
        return inst[0].get('country_code', 'Unknown') if inst else "Unknown"
    except: return "Unknown"

def fetch_page(params):
    try:
        response = requests.get(BASE_URL, params=params, timeout=45) # Increased timeout
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

def run_search_pipeline():
    all_results = {}
    print(f"🚀 Starting STRICT Eco Bilge Search: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Strategy: Filter-based literal matching (No fuzzy noise)")
    
    for i, filter_query in enumerate(STRICT_FILTERS):
        print(f"\n🔍 Query {i+1}/{len(STRICT_FILTERS)}: {filter_query}...")
        cursor = '*'
        batch_count = 0
        
        while cursor:
            # All logic is now inside the 'filter' parameter
            params = {
                'filter': f'{filter_query},publication_year:2000-2026,has_abstract:true',
                'mailto': EMAIL,
                'per_page': 200,
                'cursor': cursor
            }
            
            data = fetch_page(params)
            if not data: break
            
            results = data.get('results', [])
            if not results: break
            
            for work in results:
                doi = work.get('doi')
                key = doi if doi else work.get('id')
                
                if key not in all_results:
                    # Robust nested extraction
                    primary_loc = work.get('primary_location') or {}
                    source_info = primary_loc.get('source') or {}
                    
                    all_results[key] = {
                        "name": work.get('display_name'),
                        "url": doi if doi else work.get('id'),
                        "date": work.get('publication_date'),
                        "description": reconstruct_abstract(work.get('abstract_inverted_index')),
                        "country": get_primary_country(work.get('authorships')),
                        "doi": doi,
                        "journal": source_info.get('display_name', 'Unknown'),
                        "origin_query": filter_query
                    }
            
            batch_count += 1
            print(f"   ✅ Batch {batch_count} collected. (Unique total: {len(all_results)})")
            
            cursor = data.get('meta', {}).get('next_cursor')
            time.sleep(0.7) # Respect the Polite Pool

    if all_results:
        df = pd.DataFrame(all_results.values())
        # Final clean-up: remove any duplicates that might have slipped through
        df = df.drop_duplicates(subset=['doi']) if 'doi' in df.columns else df
        
        filename = f"eco_bilge_STRICT_{datetime.now().strftime('%Y_%m_%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n🏁 PIPELINE COMPLETE")
        print(f"📊 Final High-Signal Records: {len(df)}")
        print(f"💾 File Saved: {filename}")
    else:
        print("\n❌ No results found. Ensure keywords are correct.")

if __name__ == "__main__":
    run_search_pipeline()