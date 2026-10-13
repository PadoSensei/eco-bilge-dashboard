import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def run_audit():
    print("🔍 --- ECO-BILGE DATA AUDIT --- 🔍\n")

    # 1. Source Breakdown (Explaining Deduplication)
    res_sources = supabase.table("screening_phase_1").select("source_database").execute()
    sources = [r['source_database'] for r in res_sources.data]
    
    print("📊 DATASET COMPOSITION:")
    for src in set(sources):
        print(f"   - {src}: {sources.count(src)} unique papers")
    print("\n*Note: If Scopus/WoS counts are low, it's because they were already captured by OpenAlex deduplication.*")

    # 2. The "Q3 Victims" List
    print("\n🚫 PAPERS EXCLUDED BY Q3 KILL SWITCH (Potential False Negatives):")
    res_excluded = supabase.table("screening_phase_1")\
        .select("title", "exclusion_reason")\
        .ilike("exclusion_reason", "%Q3 KILL SWITCH%")\
        .execute()

    if not res_excluded.data:
        print("   No papers found matching this exclusion criteria.")
    else:
        for i, item in enumerate(res_excluded.data, 1):
            print(f"   {i}. {item['title'][:90]}...")
    
    print(f"\nTotal 'Q3' Exclusions: {len(res_excluded.data)}")

if __name__ == "__main__":
    run_audit()