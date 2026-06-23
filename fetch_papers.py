import urllib.request
import json
import urllib.parse

query = urllib.parse.quote("MobileNetV2 leaf classification")
url = f"https://api.openalex.org/works?search={query}&filter=publication_year:2020-2026&per-page=25"

req = urllib.request.Request(url, headers={'User-Agent': 'mailto:test@example.com'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        
    papers = []
    for work in data.get('results', []):
        title = work.get('title')
        year = work.get('publication_year')
        doi = work.get('doi')
        authors = ", ".join([a.get('author', {}).get('display_name', '') for a in work.get('authorships', [])[:3]])
        if len(work.get('authorships', [])) > 3:
            authors += " et al."
        papers.append({"title": title, "year": year, "authors": authors, "doi": doi})
        
    with open('papers.json', 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(papers)} papers to papers.json")
except Exception as e:
    print("Error:", e)
