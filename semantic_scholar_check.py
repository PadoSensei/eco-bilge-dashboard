import requests
import json

# The DOI that failed previously
DOI = "10.1016/j.rser.2015.11.029"

def test_semantic_scholar_graph_api(doi):
    print(f"📡 Querying Semantic Scholar GRAPH API (v1) for DOI: {doi}...")
    
    # Modern Graph API Syntax:
    # URL: /graph/v1/paper/DOI:<DOI>
    # Fields: We MUST ask for 'abstract' explicitly
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    params = {'fields': 'title,abstract,authors,year'}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("abstract")
            if abstract:
                print("✅ SUCCESS! Abstract recovered via Graph API.")
                print(f"\n--- ABSTRACT SNIPPET ---\n{abstract[:300]}...\n")
                return True
            else:
                print("❌ Paper found, but Abstract field is NULL in the Graph API response.")
        elif response.status_code == 404:
            print("⚠️ 404: Paper not found in Semantic Scholar's index.")
        else:
            print(f"🛑 API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"🔥 Connection Error: {e}")
    return False

test_semantic_scholar_graph_api(DOI)