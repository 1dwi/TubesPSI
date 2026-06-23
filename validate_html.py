from html.parser import HTMLParser
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr', 'path', 'circle', 'polyline', 'line']
    
    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append((tag, self.getpos()))
            
    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        if not self.stack:
            print(f"Error: Unexpected closing tag </{tag}> at line {self.getpos()[0]}")
            return
        top_tag, pos = self.stack.pop()
        if top_tag != tag:
            print(f"Error: Mismatched tag at line {self.getpos()[0]}: Expected </{top_tag}> (opened at {pos[0]}), got </{tag}>")

parser = MyHTMLParser()
with open("web/templates/index.html", "r", encoding="utf-8") as f:
    parser.feed(f.read())

if parser.stack:
    print("Unclosed tags:", parser.stack)
else:
    print("HTML is well-formed.")
