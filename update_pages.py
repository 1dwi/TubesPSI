import os
import re
from PyPDF2 import PdfReader

template_path = 'Template_Sitasi_Word.md'
folder_path = r'laporan word\Jurnal Referensi'

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Get all pdf files
pdfs = sorted([f for f in os.listdir(folder_path) if f.endswith('.pdf')])

for i, pdf_file in enumerate(pdfs):
    idx = i + 1
    pdf_path = os.path.join(folder_path, pdf_file)
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        real_pages = f"1-{num_pages}"
    except Exception as e:
        real_pages = "-"

    # Regex to find Jurnal ke-X block and replace Pages, Volume, Issue
    # We replace the static or dummy values back to the real page count and empty Volume/Issue.
    
    # Replace Pages
    content = re.sub(rf"(### Jurnal ke-{idx}\n.*?)- \*\*Pages:\*\* .*?\n", rf"\1- **Pages:** {real_pages}\n", content, flags=re.DOTALL)
    
    # Clean up Volume and Issue back to '-'
    content = re.sub(rf"(### Jurnal ke-{idx}\n.*?)- \*\*Volume:\*\* .*?\n", rf"\1- **Volume:** -\n", content, flags=re.DOTALL)
    content = re.sub(rf"(### Jurnal ke-{idx}\n.*?)- \*\*Issue:\*\* .*?\n", rf"\1- **Issue:** -\n", content, flags=re.DOTALL)

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Template updated with REAL page numbers!")
