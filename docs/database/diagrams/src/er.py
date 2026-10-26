"""Логические ER-диаграммы (рис. 13, 14): связи идут от строки PK к строке FK."""
import sys
from xml.sax.saxutils import escape

ROW = 43          # высота строки атрибута
HEAD = 92         # высота шапки (русское имя + имя таблицы)
KEYW = 78         # ширина колонки ключей
FONT = "Times New Roman"

BORDER = "#A31F45"
DASHED = "#8A8A8A"
HEAD_FILL = "#F2F2F2"
KEY_FILL = "#FAFAFA"
GRID = "#D6D6D6"
KEY_TXT = "#1F4E79"
LINE = "#222222"
SW = 2.6          # толщина линий связей


class Table:
    def __init__(self, title, code, rows, x, y, w=420, stub=False, note=None):
        self.title, self.code, self.rows = title, code, rows
        self.x, self.y, self.w, self.stub, self.note = x, y, w, stub, note
        self.kw = KEYW + 18 if any("," in r[0] for r in rows) else KEYW

    @property
    def h(self):
        return HEAD + ROW * len(self.rows) + (ROW if self.note else 0)

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    def ry(self, name, k=0):
        """Центр строки атрибута name (k – номер вхождения)."""
        idx = [i for i, r in enumerate(self.rows) if r[1] == name][k]
        return self.y + HEAD + ROW * idx + ROW / 2

    def svg(self):
        x, y, w = self.x, self.y, self.w
        col = DASHED if self.stub else BORDER
        dash = ' stroke-dasharray="10 6"' if self.stub else ""
        o = [f'<g>']
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{HEAD}" fill="{HEAD_FILL}"/>')
        body_h = self.h - HEAD
        o.append(f'<rect x="{x}" y="{y+HEAD}" width="{self.kw}" height="{body_h}" fill="{KEY_FILL}"/>')
        o.append(f'<text x="{x+w/2}" y="{y+39}" text-anchor="middle" font-size="31" font-weight="bold">{escape(self.title)}</text>')
        o.append(f'<text x="{x+w/2}" y="{y+76}" text-anchor="middle" font-size="24" fill="#555" letter-spacing="0.6">{escape(self.code)}</text>')
        for i, (key, name, *_rest) in enumerate(self.rows):
            ry = y + HEAD + ROW * i
            if i:
                o.append(f'<line x1="{x}" y1="{ry}" x2="{x+w}" y2="{ry}" stroke="{GRID}" stroke-width="1.2"/>')
            if key:
                fs = 22 if "," in key else 24
                o.append(f'<text x="{x+self.kw/2}" y="{ry+ROW/2+8}" text-anchor="middle" font-size="{fs}" font-weight="bold" fill="{KEY_TXT}">{key}</text>')
            bold = ' font-weight="bold"' if "PK" in key else ""
            o.append(f'<text x="{x+self.kw+16}" y="{ry+ROW/2+10}" font-size="29"{bold}>{escape(name)}</text>')
        if self.note:
            ny = y + HEAD + ROW * len(self.rows)
            o.append(f'<line x1="{x}" y1="{ny}" x2="{x+w}" y2="{ny}" stroke="{GRID}" stroke-width="1.2"/>')
            o.append(f'<rect x="{x+1}" y="{ny+1}" width="{w-2}" height="{ROW-2}" fill="#fff"/>')
            o.append(f'<text x="{x+w/2}" y="{ny+ROW/2+8}" text-anchor="middle" font-size="23" font-style="italic" fill="#666">{escape(self.note)}</text>')
        o.append(f'<line x1="{x+self.kw}" y1="{y+HEAD}" x2="{x+self.kw}" y2="{y+self.h - (ROW if self.note else 0)}" stroke="{GRID}" stroke-width="1.2"/>')
        o.append(f'<line x1="{x}" y1="{y+HEAD}" x2="{x+w}" y2="{y+HEAD}" stroke="{col}" stroke-width="3"{dash}/>')
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{self.h}" fill="none" stroke="{col}" stroke-width="3.2"{dash}/>')
        o.append('</g>')
        return "\n".join(o)


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = (dx * dx + dy * dy) ** 0.5
    return dx / n, dy / n


def marker(p, q, kind):
    """Обозначение кратности на конце p; q – следующая точка линии (направление от таблицы)."""
    ux, uy = _unit(p, q)
    px, py = -uy, ux
    o = []

    def at(d):
        return p[0] + ux * d, p[1] + uy * d

    def bar(d, half=13):
        cx, cy = at(d)
        o.append(f'<line x1="{cx+px*half:.1f}" y1="{cy+py*half:.1f}" x2="{cx-px*half:.1f}" y2="{cy-py*half:.1f}"/>')

    def circle(d, r=9):
        cx, cy = at(d)
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#fff"/>')

    def crow(length=26, spread=15):
        ax, ay = at(length)
        for s in (-1, 1):
            o.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{p[0]+px*spread*s:.1f}" y2="{p[1]+py*spread*s:.1f}"/>')

    if kind == "one":            # ровно один
        bar(13); bar(23)
    elif kind == "zero_one":     # ноль или один
        bar(13); circle(33)
    elif kind == "many":         # один или много
        crow(); bar(34)
    elif kind == "zero_many":    # ноль или много
        crow(); circle(36)
    return "\n".join(o)


