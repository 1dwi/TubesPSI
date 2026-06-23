import urllib.request
import xml.etree.ElementTree as ET
import os

# Create folder
target_folder = os.path.join('laporan word', 'Jurnal Referensi')
os.makedirs(target_folder, exist_ok=True)

# Query arXiv (Diperluas untuk memastikan dapat >= 25 jurnal tahun 2020+)
query = "all:%22leaf%20disease%22"
url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=300"

print("Fetching metadata from arXiv...")
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)
ns = {'atom': 'http://www.w3.org/2005/Atom'}

entries = root.findall('atom:entry', ns)
print(f"Found {len(entries)} papers.")

downloaded_count = 0

for i, entry in enumerate(entries):
    if downloaded_count >= 25:
        break
        
    # Check Year >= 2020
    published = entry.find('atom:published', ns)
    if published is None: continue
    pub_year = int(published.text[:4])
    if pub_year < 2020:
        continue
        
    title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
    # clean title for filename
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    if len(safe_title) > 50:
        safe_title = safe_title[:50]
        
    pdf_url = ""
    for link in entry.findall('atom:link', ns):
        if link.attrib.get('title') == 'pdf':
            pdf_url = link.attrib.get('href')
            break
            
    if not pdf_url:
        print(f"[{i+1}/30] No PDF link for: {safe_title}")
        continue
        
    # ensure https
    if pdf_url.startswith('http://'):
        pdf_url = pdf_url.replace('http://', 'https://')
    # add .pdf if needed
    if not pdf_url.endswith('.pdf'):
        pdf_url += '.pdf'
        
    filename = os.path.join(target_folder, f"{downloaded_count+1:02d}_{safe_title.replace(' ', '_')}.pdf")
    print(f"[{downloaded_count+1}/25] Downloading {filename} from {pdf_url} (Tahun: {pub_year}) ...")
    
    try:
        urllib.request.urlretrieve(pdf_url, filename)
        downloaded_count += 1
    except Exception as e:
        print(f"  -> Error downloading: {e}")

print("Done!")
