import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client

# 1. Configuration & Constants
load_dotenv()

SYSTEM_PROMPT = """
You are a research data extractor. Analyze the Marine Research TITLE and ABSTRACT.
Return ONLY a JSON object. Provide integer scores (0, 1, or 2) for these 5 fields:

q1: Water (2=coastal/marina/river/estuary, 1=generic marine, 0=land/lab/deep sea)
q2: Vessel (2=boat/yacht <400gt/bilge, 1=shipping traffic/port, 0=fixed land source)
q3: Quant (2=explicit numbers/mg/L/ppm/volumes, 1=generic impact, 0=qualitative/policy/case study)
q4: Oil (2=oil/TPH/PAH/detergent/surfactant, 1=generic pollution, 0=noise/metals/plastic)
q5: Method (2=original empirical study, 1=systematic review/thesis/grey lit, 0=editorial/news)

exclusion_reason: Provide a brief 1-sentence reason.
JSON: {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "exclusion_reason": "string"}
"""

class ResearchScreener:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    def normalize_keys(self, data):
        """Cleans AI keys: 'Q1_Score' or 'q 1' becomes 'q1'."""
        if isinstance(data, list):
            data = data[0]
        return {str(k).lower().replace("_", "").replace(" ", ""): v for k, v in data.items()}

    def calculate_decision(self, scores, abstract_text):
        """Single source of truth for research logic."""
        q1, q2, q3, q4, q5 = scores
        total = sum(scores)
        
        # Rule 1: Safety Catch for missing abstracts
        # If abstract is tiny/missing, but Title is perfect (Vessel=2, Oil=2), move to DOUBT
        if (not abstract_text or len(abstract_text) < 100) and (q2 == 2 and q4 == 2):
            return "DOUBT", total, "MISSING ABSTRACT: High-relevance title; manual check needed."

        # Rule 2: The Q3 Kill Switch (Journal Requirement)
        if q3 == 0:
            return "EXCLUDE", total, "Q3 KILL SWITCH: No quantitative data/Qualitative study."
        
        # Rule 3: Scoring Tiers
        if total >= 8:
            return "PASS", total, "Meets inclusion criteria."
        if total >= 5:
            return "DOUBT", total, "Potential relevance; needs human review."
        
        return "EXCLUDE", total, "Low score: Cumulative criteria not met."

    def process_article(self, article):
        title = article.get('title', 'Unknown')
        abstract = article.get('abstract_text', '') or '' # Ensure string even if NULL
        print(f"🧐 Analyzing: {title[:60]}...")

        try:
            # Call AI
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"{SYSTEM_PROMPT}\n\nTITLE: {title}\nABSTRACT: {abstract}",
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            
            raw_json = json.loads(response.text)
            norm = self.normalize_keys(raw_json)

            # Extract scores safely
            scores = [
                int(norm.get('q1', 0)),
                int(norm.get('q2', 0)),
                int(norm.get('q3', 0)),
                int(norm.get('q4', 0)),
                int(norm.get('q5', 0))
            ]
            ai_reason = norm.get('exclusionreason', 'N/A')

            # FIX: We now pass 'abstract' as the second argument
            decision, total, logic_reason = self.calculate_decision(scores, abstract)
            
            # Final Reason: Combine logic results with the AI's specific note
            final_reason = f"{logic_reason} (AI Note: {ai_reason})"

            # Update DB
            self.db.table("screening_phase_1").update({
                "q1_score": scores[0], "q2_score": scores[1], "q3_score": scores[2],
                "q4_score": scores[3], "q5_score": scores[4],
                "total_score": total,
                "decision": decision,
                "exclusion_reason": final_reason[:250] # Database safety limit
            }).eq("id", article['id']).execute()

            print(f"   ✅ Result: {decision} ({total} pts)")
            return True

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

    def run_sprint(self, limit=100):
        print(f"🚀 Starting sprint on {limit} items...")
        res = self.db.table("screening_phase_1").select("*").eq("decision", "Pending").limit(limit).execute()
        
        if not res.data:
            print("🏁 No pending articles. Vault is clean.")
            return

        success_count = 0
        for art in res.data:
            if self.process_article(art):
                success_count += 1
            time.sleep(1.2) # API Rate Limit protection

        print(f"\n🏁 Sprint Finished. {success_count}/{len(res.data)} items processed successfully.")

if __name__ == "__main__":
    screener = ResearchScreener()
    screener.run_sprint(500) # You can change this to 500 for the full run