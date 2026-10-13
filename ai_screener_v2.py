import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client

load_dotenv()

# Updated System Prompt based on the Official Protocol
SYSTEM_PROMPT = """
You are a senior research data extractor specializing in Marine Pollution (PICO framework).
Analyze the TITLE and ABSTRACT provided. Support English, Portuguese, French, and Spanish.

Return ONLY a JSON object with integer scores (0, 1, or 2) for these 5 fields:

q1 (Population): Receptor water body. (2=Coastal/estuary/marina/port, 1=Generic marine/aquatic, 0=Land/Lab/Deep sea/Atmosphere)
q2 (Intervention): Vessel source. (2=Boats/ships/bilge/vessels, 1=Port activity/shipping traffic, 0=Land-based source/industry)
q3 (Outcome): Quantitative data. (2=Numbers/mg/L/ppm/volumes/indices, 1=Generic pollution/impact mention, 0=Qualitative only/Governance/Policy/Management/Case Study)
q4 (Substance): Oil/Detergents. (2=Oil/TPH/PAH/Hydrocarbon/Bilge/Fuel/Diesel/Detergent/Surfactant, 1=Generic pollution, 0=Plastics/Metals/Noise/Sewage)
q5 (Method): Empirical Rigor. (2=Original peer-reviewed study/Field/Exp, 1=Systematic review/Meta-analysis/Thesis/Technical report, 0=Editorial/News/Blog/Narrative review)

CRITICAL: If the title/abstract focuses on 'governance', 'policy', 'stakeholders', 'perception', or 'legal frameworks', q3 MUST be 0.

JSON Format: {"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0, "exclusion_reason": "string"}
"""

class ResearchScreener:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    def normalize_keys(self, data):
        if isinstance(data, list): data = data[0]
        return {str(k).lower().replace("_", "").replace(" ", ""): v for k, v in data.items()}

    def calculate_decision(self, scores, abstract_text):
        """
        Implements Cleber's Official Scoring Tiers:
        0-4: EXCLUDE
        5-7: DOUBT (Human Review)
        8-10: PASS (Fase 2)
        Rule: Q3=0 is an Absolute Kill Switch.
        """
        q1, q2, q3, q4, q5 = scores
        total = sum(scores)
        
        # Rule 1: Absolute Q3 Rule (Outcome Missing)
        if q3 == 0:
            return "EXCLUDE", total, "RULE Q3=0: Absolute exclusion. Outcome (PICO) not met. Qualitative/Policy study."

        # Rule 2: Official Scoring Tiers
        if total >= 8:
            return "PASS", total, "Meets inclusion criteria for Phase 2."
        
        if total >= 5:
            return "DOUBT", total, "Borderline score; second human reviewer required."
        
        return "EXCLUDE", total, f"Low Score ({total}/10): Does not meet minimum relevance threshold."

    def process_article(self, article):
        title = article.get('title', 'Unknown')
        abstract = article.get('abstract_text', '') or ''
        print(f"🧐 Analyzing: {title[:70]}...")

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"{SYSTEM_PROMPT}\n\nTITLE: {title}\nABSTRACT: {abstract}",
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            
            raw_json = json.loads(response.text)
            norm = self.normalize_keys(raw_json)

            scores = [
                int(norm.get('q1', 0)),
                int(norm.get('q2', 0)),
                int(norm.get('q3', 0)),
                int(norm.get('q4', 0)),
                int(norm.get('q5', 0))
            ]
            ai_note = norm.get('exclusionreason', 'N/A')

            decision, total, logic_reason = self.calculate_decision(scores, abstract)
            final_reason = f"{logic_reason} | AI Note: {ai_note}"

            self.db.table("screening_phase_1").update({
                "q1_score": scores[0], "q2_score": scores[1], "q3_score": scores[2],
                "q4_score": scores[3], "q5_score": scores[4],
                "total_score": total,
                "decision": decision,
                "exclusion_reason": final_reason[:255]
            }).eq("id", article['id']).execute()

            print(f"   ✅ Result: {decision} ({total}/10 pts)")
            return True

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
        
    def run_re_evaluation(self, target_decision="Exclude", limit=50):
        """Forces a re-scan of already processed items using the new protocol."""
        print(f"🔄 Re-evaluating {limit} items currently marked as '{target_decision}'...")
        
        res = self.db.table("screening_phase_1")\
            .select("*")\
            .eq("decision", target_decision)\
            .limit(limit)\
            .execute()
        
        if not res.data:
            print(f"🏁 No items found with decision: {target_decision}")
            return

        for art in res.data:
            self.process_article(art)
            time.sleep(1.0)

    def run_sprint(self, limit=100):
        # We only re-process 'Pending' items to save costs
        res = self.db.table("screening_phase_1").select("*").eq("decision", "Pending").limit(limit).execute()
        
        if not res.data:
            print("🏁 No pending articles.")
            return

        for art in res.data:
            self.process_article(art)
            time.sleep(1.0) 

if __name__ == "__main__":
    screener = ResearchScreener()
    
    # 1. First, check if there are any actually new items
    screener.run_sprint(limit=10) 
    
    # 2. Re-evaluate items that were previously EXCLUDED 
    # to see if the new 10-point scale "rescues" them.
    # NOTE: Match the case "EXCLUDE" or "Exclude" exactly as it is in your DB
    screener.run_re_evaluation(target_decision="EXCLUDE", limit=50)