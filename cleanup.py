import os
from dotenv import load_dotenv
from supabase import create_client

# 1. SETUP
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_database_logic():
    print("🧹 Starting Database Logic Sweep...")

    # Fetch all articles that have been screened (Decision is not 'Pending')
    res = supabase.table("screening_phase_1").select("*").neq("decision", "Pending").execute()
    articles = res.data

    if not articles:
        print("⚠️ No screened articles found to fix. Ensure decision != 'Pending'.")
        return

    print(f"🧐 Found {len(articles)} articles. Recalculating math...")

    fixed_count = 0
    for art in articles:
        # Get raw scores, defaulting to 0 if they are NULL
        q1 = art.get('q1_score') or 0
        q2 = art.get('q2_score') or 0
        q3 = art.get('q3_score') or 0
        q4 = art.get('q4_score') or 0
        q5 = art.get('q5_score') or 0
        
        # 1. Calculate correct total
        correct_total = q1 + q2 + q3 + q4 + q5
        
        # 2. Re-apply Cléber's strict rules
        # RULE A: The Q3 Kill Switch (Quantitative data is mandatory)
        if q3 == 0:
            correct_decision = "EXCLUDE"
            # Ensure the reason reflects the kill switch
            new_reason = f"Q3 KILL SWITCH: No quantitative data. {art.get('exclusion_reason', '')}"
        
        # RULE B: Tiered Scoring
        elif correct_total >= 8:
            correct_decision = "PASS"
            new_reason = art.get('exclusion_reason')
        elif correct_total >= 5:
            correct_decision = "DOUBT"
            new_reason = art.get('exclusion_reason')
        else:
            correct_decision = "EXCLUDE"
            new_reason = art.get('exclusion_reason')

        # 3. Check if we actually need to update (to save database calls)
        if (art['total_score'] != correct_total) or (art['decision'] != correct_decision):
            supabase.table("screening_phase_1").update({
                "total_score": correct_total,
                "decision": correct_decision,
                "exclusion_reason": new_reason[:250] if new_reason else "N/A"
            }).eq("id", art['id']).execute()
            fixed_count += 1

    print(f"🏁 DONE! Logic sweep complete.")
    print(f"✅ Items corrected: {fixed_count}")
    print(f"📊 Items verified: {len(articles)}")

if __name__ == "__main__":
    fix_database_logic()