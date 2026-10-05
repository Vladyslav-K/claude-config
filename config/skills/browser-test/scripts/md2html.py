# Converts report.md / findings.md of a browser-test run into a self-contained HTML file.
# Usage: python3 md2html.py <src.md> <out.html> <title>
# Supports only the markup of the skill's templates: headings, paragraphs, "- " lists,
# tables, **bold**, _italic_, `code`, ![alt](path). Image paths are relative to the .md file.
import base64, html, io, re, sys, os
from PIL import Image

src, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
base = os.path.dirname(src)
lines = open(src, encoding='utf-8').read().split('\n')
cache = {}

missing = sorted({p for l in lines for p in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', l) if not os.path.isfile(os.path.join(base, p))})
if missing:
    sys.exit('missing images: ' + ', '.join(missing))

def img_tag(alt, path):
    full = os.path.join(base, path)
    if full not in cache:
        im = Image.open(full).convert('RGB')
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=82, optimize=True)
        cache[full] = (base64.b64encode(buf.getvalue()).decode(), im.size)
    data, (w, h) = cache[full]
    cls = 'narrow' if w < 800 else 'wide'
    return f'<figure class="{cls}"><img alt="{html.escape(alt)}" src="data:image/jpeg;base64,{data}"><figcaption>{html.escape(os.path.basename(path))}</figcaption></figure>'

def inline(text):
    # Code and images become placeholders first, so their content is not touched by the bold/italic rules.
    codes = []
    def keep(m):
        codes.append('<code>' + html.escape(m.group(1)) + '</code>')
        return f'\x00{len(codes)-1}\x00'
    text = re.sub(r'`([^`]+)`', keep, text)
    imgs = []
    def keep_img(m):
        imgs.append(img_tag(m.group(1), m.group(2)))
        return f'\x01{len(imgs)-1}\x01'
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', keep_img, text)
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<![\w/])_(.+?)_(?![\w/])', r'<em>\1</em>', text)
    text = re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], text)
    text = re.sub(r'\x01(\d+)\x01', lambda m: imgs[int(m.group(1))], text)
    return text

body, para, items, table = [], [], [], []
def flush():
    global para, items, table
    if para:
        body.append('<p>' + '<br>'.join(inline(l) for l in para) + '</p>'); para = []
    if items:
        body.append('<ul>' + ''.join(f'<li>{inline(i)}</li>' for i in items) + '</ul>'); items = []
    if table:
        rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in table if not re.match(r'^\|[\s\-|:]+\|$', r.strip())]
        h = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
        b = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
        body.append(f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'); table = []

for raw in lines:
    line = raw.rstrip()
    m = re.match(r'^(#{1,6})\s+(.*)$', line)
    if m:
        flush(); n = len(m.group(1)); body.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); continue
    if line.startswith('|'):
        if para or items: flush()
        table.append(line); continue
    if table: flush()
    if re.match(r'^\s*- ', line):
        if para: flush()
        items.append(re.sub(r'^\s*- ', '', line)); continue
    if not line.strip():
        flush(); continue
    if items and raw.startswith('  '):
        items[-1] += ' ' + line.strip(); continue
    if items: flush()
    para.append(line)
flush()

css = '''
@page { size: A4; margin: 14mm 12mm; }
body { font-family: "DejaVu Sans", "Noto Color Emoji", sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1f2937; }
h1 { font-size: 19pt; border-bottom: 2px solid #334155; padding-bottom: 4px; }
h2 { font-size: 15pt; margin-top: 22px; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; break-after: avoid; }
h3 { font-size: 12.5pt; margin-top: 18px; break-after: avoid; }
h4 { font-size: 11pt; margin-top: 14px; break-after: avoid; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9pt; background: #f1f5f9; padding: 0 3px; border-radius: 3px; word-break: break-word; }
figure { margin: 8px 0 12px; break-inside: avoid; }
figure img { display: block; border: 1px solid #cbd5e1; border-radius: 4px; }
figure.wide img { width: 100%; }
figure.narrow img { width: 45%; }
figcaption { font-size: 8pt; color: #64748b; margin-top: 2px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }
th, td { border: 1px solid #cbd5e1; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f1f5f9; }
ul { padding-left: 20px; } li { margin: 2px 0; }
'''
open(out, 'w', encoding='utf-8').write(f'<!doctype html><html lang="uk"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{css}</style></head><body>{"".join(body)}</body></html>')
print(out, len(cache), 'images')
