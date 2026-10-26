"""Вставка раздела 3 (3.1–3.3) в отчёт УП ПМ.02."""
import re, sys, zipfile, shutil, xml.dom.minidom
from xml.sax.saxutils import escape
from docxkit import Doc
import section3

SRC = sys.argv[1]
DST = sys.argv[2]

z = zipfile.ZipFile(SRC)
doc = z.read("word/document.xml").decode("utf8")
rels = z.read("word/_rels/document.xml.rels").decode("utf8")
settings = z.read("word/settings.xml").decode("utf8")
assert "РАЗДЕЛ 3." not in doc, "раздел 3 уже есть в документе"

bm = max(map(int, re.findall(r'w:bookmarkStart w:id="(\d+)"', doc))) + 1
toc_no = max(map(int, re.findall(r'_Toc(\d+)', doc))) + 1
docpr = max(map(int, re.findall(r'<wp:docPr id="(\d+)"', doc))) + 1
rid = max(map(int, re.findall(r'Id="rId(\d+)"', rels))) + 1

d = Doc(bm, toc_no, docpr, rid)
section3.build(d)

# 1. тело раздела – перед завершающим sectPr
i = doc.rindex("<w:sectPr")
doc = doc[:i] + d.xml() + doc[i:]

# 2. оглавление: новые пункты после последнего, конец поля TOC переносится на последний пункт
END = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
assert doc.count(END) >= 1
j = doc.index(END)                       # первый end – конец поля TOC
toc_end_para = doc.rfind("<w:p ", 0, j)
k = doc.index("</w:p>", j) + 6
para = doc[toc_end_para:k].replace(END, "")
assert 'w:val="TOC' in para, para[:200]
est = [72, 72, 73, 74, 77, 81, 85, 89, 89, 92, 95, 98, 98, 101, 104]
entries = []
for n, (level, text, name) in enumerate(d.toc):
    entries.append(f'<w:p><w:pPr><w:pStyle w:val="TOC{level}"/></w:pPr><w:hyperlink w:anchor="{name}" w:history="1">'
                   f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r><w:r><w:tab/><w:t>{est[n] if n < len(est) else ""}</w:t></w:r></w:hyperlink>'
                   + (END if n == len(d.toc) - 1 else "") + '</w:p>')
doc = doc[:toc_end_para] + para + "".join(entries) + doc[k:]

# 3. связи и изображения
new_rels = "".join(f'<Relationship Id="{r}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{f}"/>'
                   for r, f, _ in d.media)
rels = rels.replace("</Relationships>", new_rels + "</Relationships>")

# 4. обновление полей (оглавления) при открытии
if "<w:updateFields" not in settings:
    settings = settings.replace("<w:footnotePr>", '<w:updateFields w:val="true"/><w:footnotePr>', 1)
    assert "<w:updateFields" in settings

xml.dom.minidom.parseString(doc.encode("utf8"))
xml.dom.minidom.parseString(rels.encode("utf8"))
xml.dom.minidom.parseString(settings.encode("utf8"))

out = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for it in z.infolist():
    data = z.read(it.filename)
    if it.filename == "word/document.xml": data = doc.encode("utf8")
    elif it.filename == "word/_rels/document.xml.rels": data = rels.encode("utf8")
    elif it.filename == "word/settings.xml": data = settings.encode("utf8")
    out.writestr(it, data)
for _, f, png in d.media:
    out.write(png, f"word/media/{f}")
out.close()
print("headings:", len(d.toc), "figures:", len(d.media), "bookmarks from", bm, "toc from", toc_no)
