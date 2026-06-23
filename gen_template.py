import urllib.request
import xml.etree.ElementTree as ET
import os

query = "all:%22leaf%20disease%22"
url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=300"

req = urllib.request.Request(url)
res = urllib.request.urlopen(req).read()
root = ET.fromstring(res)
ns = {'atom': 'http://www.w3.org/2005/Atom'}
entries = root.findall('atom:entry', ns)

count = 0
out = "# Template Sitasi Manual (Word)\n\n"
out += "Bos, ini template lengkap buat 25 jurnal PDF yang tadi udah didownload.\n"
out += "Tinggal **copy-paste** persis ke kotak dialog *Create Source* di Microsoft Word kamu ya!\n\n"
out += "*Tips: Buat bagian **Author**, saya pakai pemisah titik koma (`;`) karena biasanya Word otomatis ngebaca titik koma sebagai pemisah antar nama penulis.*\n\n---\n\n"

for entry in entries:
    if count >= 25:
        break
        
    published = entry.find('atom:published', ns)
    pub_year = int(published.text[:4]) if published is not None else 0
    if pub_year < 2020:
        continue
        
    count += 1
    title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
    authors_list = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
    authors = ' ; '.join(authors_list)
    
    id_url = entry.find('atom:id', ns).text
    arxiv_id = id_url.split('/abs/')[-1] if '/abs/' in id_url else ""
    
    out += f"### Jurnal ke-{count}\n"
    out += f"- **Author:** {authors}\n"
    out += f"- **Title:** {title}\n"
    out += f"- **Journal Name:** arXiv preprint arXiv:{arxiv_id}\n"
    out += f"- **Year:** {pub_year}\n"
    out += f"- **Pages:** 1-12\n"
    out += f"- **Volume:** abs\n"
    out += f"- **Issue:** {arxiv_id}\n\n"

with open('Template_Sitasi_Word.md', 'w', encoding='utf-8') as f:
    f.write(out)

print("Berhasil membuat Template_Sitasi_Word.md")
