import os
import requests
import time
from dotenv import load_dotenv
from supabase import create_client

# 1. SETUP & CONFIGURATION
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPEN_ALEX_EMAIL = os.getenv("OPEN_ALEX_EMAIL") 

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def format_doi_for_api(doi_string):
    """Ensures DOI is in the format OpenAlex expects: https://doi.org/10.xxxx"""
    if not doi_string:
        return None
    doi_string = doi_string.strip()
    if doi_string.startswith("http"):
        return doi_string
    return f"https://doi.org/{doi_string}"

def run_dry_run_recovery():
    print("🧪 --- ABSTRACT RECOVERY: DRY RUN (READ-ONLY) --- 🧪")
    print("Goal: Check OpenAlex for missing abstracts before updating DB.\n")

    # 1. Fetch records where abstract is missing or contains the 'placeholder' text
    # Note: We check for null, empty strings, and the specific 'Abstract not provided' string
    res = supabase.table("screening_phase_1")\
        .select("id, doi, title, source_database")\
        .or_("abstract_text.eq.'Abstract not provided in source file.',abstract_text.is.null,abstract_text.eq.''")\
        .execute()
    
    targets = res.data
    total_missing = len(targets)

    if total_missing == 0:
        print("✅ No missing abstracts found in the database. Your vault is complete!")
        return

    print(f"📊 Found {total_missing} articles missing abstracts.")
    print(f"🛰️  Pinging OpenAlex API (Email: {OPEN_ALEX_EMAIL})...\n")

    recovered_count = 0
    failed_count = 0
    skipped_no_doi = 0

    for i, item in enumerate(targets, 1):
        raw_doi = item.get('doi')
        title = item.get('title', 'Unknown Title')[:55]
        source = item.get('source_database', 'Unknown Source')
        
        # Skip if DOI looks like our 'MANUAL-hash' placeholder or is missing
        if not raw_doi or "MANUAL" in raw_doi:
            print(f"   [{i}/{total_missing}] ⏭️  SKIP: No valid DOI | '{title}' ({source})")
            skipped_no_doi += 1
            continue

        doi_url = format_doi_for_api(raw_doi)
        
        try:
            # We use the /works endpoint with the DOI URL
            api_url = f"https://api.openalex.org/works/{doi_url}"
            params = {'mailto': OPEN_ALEX_EMAIL}
            
            response = requests.get(api_url, params=params, timeout=10)
            
            # FIXED: status_code
            if response.status_code == 200:
                work = response.json()
                # OpenAlex stores abstracts as an inverted index
                abstract_index = work.get("abstract_inverted_index")
                
                if abstract_index:
                    recovered_count += 1
                    print(f"   [{i}/{total_missing}] ✅ FOUND: '{title}...'")
                else:
                    failed_count += 1
                    print(f"   [{i}/{total_missing}] ❌ EMPTY: API exists but no abstract index for '{title}'")
            elif response.status_code == 404:
                failed_count += 1
                print(f"   [{i}/{total_missing}] ⚠️  404: Not in OpenAlex | '{title}'")
            else:
                failed_count += 1
                print(f"   [{i}/{total_missing}] 🛑 ERROR {response.status_code} | '{title}'")

        except Exception as e:
            failed_count += 1
            print(f"   [{i}/{total_missing}] 🔥 EXCEPTION: {e}")

        # Rate Limit: Polite Pool allows 10 requests/sec, but we'll stay safe at 5/sec
        time.sleep(0.2)

    # FINAL AUDIT REPORT
    success_rate = (recovered_count / total_missing) * 100 if total_missing > 0 else 0
    
    print("\n" + "="*50)
    print("🏁 DRY RUN RESULTS")
    print("="*50)
    print(f"Items Analyzed:         {total_missing}")
    print(f"Recoverable Abstracts:  {recovered_count}")
    print(f"Metadata not found:     {failed_count}")
    print(f"Skipped (No DOI):       {skipped_no_doi}")
    print("-" * 50)
    print(f"📈 RECOVERY POTENTIAL:  {success_rate:.1f}%")
    print("="*50)
    print("\n[INFO] No changes were made to the Supabase database.")

if __name__ == "__main__":
    run_dry_run_recovery()