class Link:
    """Связь: points – ломаная от родителя (PK) к потомку (FK)."""

    def __init__(self, points, parent="one", child="zero_many", bracket_start=None, bracket_end=None):
        self.points, self.parent, self.child = points, parent, child
        self.bs, self.be = bracket_start, bracket_end

    def svg(self):
        pts = self.points
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        o = [f'<polyline points="{d}" fill="none"/>']

        def off(p, q, br):  # при скобке обозначение начинается от скобки, а не от края таблицы
            if not br:
                return p
            ux, uy = _unit(p, q)
            return p[0] + ux * 9, p[1] + uy * 9
        o.append(marker(off(pts[0], pts[1], self.bs), pts[1], self.parent))
        o.append(marker(off(pts[-1], pts[-2], self.be), pts[-2], self.child))
        for br, p, q in ((self.bs, pts[0], pts[1]), (self.be, pts[-1], pts[-2])):
            if br:
                o.append(bracket(p, q, br))
        return "\n".join(o)


def bracket(p, q, span):
    """Скобка, объединяющая строки составного ключа: span=(y_top, y_bottom), край таблицы – p."""
    side = 1 if q[0] > p[0] else -1
    x0, x1 = p[0] + side * 9, p[0]
    y0, y1 = span
    return (f'<polyline points="{x1},{y0} {x0},{y0} {x0},{y1} {x1},{y1}" fill="none" stroke-width="2.2"/>'
            f'<line x1="{x0}" y1="{p[1]}" x2="{p[0]}" y2="{p[1]}"/>')


def junction(x, y):
    return f'<circle cx="{x}" cy="{y}" r="5.5" fill="{LINE}" stroke="none"/>'


def legend(x, y, w, junction=False, composite=False):
    """Легенда: кратности (сетка), виды ключей и при необходимости ответвление."""
    h = 210
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#BDBDBD" stroke-width="2"/>']
    o.append(f'<text x="{x+30}" y="{y+56}" font-size="27" font-weight="bold">Обозначения</text>')
    o.append(f'<text x="{x+30}" y="{y+90}" font-size="27" font-weight="bold">кратности связей:</text>')
    items = [("one", "ровно один"), ("zero_one", "ноль или один"),
             ("many", "один или много"), ("zero_many", "ноль или много")]
    gx = x + 300
    cw = (w - 330) / 2
    for i, (k, label) in enumerate(items):
        lx, ly = gx + cw * (i % 2), y + 48 + 46 * (i // 2)
        o.append(f'<g stroke="{LINE}" stroke-width="{SW}" fill="none">'
                 f'<line x1="{lx}" y1="{ly}" x2="{lx+96}" y2="{ly}"/>'
                 f'{marker((lx+96, ly), (lx, ly), k)}</g>')
        o.append(f'<text x="{lx+112}" y="{ly+9}" font-size="27">– {label}</text>')
    ky = y + h - 36
    o.append(f'<line x1="{x+30}" y1="{ky-40}" x2="{x+w-30}" y2="{ky-40}" stroke="#E2E2E2" stroke-width="1.5"/>')
    o.append(f'<text x="{x+30}" y="{ky+9}" font-size="27" font-weight="bold">Ключи:</text>')
    kx = gx
    for k, label in (("PK", "первичный"), ("FK", "внешний"), ("UK", "уникальный")):
        o.append(f'<text x="{kx}" y="{ky+9}" font-size="25" font-weight="bold" fill="{KEY_TXT}">{k}</text>')
        o.append(f'<text x="{kx+46}" y="{ky+9}" font-size="27">– {label}</text>')
        kx += 220
    if junction:
        jx = x + w - 420
        o.append(f'<g stroke="{LINE}" stroke-width="{SW}"><line x1="{jx}" y1="{ky}" x2="{jx+96}" y2="{ky}"/>'
                 f'<line x1="{jx+48}" y1="{ky}" x2="{jx+48}" y2="{ky+20}"/></g>'
                 f'<circle cx="{jx+48}" cy="{ky}" r="5.5" fill="{LINE}"/>')
        o.append(f'<text x="{jx+112}" y="{ky+9}" font-size="27">– ответвление связи</text>')
    if composite:
        jx = x + w - 470
        o.append(f'<g stroke="{LINE}" stroke-width="{SW}" fill="none"><line x1="{jx}" y1="{ky}" x2="{jx+87}" y2="{ky}"/>'
                 f'<polyline points="{jx+96},{ky-16} {jx+87},{ky-16} {jx+87},{ky+16} {jx+96},{ky+16}" stroke-width="2.2"/></g>')
        o.append(f'<text x="{jx+112}" y="{ky+9}" font-size="27">– составной ключ</text>')
    return "\n".join(o), h


def document(width, height, tables, links, extra=""):
    body = [t.svg() for t in tables]
    lines = [l.svg() for l in links]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{FONT}" fill="#111">
<rect width="100%" height="100%" fill="#fff"/>
<g stroke="{LINE}" stroke-width="{SW}" stroke-linecap="square" stroke-linejoin="miter" fill="none">
{chr(10).join(lines)}
</g>
{chr(10).join(body)}
{extra}
</svg>'''
