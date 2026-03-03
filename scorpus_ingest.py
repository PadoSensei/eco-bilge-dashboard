import os
import requests
import time
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPEN_ALEX_EMAIL = os.getenv("OPEN_ALEX_EMAIL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. EXPANDED SEARCH BUCKETS (Based on your PICO criteria)
search_queries = [
    "bilge water discharge",
    "recreational vessel pollution",
    "small vessel oil statistics",
    "yacht marina water quality",
    "pleasure craft hydrocarbon",
    "boat bilge TPH",
    "vessels under 400 GT",
    "MARPOL Annex I small vessel",
    "bilge water surfactants",
    "detergent marine pollution",
    "coastal marina oil contamination",
    "estuary vessel discharge",
    "bilge generation rates"
]

def reconstruct_abstract(inverted_index):
    if not inverted_index: return None
    word_index = {}
    for word, positions in inverted_index.items():
        for pos in positions: word_index[pos] = word
    return " ".join([word_index[i] for i in sorted(word_index.keys())])

def fetch_openalex_big_pull():
    base_url = "https://api.openalex.org/works"
    
    total_new_papers = 0

    for query in search_queries:
        print(f"🔍 Searching for: {query}")
        
        # We increase per_page to 200 to get more results per category
        params = {
            'filter': f'title_and_abstract.search:{query}',
            'mailto': OPEN_ALEX_EMAIL,
            'per_page': 200 
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            results = response.json().get('results', [])

            for work in results:
                doi = work.get("doi")
                if not doi: continue 

                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

                payload = {
                    "title": work.get("display_name"),
                    "doi": doi.replace("https://doi.org/", ""),
                    "abstract_text": abstract,
                    "source_database": "OpenAlex"
                }
                
                # USE TRY-EXCEPT TO SILENTLY SKIP DUPLICATES
                try:
                    supabase.table("screening_phase_1").upsert(payload).execute()
                    total_new_papers += 1
                except Exception:
                    # This is a duplicate DOI, just ignore it
                    pass
            
            print(f"✅ Finished processing batch for: {query}")
            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️ API Error on {query}: {e}")

    print(f"🏁 DONE! Added approximately {total_new_papers} unique papers to the vault.")

if __name__ == "__main__":
    fetch_openalex_big_pull()