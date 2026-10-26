"""Замена рисунков раздела 3 в отчёте на перерисованные (с пересчётом пропорций)."""
import re, sys, zipfile, xml.dom.minidom
from PIL import Image
from docxkit import PAGE_W, MAX_H
SRC, DST = sys.argv[1], sys.argv[2]
ORDER = ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "a11", "n1", "n2", "n3", "menu", "g1", "g2"]
z = zipfile.ZipFile(SRC)
doc = z.read("word/document.xml").decode("utf8")
rels = z.read("word/_rels/document.xml.rels").decode("utf8")
media = sorted(set(re.findall(r'media/(image_s3_(\d+)\.png)', rels)), key=lambda m: int(m[1]))
assert len(media) == len(ORDER), media
new = {}
for (fname, _), key in zip(media, ORDER):
    png = f"final/{key}.png"
    new[f"word/media/{fname}"] = open(png, "rb").read()
    rid = re.search(r'Id="(rId\d+)"[^>]*Target="media/%s"' % re.escape(fname), rels).group(1)
    w, h = Image.open(png).size
    cx, cy = PAGE_W, round(PAGE_W * h / w)
    if cy > MAX_H:
        cx, cy = round(cx * MAX_H / cy), MAX_H
    i = doc.index(f'r:embed="{rid}"')
    st = doc.rfind("<w:drawing>", 0, i); en = doc.index("</w:drawing>", i)
    seg = re.sub(r'<wp:extent cx="\d+" cy="\d+"/>', f'<wp:extent cx="{cx}" cy="{cy}"/>', doc[st:en])
    seg = re.sub(r'<a:ext cx="\d+" cy="\d+"/>', f'<a:ext cx="{cx}" cy="{cy}"/>', seg)
    doc = doc[:st] + seg + doc[en:]
xml.dom.minidom.parseString(doc.encode("utf8"))
out = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for it in z.infolist():
    data = new.get(it.filename) or (doc.encode("utf8") if it.filename == "word/document.xml" else z.read(it.filename))
    out.writestr(it, data)
out.close()
print("заменено рисунков:", len(new))
