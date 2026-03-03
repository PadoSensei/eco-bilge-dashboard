import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def run_sanity_check():
    print("🔍 --- STEP 1: MODEL AVAILABILITY ---")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            print(f"✅ Found: {m.name}")

    print("\n📊 --- STEP 2: PROJECT COST ESTIMATION ---")
    
    # Assumptions based on your Eco Bilge data:
    # 500 articles, avg 300 words each = approx 400 tokens per abstract
    # System prompt + formatting = approx 200 tokens per call
    # Total input per article = ~600 tokens
    # Total output per article = ~100 tokens (JSON result)
    
    num_articles = 500
    avg_input_tokens = 600
    avg_output_tokens = 100
    
    total_input = num_articles * avg_input_tokens
    total_output = num_articles * avg_output_tokens

    # Current Pricing (Pay-as-you-go tiers)
    # Note: Free tier is $0 up to 1,500 requests/day
    pricing = {
        "gemini-1.5-flash": {"in": 0.075 / 1_000_000, "out": 0.30 / 1_000_000},
        "gemini-1.5-pro":   {"in": 1.25 / 1_000_000, "out": 5.00 / 1_000_000},
        "gemini-1.0-pro":   {"in": 0.50 / 1_000_000, "out": 1.50 / 1_000_000}
    }

    print(f"Total projected Input tokens:  {total_input:,}")
    print(f"Total projected Output tokens: {total_output:,}")
    print("-" * 30)

    for model_id, rates in pricing.items():
        # Find the internal name (e.g., 'models/gemini-1.5-flash')
        internal_name = f"models/{model_id}"
        status = "INSTALLED" if internal_name in available_models else "NOT FOUND"
        
        cost = (total_input * rates['in']) + (total_output * rates['out'])
        
        print(f"Model: {model_id:<18} | Status: {status:<10} | Est. Cost: ${cost:.4f}")

    print("\n💡 NOTE: If using the FREE TIER, your actual cost is $0.00.")
    print("Free Tier Limits (1.5 Flash): 15 RPM (Requests Per Minute), 1 million TPM, 1,500 RPD.")

if __name__ == "__main__":
    run_sanity_check()