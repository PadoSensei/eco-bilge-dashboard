import requests
import json

# Replace with a DOI that returned 'EMPTY' in your last run
DOI = "10.1016/j.rser.2015.11.029" # Example: Microbial electrolysis cells paper

def inspect_record(doi):
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")

inspect_record(DOI)