import urllib.request
import json
import urllib.parse

# Kombinasi keyword spesifik untuk ikan / aquaculture
query = urllib.parse.quote("Terminalia catappa fish")
url = f"https://api.openalex.org/works?search={query}&per-page=15&sort=relevance_score:desc"

req = urllib.request.Request(url)
res = urllib.request.urlopen(req).read()
data = json.loads(res)

with open('hasil_ketapang.txt', 'w', encoding='utf-8') as f:
    f.write('--- Hasil OpenAlex: Terminalia catappa fish ---\n')
    for w in data.get('results', []):
        title = w.get('title')
        year = w.get('publication_year')
        doi = w.get('doi')
        authors = " ; ".join([a.get('author', {}).get('display_name', '') for a in w.get('authorships', [])])
        if title:
            f.write(f"- Title: {title} ({year})\n")
            f.write(f"  Author: {authors}\n")
            f.write(f"  DOI: {doi}\n")
            f.write("---\n")
print("Hasil pencarian tersimpan di hasil_ketapang.txt")
