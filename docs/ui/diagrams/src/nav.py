"""Схемы навигации по экранным формам и графы состояний меню (разделы 3.2, 3.3)."""
from xml.sax.saxutils import escape
from act import text_w, wrap, FONT, TTF
from PIL import ImageFont

LINE = "#2B2B2B"
BLUE = "#1F4E79"
BORD = "#A31F45"
_fb = ImageFont.truetype("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf", 25)


class Box:
    def __init__(self, key, cx, cy, title, ops="", code="", w=290, kind="form", h=None):
        self.key, self.cx, self.cy, self.title, self.ops, self.code = key, cx, cy, title, ops, code
        self.w, self.kind = w, kind
        lines = wrap(title, w - 30)
        self.lines = lines
        self.h = h or (24 + 30 * len(lines) + (30 if ops else 0) + 18)

    @property
    def x0(self): return self.cx - self.w / 2
    @property
    def y0(self): return self.cy - self.h / 2
    @property
    def x1(self): return self.cx + self.w / 2
    @property
    def y1(self): return self.cy + self.h / 2

    def clip(self, px, py):
        """Точка на границе по направлению от центра к (px, py)."""
        dx, dy = px - self.cx, py - self.cy
        if dx == 0 and dy == 0:
            return self.cx, self.cy
        tx = (self.w / 2) / abs(dx) if dx else 1e9
        ty = (self.h / 2) / abs(dy) if dy else 1e9
        t = min(tx, ty)
        return self.cx + dx * t, self.cy + dy * t

    def svg(self):
        if self.kind == "hub":
            fill, stroke, sw, dash = "#F2F2F2", BORD, 3.4, ""
        elif self.kind == "ext":
            fill, stroke, sw, dash = "#FFFFFF", "#8A8A8A", 2.4, ' stroke-dasharray="9 6"'
        elif self.kind == "state":
            fill, stroke, sw, dash = "#FFFFFF", BLUE, 2.6, ""
        else:
            fill, stroke, sw, dash = "#FFFFFF", BORD, 2.6, ""
        rx = 22 if self.kind == "state" else 10
        o = [f'<rect x="{self.x0:.1f}" y="{self.y0:.1f}" width="{self.w}" height="{self.h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>']
        n = len(self.lines) + (1 if self.ops else 0)
        y = self.cy - (n - 1) * 15 + 9
        for i, l in enumerate(self.lines):
            o.append(f'<text x="{self.cx}" y="{y + 30 * i:.1f}" text-anchor="middle" font-size="25" font-weight="bold">{escape(l)}</text>')
        if self.ops:
            o.append(f'<text x="{self.cx}" y="{y + 30 * len(self.lines) + 2:.1f}" text-anchor="middle" font-size="23" fill="{BLUE}">{escape(self.ops)}</text>')
        return "\n".join(o)


class Actor:
    def __init__(self, key, cx, cy, label):
        self.key, self.cx, self.cy, self.label = key, cx, cy, label
        self.w, self.h = 60, 130

    def clip(self, px, py):
        return (self.cx + (34 if px > self.cx else -34), self.cy)

    def svg(self):
        x, y = self.cx, self.cy - 40
        c = BLUE
        return (f'<g stroke="{c}" stroke-width="3" fill="none"><circle cx="{x}" cy="{y-28}" r="16"/>'
                f'<line x1="{x}" y1="{y-12}" x2="{x}" y2="{y+34}"/><line x1="{x-26}" y1="{y+6}" x2="{x+26}" y2="{y+6}"/>'
                f'<line x1="{x}" y1="{y+34}" x2="{x-22}" y2="{y+72}"/><line x1="{x}" y1="{y+34}" x2="{x+22}" y2="{y+72}"/></g>'
                f'<text x="{x}" y="{y+106}" text-anchor="middle" font-size="25" fill="{c}">{escape(self.label)}</text>')


def arrow(x0, y0, x1, y1, color=LINE):
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    s, hw = 17, 7
    return (f'<polygon points="{x1:.1f},{y1:.1f} {x1-ux*s+px*hw:.1f},{y1-uy*s+py*hw:.1f} '
            f'{x1-ux*s-px*hw:.1f},{y1-uy*s-py*hw:.1f}" fill="{color}"/>')


class Graph:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.items, self.edges, self.extra = {}, [], []

    def box(self, key, *a, **kw):
        self.items[key] = Box(key, *a, **kw)
        return self.items[key]

    def actor(self, key, *a):
        self.items[key] = Actor(key, *a)

    def e(self, a, b, label="", both=False, dashed=False, points=None, t=0.5, lpos=None, start=None, end=None):
        self.edges.append(dict(a=a, b=b, label=label, both=both, dashed=dashed, points=points or [], t=t, lpos=lpos,
                               start=start, end=end))

    def edge_svg(self, ed):
        A, B = self.items[ed["a"]], self.items[ed["b"]]
        mids = ed["points"]
        p0 = ed["start"] or A.clip(*(mids[0] if mids else (B.cx, B.cy)))
        p1 = ed["end"] or B.clip(*(mids[-1] if mids else (A.cx, A.cy)))
        pts = [p0] + mids + [p1]
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        col = "#666" if ed["dashed"] else LINE
        dash = ' stroke-dasharray="10 7"' if ed["dashed"] else ""
        o = [f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="2.4"{dash}/>']
        o.append(arrow(*pts[-2], *pts[-1], col))
        if ed["both"]:
            o.append(arrow(*pts[1], *pts[0], col))
        if ed["label"]:
            if ed["lpos"]:
                lx, ly = ed["lpos"]
            else:  # середина самого длинного отрезка
                segs = list(zip(pts, pts[1:]))
                (xa, ya), (xb, yb) = max(segs, key=lambda s: (s[1][0] - s[0][0]) ** 2 + (s[1][1] - s[0][1]) ** 2)
                lx, ly = xa + (xb - xa) * ed["t"], ya + (yb - ya) * ed["t"]
            tw = text_w(ed["label"]) * 0.9
            o.append(f'<rect x="{lx - tw/2 - 9:.1f}" y="{ly - 17:.1f}" width="{tw + 18:.1f}" height="34" rx="17" fill="#fff" stroke="{BLUE}" stroke-width="1.6"/>')
            o.append(f'<text x="{lx:.1f}" y="{ly + 7.5:.1f}" text-anchor="middle" font-size="23" fill="{BLUE}">{escape(ed["label"])}</text>')
        return "\n".join(o)

    def save(self, name):
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" viewBox="0 0 {self.W} {self.H}" font-family="{FONT}" fill="#111">',
             '<rect width="100%" height="100%" fill="#fff"/>']
        o += self.extra
        o += [self.edge_svg(e) for e in self.edges]
        o += [i.svg() for i in self.items.values()]
        o.append("</svg>")
        open(name + ".svg", "w").write("\n".join(o))
        return self.W, self.H


def note(x, y, w, lines, fs=23):
    h = 22 + 32 * len(lines)
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FAFAFA" stroke="#BDBDBD" stroke-width="1.6"/>']
    for i, l in enumerate(lines):
        o.append(f'<text x="{x+22}" y="{y+40+32*i}" font-size="{fs}">{l}</text>')
    return "\n".join(o)
