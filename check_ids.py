import re

# get all getElementById from main.js
with open("web/static/js/main.js", "r", encoding="utf-8") as f:
    js_content = f.read()

ids_in_js = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js_content)

# get all id attributes from index.html
with open("web/templates/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

ids_in_html = re.findall(r"id=['\"]([^'\"]+)['\"]", html_content)
html_id_set = set(ids_in_html)

missing = []
for js_id in set(ids_in_js):
    if js_id not in html_id_set:
        missing.append(js_id)

print(f"Total IDs used in JS: {len(set(ids_in_js))}")
if missing:
    print("WARNING! These IDs are used in main.js but missing in index.html:")
    for m in missing:
        print(f"- {m}")
else:
    print("All IDs used in main.js are present in index.html.")
