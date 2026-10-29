"""Общие макеты ГПИ: схемы навигации (рисунки 26–28), где формы показаны макетами окон (раздел 3.4.4)."""
from xml.sax.saxutils import escape
from act import text_w, wrap, FONT
from nav import Graph, arrow, LINE, BLUE, BORD

TW, TH = 420, 315          # окно миниатюры макета
FS_T, FS_O, FS_L = 36, 32, 29
K = FS_T / 25              # act.text_w и wrap меряют шрифтом 25 px
GREY = "#5A5A5A"


def tw(s, fs):
    return text_w(s) * fs / 25


class Card:
    """Форма: миниатюра макета, название, коды операций и выпадающие списки формы."""

    def __init__(self, key, cx, cy, title, ops="", lists="", kind="form"):
        self.key, self.cx, self.cy, self.title, self.ops, self.lists, self.kind = key, cx, cy, title, ops, lists, kind
        self.w = TW + 24
        self.lines = wrap(title, (self.w - 30) / K)
        self.llines = wrap(lists, (self.w - 64) * 25 / FS_L) if lists else []
        self.h = 12 + TH + 14 + 42 * len(self.lines) + (38 if ops else 0) + 36 * len(self.llines) + 14

    x0 = property(lambda s: s.cx - s.w / 2)
    x1 = property(lambda s: s.cx + s.w / 2)
    y0 = property(lambda s: s.cy - s.h / 2)
    y1 = property(lambda s: s.cy + s.h / 2)

    def clip(self, px, py):
        dx, dy = px - self.cx, py - self.cy
        if dx == 0 and dy == 0:
            return self.cx, self.cy
        t = min((self.w / 2) / abs(dx) if dx else 1e9, (self.h / 2) / abs(dy) if dy else 1e9)
        return self.cx + dx * t, self.cy + dy * t

    def svg(self):
        ext = self.kind == "ext"
        stroke, sw = ("#8A8A8A", 2.4) if ext else (BORD, 3.4 if self.kind == "hub" else 2.6)
        dash = ' stroke-dasharray="9 6"' if ext else ""
        fill = "#F2F2F2" if self.kind == "hub" else "#FFFFFF"
        o = [f'<rect x="{self.x0:.1f}" y="{self.y0:.1f}" width="{self.w}" height="{self.h:.1f}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>']
        ix, iy = self.x0 + 12, self.y0 + 12
        o.append(f'<rect x="{ix:.1f}" y="{iy:.1f}" width="{TW}" height="{TH}" fill="#070807"/>')
        op = ' opacity="0.55"' if ext else ""
        o.append(f'<image href="mock/{self.key}.png" x="{ix:.1f}" y="{iy:.1f}" width="{TW}" height="{TH}" preserveAspectRatio="xMidYMid meet"{op}/>')
        o.append(f'<rect x="{ix:.1f}" y="{iy:.1f}" width="{TW}" height="{TH}" fill="none" stroke="#3A3A3A" stroke-width="1.2"/>')
        y = iy + TH + 14 + 34
        for l in self.lines:
            o.append(f'<text x="{self.cx}" y="{y:.1f}" text-anchor="middle" font-size="{FS_T}" font-weight="bold">{escape(l)}</text>')
            y += 42
        if self.ops:
            o.append(f'<text x="{self.cx}" y="{y - 4:.1f}" text-anchor="middle" font-size="{FS_O}" fill="{BLUE}">{escape(self.ops)}</text>')
            y += 38
        for i, l in enumerate(self.llines):
            w = tw(l, FS_L) + (30 if i == 0 else 0)
            x = self.cx - w / 2
            if i == 0:  # значок выпадающего списка
                o.append(f'<rect x="{x:.1f}" y="{y - 27:.1f}" width="22" height="22" rx="4" fill="none" stroke="{GREY}" stroke-width="1.8"/>'
                         f'<path d="M{x + 6:.1f},{y - 19:.1f} l5,5 l5,-5" fill="none" stroke="{GREY}" stroke-width="2"/>')
                x += 30
            o.append(f'<text x="{x:.1f}" y="{y - 8:.1f}" font-size="{FS_L}" font-style="italic" fill="{GREY}">{escape(l)}</text>')
            y += 36
        return "\n".join(o)


class Actor:
    def __init__(self, key, cx, cy, label):
        self.key, self.cx, self.cy, self.label = key, cx, cy, label
        self.w, self.h = 70, 150

    def clip(self, px, py):
        return (self.cx + (40 if px > self.cx else -40), self.cy)

    def svg(self):
        x, y = self.cx, self.cy - 46
        return (f'<g stroke="{BLUE}" stroke-width="3.4" fill="none"><circle cx="{x}" cy="{y-32}" r="19"/>'
                f'<line x1="{x}" y1="{y-13}" x2="{x}" y2="{y+40}"/><line x1="{x-30}" y1="{y+7}" x2="{x+30}" y2="{y+7}"/>'
                f'<line x1="{x}" y1="{y+40}" x2="{x-26}" y2="{y+84}"/><line x1="{x}" y1="{y+40}" x2="{x+26}" y2="{y+84}"/></g>'
                f'<text x="{x}" y="{y+124}" text-anchor="middle" font-size="{FS_O}" fill="{BLUE}">{escape(self.label)}</text>')


class MockGraph(Graph):
    def card(self, key, *a, **kw):
        self.items[key] = Card(key, *a, **kw)
        return self.items[key]

    def actor(self, key, *a):
        self.items[key] = Actor(key, *a)

    def edge_svg(self, ed):
        A, B = self.items[ed["a"]], self.items[ed["b"]]
        mids = ed["points"]
        p0 = ed["start"] or A.clip(*(mids[0] if mids else (B.cx, B.cy)))
        p1 = ed["end"] or B.clip(*(mids[-1] if mids else (A.cx, A.cy)))
        pts = [p0] + mids + [p1]
        col = "#666" if ed["dashed"] else LINE
        dash = ' stroke-dasharray="12 8"' if ed["dashed"] else ""
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        o = [f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="3"{dash}/>', arrow(*pts[-2], *pts[-1], col)]
        if ed["both"]:
            o.append(arrow(*pts[1], *pts[0], col))
        if ed["label"]:
            if ed["lpos"]:
                lx, ly = ed["lpos"]
            else:
                (xa, ya), (xb, yb) = max(zip(pts, pts[1:]), key=lambda s: (s[1][0] - s[0][0]) ** 2 + (s[1][1] - s[0][1]) ** 2)
                lx, ly = xa + (xb - xa) * ed["t"], ya + (yb - ya) * ed["t"]
            w = tw(ed["label"], FS_O)
            o.append(f'<rect x="{lx - w/2 - 12:.1f}" y="{ly - 22:.1f}" width="{w + 24:.1f}" height="44" rx="22" fill="#fff" stroke="{BLUE}" stroke-width="2"/>')
            o.append(f'<text x="{lx:.1f}" y="{ly + 10:.1f}" text-anchor="middle" font-size="{FS_O}" fill="{BLUE}">{escape(ed["label"])}</text>')
        return "\n".join(o)


def note(x, y, w, lines, fs=FS_L + 1):
    h = 26 + 40 * len(lines)
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FAFAFA" stroke="#BDBDBD" stroke-width="1.8"/>']
    for i, l in enumerate(lines):
        o.append(f'<text x="{x + 26}" y="{y + 48 + 40 * i}" font-size="{fs}">{l}</text>')
    return "\n".join(o)
