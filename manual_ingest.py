import os
import rispy
import re
import time
from dotenv import load_dotenv
from supabase import create_client

# 1. SETUP
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def clean_string(text):
    """Normalize strings for accurate duplicate detection."""
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip().lower()

def ingest_research_file(filepath, source_label):
    print(f"\n--- 📥 Ingesting: {filepath} ({source_label}) ---")
    
    # Identify file type and load entries
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            # rispy is great for .ris; for .txt (WOS), it usually follows the same logic
            entries = rispy.load(f)
    except Exception as e:
        print(f"❌ Failed to parse {filepath}. Ensure it is a valid RIS or Tagged Text file. Error: {e}")
        return

    stats = {"new": 0, "duplicate": 0, "no_doi": 0, "invalid": 0}
    
    for entry in entries:
        # Scopus/WOS use different tags; we check all common possibilities
        title = entry.get('title') or entry.get('primary_title') or entry.get('T1')
        doi = entry.get('doi') or entry.get('DO')
        abstract = entry.get('abstract') or entry.get('AB') or entry.get('N1')
        
        if not title:
            stats["invalid"] += 1
            continue

        # --- SMART DEDUPLICATION ---
        exists = False
        if doi:
            # Check DOI (The gold standard)
            check = supabase.table("screening_phase_1").select("id").eq("doi", doi).execute()
            if check.data: exists = True
        
        if not exists:
            # Backup check: Normalize Title (Catching duplicates OpenAlex missed)
            norm_title = clean_string(title)
            # We use ILIKE for a case-insensitive database check
            check = supabase.table("screening_phase_1").select("id").ilike("title", norm_title).execute()
            if check.data: exists = True

        if exists:
            print(f"🔁 [SKIP] Duplicate: {title[:50]}...")
            stats["duplicate"] += 1
        else:
            # Create a consistent ID for papers without DOIs
            final_doi = doi if doi else f"MANUAL-{hash(clean_string(title))}"
            
            payload = {
                "title": title.strip(),
                "doi": final_doi,
                "abstract_text": abstract if abstract else "Abstract not provided in source file.",
                "source_database": source_label,
                "decision": "Pending"
            }
            
            try:
                supabase.table("screening_phase_1").insert(payload).execute()
                if doi:
                    print(f"✨ [NEW] Added: {title[:50]}...")
                    stats["new"] += 1
                else:
                    print(f"📝 [NEW/NO-DOI] Added: {title[:50]}...")
                    stats["no_doi"] += 1
            except Exception as e:
                print(f"⚠️ Database Error on {title[:30]}: {e}")

    # 4. FINAL LOGGING FOR PRISMA AUDIT
    print(f"\n🏁 FINAL SUMMARY for {source_label}:")
    print(f"   📊 Total Scanned:      {len(entries)}")
    print(f"   ✨ Unique (with DOI):  {stats['new']}")
    print(f"   📝 Unique (no DOI):    {stats['no_doi']}")
    print(f"   🔁 Duplicates Hidden:  {stats['duplicate']}")
    print(f"   ❌ Invalid (no title): {stats['invalid']}")

if __name__ == "__main__":
    # AUTOMATED WORKFLOW: Add your files here
    files_to_run = [
        {"path": "scopus.ris", "label": "Scopus (Manual)"},
        {"path": "world_of_science.ris", "label": "Web of Science (Manual)"}
    ]

    for file_conf in files_to_run:
        if os.path.exists(file_conf['path']):
            ingest_research_file(file_conf['path'], file_conf['label'])
            time.sleep(1) # Breath between files
        else:
            print(f"ℹ️ File not found, skipping: {file_conf['path']}")