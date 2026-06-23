import urllib.request
import json
import urllib.parse

# Mencari kombinasi klasifikasi citra / kematangan daun ketapang
queries = [
    "Terminalia catappa maturity",
    "Terminalia catappa classification",
    "Terminalia catappa leaf image",
    "Terminalia catappa leaf maturity"
]

results = []
for q in queries:
    try:
        query = urllib.parse.quote(q)
        url = f"https://api.openalex.org/works?search={query}&per-page=10&sort=relevance_score:desc"
        req = urllib.request.Request(url)
        res = urllib.request.urlopen(req).read()
        data = json.loads(res)
        
        for w in data.get('results', []):
            title = w.get('title')
            if title and title not in [r['title'] for r in results]:
                results.append({
                    'title': title,
                    'year': w.get('publication_year'),
                    'doi': w.get('doi'),
                    'authors': " ; ".join([a.get('author', {}).get('display_name', '') for a in w.get('authorships', [])])
                })
    except Exception as e:
        continue

with open('hasil_ketapang_spesifik.txt', 'w', encoding='utf-8') as f:
    f.write('--- Hasil OpenAlex: Terminalia catappa Classification/Maturity ---\n')
    for r in results[:15]:
        f.write(f"- Title: {r['title']} ({r['year']})\n")
        f.write(f"  Author: {r['authors']}\n")
        f.write(f"  DOI: {r['doi']}\n")
        f.write("---\n")
