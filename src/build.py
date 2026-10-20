import base64, io, re, sys
from PIL import Image
src_html, img_dir, out = sys.argv[1:4]
s = open(src_html, encoding="utf-8").read()

# split artifact source into head part (title, links, style) and body part
s = s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
cut = s.index('</style>') + len('</style>')
head_part, body_part = s[:cut], s[cut:]

# embed photos as data URIs
def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()
for k in range(1, 15):
    body_part = body_part.replace(f"'img/k{k}.webp'", f"'data:image/webp;base64,{b64(f'{img_dir}/k{k}.webp')}'")
assert "img/k" not in body_part

# drop the artifact viewer's hot reload hook
hot = re.search(r"\n  window\.claude\?\.hot.*?start\(hot\?\.data \?\? \{\}\);\n", body_part, re.S)
assert hot
body_part = body_part[:hot.start()] + "\n  start({});\n" + body_part[hot.end():]

# home screen icon from the checkered kitty photo
im = Image.open(f"{img_dir}/k1.webp").convert("RGB").crop((25, 25, 535, 535)).resize((180, 180), Image.LANCZOS)
buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
touch = base64.b64encode(buf.getvalue()).decode()

favicon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 -14 100 100'%3E"
           "%3Cg fill='%23e5364f' stroke='%233b2a2f' stroke-width='5'%3E"
           "%3Cellipse cx='27' cy='36' rx='24' ry='21' transform='rotate(-14 27 36)'/%3E"
           "%3Cellipse cx='73' cy='36' rx='24' ry='21' transform='rotate(14 73 36)'/%3E"
           "%3Ccircle cx='50' cy='37' r='12'/%3E%3C/g%3E%3C/svg%3E")

doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#fff3f6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1d1418" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="CAT 타이머">
<link rel="icon" href="{favicon}">
<link rel="apple-touch-icon" href="data:image/png;base64,{touch}">
<style>
:root {{ color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
html, body {{ margin: 0; }}
body {{ -webkit-text-size-adjust: 100%; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
{head_part}
</head>
<body>
{body_part.strip()}
</body>
</html>
"""
open(out, "w", encoding="utf-8").write(doc)
print(out, len(doc.encode()) // 1024, "KB")
