"""Построение фрагментов WordprocessingML в стилях отчёта (a0, a1, a4, a5, a6, a8, Heading1–3)."""
from xml.sax.saxutils import escape
from PIL import Image

PAGE_W = 5852160          # ширина рисунка, EMU (16,26 см)
MAX_H = 8100000           # предельная высота рисунка, EMU (22,5 см)


def run(t, b=False, color=None, sz=None, i=False):
    rpr = ""
    if b: rpr += "<w:b/><w:bCs/>"
    if i: rpr += "<w:i/><w:iCs/>"
    if color: rpr += f'<w:color w:val="{color}"/>'
    if sz: rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>'


class Doc:
    def __init__(self, bm_id, toc_no, docpr_id, rid_no):
        self.parts, self.toc = [], []
        self.bm_id, self.toc_no, self.docpr, self.rid = bm_id, toc_no, docpr_id, rid_no
        self.media = []          # (rid, имя файла в архиве, путь png)
        self.after_table = False

    def _space(self):
        if self.after_table:
            self.after_table = False
            return '<w:spacing w:before="240"/>'
        return ""

    def h(self, level, text):
        name = f"_Toc{self.toc_no}"
        self.toc.append((level, text, name))
        self.toc_no += 1
        style = f"Heading{level}"
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:bookmarkStart w:id="{self.bm_id}" w:name="{name}"/>'
                          f'{run(text)}<w:bookmarkEnd w:id="{self.bm_id}"/></w:p>')
        self.bm_id += 1
        self.after_table = False

    def p(self, text):
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="a0"/>{self._space()}</w:pPr>{run(text)}</w:p>')

    def li(self, text):
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="a1"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="5"/></w:numPr>{self._space()}</w:pPr>{run(text)}</w:p>')

    def fig(self, png, caption):
        w, h = Image.open(png).size
        cx, cy = PAGE_W, round(PAGE_W * h / w)
        if cy > MAX_H:
            cx, cy = round(cx * MAX_H / cy), MAX_H
        rid = f"rId{self.rid}"; self.rid += 1
        did = self.docpr; self.docpr += 1
        fname = f"image_s3_{did}.png"
        self.media.append((rid, fname, png))
        self.parts.append(
            f'<w:p><w:pPr><w:pStyle w:val="a0"/><w:keepNext/><w:spacing w:before="120"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="{did}" name="Picture {did}"/>'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="0" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="a0"/><w:spacing w:before="120" w:after="240"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr>{run(caption)}</w:p>')
        self.after_table = False

    def table(self, caption, widths, header, rows, sz=None):
        """Ячейка: строка или dict(t, fill, color, b, jc, span, vm, sz)."""
        self.parts.append(f'<w:p><w:pPr><w:pStyle w:val="a4"/></w:pPr>{run(caption)}</w:p>')
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        o = [f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
             f'<w:tblCellMar><w:top w:w="28" w:type="dxa"/><w:left w:w="85" w:type="dxa"/><w:bottom w:w="28" w:type="dxa"/><w:right w:w="85" w:type="dxa"/></w:tblCellMar>'
             f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']

        def cell(c, w, head):
            if isinstance(c, str):
                c = {"t": c}
            span = c.get("span", 1)
            width = sum(widths[w:w + span])
            tcpr = f'<w:tcW w:w="{width}" w:type="dxa"/>'
            if span > 1: tcpr += f'<w:gridSpan w:val="{span}"/>'
            if c.get("vm") == "restart": tcpr += '<w:vMerge w:val="restart"/>'
            elif c.get("vm") == "cont": tcpr += '<w:vMerge/>'
            fill = c.get("fill") or ("E7E6E6" if head else None)
            if fill: tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
            tcpr += '<w:vAlign w:val="center"/>'
            style = "a6" if head else "a5"
            jc = c.get("jc")
            ppr = f'<w:pStyle w:val="{style}"/>' + (f'<w:jc w:val="{jc}"/>' if jc else "")
            paras = []
            for line in (c.get("t", "") or "").split("\n"):
                paras.append(f'<w:p><w:pPr>{ppr}</w:pPr>{run(line, b=c.get("b", False), color=c.get("color"), sz=c.get("sz", sz)) if line else ""}</w:p>')
            return f'<w:tc><w:tcPr>{tcpr}</w:tcPr>{"".join(paras)}</w:tc>', span

        def row(cells, head):
            r = ['<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if head else '') + '</w:trPr>']
            col = 0
            for c in cells:
                x, span = cell(c, col, head)
                r.append(x)
                col += span
            r.append('</w:tr>')
            return "".join(r)

        for hr in (header if isinstance(header[0], list) else [header]):
            o.append(row(hr, True))
        for r in rows:
            o.append(row(r, False))
        o.append('</w:tbl>')
        self.parts.append("".join(o))
        self.parts.append('<w:p><w:pPr><w:pStyle w:val="a8"/></w:pPr></w:p>')
        self.after_table = True

    def xml(self):
        return "".join(self.parts)
