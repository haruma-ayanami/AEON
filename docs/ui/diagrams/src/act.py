"""UML-диаграммы активности с дорожками (swimlanes) для раздела 3.1 отчёта.

Узлы размещаются вручную: дорожка, смещение от её центра и номер строки.
Связи прокладываются ортогонально по правилам выхода/входа (b, t, l, r).
"""
from xml.sax.saxutils import escape
from PIL import ImageFont

FONT = "Times New Roman"
TTF = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
TTF_I = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
FS = 25            # кегль действий
GS = 22            # кегль условий переходов
LH = 30            # межстрочный интервал в действиях
PAD_X, PAD_Y = 18, 13
ROWH = 96          # шаг строк
HEADH = 92         # высота шапки дорожки
MARGIN = 24
LINE = "#2B2B2B"

_f = ImageFont.truetype(TTF, FS)
_fi = ImageFont.truetype(TTF_I, GS)

# оформление действий по дорожкам
STYLE = {
    "user":   ("#EEF4FB", "#2F6DB5"),
    "client": ("#F5F5F5", "#7A7A7A"),
    "server": ("#FBF0F3", "#A31F45"),
    "chain":  ("#F1F6F1", "#3F7A52"),
    "call":   ("#FFFFFF", "#333333"),
}


def text_w(s, font=_f):
    return font.getlength(s)


def wrap(text, maxw):
    """Перенос по словам с выравниванием длины строк (без коротких «хвостов»)."""
    n = len(_greedy(text, maxw))
    lo, hi = 40, maxw
    while hi - lo > 2:
        mid = (lo + hi) / 2
        if len(_greedy(text, mid)) <= n:
            hi = mid
        else:
            lo = mid
    return _greedy(text, hi)


def _greedy(text, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if text_w(t) <= maxw or not line:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


class Node:
    def __init__(self, d, key, kind, lane, row, text="", dx=0, w=None, call=False, style=None):
        self.d, self.key, self.kind, self.lane, self.row = d, key, kind, lane, row
        self.style = style or ("call" if call else None)
        self.text, self.dx, self.call = text, dx, call
        self.maxw = w
        self.layout()

    def layout(self):
        d = self.d
        lx, lw = d.lane_x[self.lane], d.lanes[self.lane][1]
        self.cx = lx + lw / 2 + self.dx
        self.cy = d.top + HEADH + d.rowh * self.row + d.rowh / 2
        if self.kind == "action":
            maxw = (self.maxw or lw - 60) - 2 * PAD_X
            self.lines = wrap(self.text, maxw)
            tw = max(text_w(l) for l in self.lines)
            self.w = max(tw + 2 * PAD_X + (26 if self.call else 0), 120)
            self.h = len(self.lines) * LH + 2 * PAD_Y - 4
        elif self.kind in ("decision", "merge"):
            self.w = self.h = 46
        elif self.kind == "start":
            self.w = self.h = 30
        elif self.kind == "end":
            self.w = self.h = 36
        elif self.kind == "bar":
            self.w, self.h = (self.maxw or 260), 9

    def port(self, side):
        return {"t": (self.cx, self.cy - self.h / 2), "b": (self.cx, self.cy + self.h / 2),
                "l": (self.cx - self.w / 2, self.cy), "r": (self.cx + self.w / 2, self.cy)}[side]

    def svg(self):
        x, y, w, h = self.cx - self.w / 2, self.cy - self.h / 2, self.w, self.h
        if self.kind == "action":
            fill, stroke = STYLE[self.style or self.d.lanes[self.lane][2]]
            o = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="15" fill="{fill}" stroke="{stroke}" stroke-width="2.2"/>']
            tx = self.cx - (13 if self.call else 0)
            ty = self.cy - (len(self.lines) - 1) * LH / 2 + FS * 0.34
            for i, l in enumerate(self.lines):
                o.append(f'<text x="{tx:.1f}" y="{ty + i * LH:.1f}" text-anchor="middle" font-size="{FS}">{escape(l)}</text>')
            if self.call:  # значок вызова поведения (UML call behavior action)
                rx, ry = x + w - 24, y + h - 12
                o.append(f'<g stroke="{stroke}" stroke-width="2" fill="none"><line x1="{rx}" y1="{ry-16}" x2="{rx}" y2="{ry}"/>'
                         f'<line x1="{rx-8}" y1="{ry-8}" x2="{rx+8}" y2="{ry-8}"/><line x1="{rx-8}" y1="{ry-8}" x2="{rx-8}" y2="{ry}"/>'
                         f'<line x1="{rx+8}" y1="{ry-8}" x2="{rx+8}" y2="{ry}"/></g>')
            return "\n".join(o)
        if self.kind in ("decision", "merge"):
            c, r = (self.cx, self.cy), 23
            pts = f"{c[0]},{c[1]-r} {c[0]+r},{c[1]} {c[0]},{c[1]+r} {c[0]-r},{c[1]}"
            o = [f'<polygon points="{pts}" fill="#FFFDF5" stroke="{LINE}" stroke-width="2.2"/>']
            if self.text:
                o.append(f'<text x="{c[0]+r+10}" y="{c[1]-r+2}" font-size="{GS}" font-style="italic" fill="#333">{escape(self.text)}</text>')
            return "\n".join(o)
        if self.kind == "start":
            return f'<circle cx="{self.cx}" cy="{self.cy}" r="15" fill="{LINE}"/>'
        if self.kind == "end":
            return (f'<circle cx="{self.cx}" cy="{self.cy}" r="18" fill="#fff" stroke="{LINE}" stroke-width="2.4"/>'
                    f'<circle cx="{self.cx}" cy="{self.cy}" r="11" fill="{LINE}"/>')
        if self.kind == "bar":
            return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{LINE}"/>'


class Diagram:
    def __init__(self, lanes, rows, rowh=ROWH):
        """lanes: [(заголовок, ширина, стиль)]"""
        self.lanes, self.rows, self.rowh = lanes, rows, rowh
        self.top = MARGIN
        self.lane_x, x = [], MARGIN
        for _, w, _ in lanes:
            self.lane_x.append(x)
            x += w
        self.width = x + MARGIN
        self.height = int(self.top + HEADH + rowh * rows + 20 + MARGIN)
        self.nodes, self.edges, self.extra = {}, [], []

    def n(self, key, kind, lane, row, text="", **kw):
        self.nodes[key] = Node(self, key, kind, lane, row, text, **kw)
        return self.nodes[key]

    def act(self, key, lane, row, text, **kw):
        return self.n(key, "action", lane, row, text, **kw)

    def e(self, a, b, label=None, exit=None, enter="t", via_x=None, via_y=None, points=None, lpos=None):
        self.edges.append(dict(a=a, b=b, label=label, exit=exit, enter=enter, via_x=via_x, via_y=via_y, points=points, lpos=lpos))

    def route(self, ed):
        A, B = self.nodes[ed["a"]], self.nodes[ed["b"]]
        if A.kind == "bar" and abs(B.cx - A.cx) < A.w / 2:   # из планки fork – вертикально вниз к узлу
            return [(B.cx, A.cy + A.h / 2), B.port("t")]
        if B.kind == "bar" and abs(A.cx - B.cx) < B.w / 2:   # в планку join – вертикально вниз от узла
            return [A.port("b"), (A.cx, B.cy - B.h / 2)]
        if ed["points"] is not None:
            return [A.port(ed["exit"])] + list(ed["points"]) + [B.port(ed["enter"])]
        ex, en = ed["exit"], ed["enter"]
        if ex is None:
            # по умолчанию: узел в другой колонке – выход сбоку и вход сверху (Г-образно),
            # иначе – вниз; так у блоков не остаётся коротких изломов
            if en == "t" and ed["via_y"] is None and abs(B.cx - A.cx) > A.w / 2 + 12 and B.cy - A.cy > A.h / 2 + 30:
                ex = "r" if B.cx > A.cx else "l"
            else:
                ex = "b"
            ed["exit"] = ex
        p0, p1 = A.port(ex), B.port(en)
        (x0, y0), (x1, y1) = p0, p1
        if ex == "b" and en == "t":
            if abs(x0 - x1) < 0.5:
                return [p0, p1]
            ym = ed["via_y"] if ed["via_y"] is not None else (y0 + y1) / 2 if y1 - y0 < 1.6 * self.rowh else y1 - 30
            return [p0, (x0, ym), (x1, ym), p1]
        if ex in "lr" and en == "t":
            if ed["via_x"] is not None:
                return [p0, (ed["via_x"], y0), (ed["via_x"], y1 - 30), (x1, y1 - 30), p1]
            return [p0, (x1, y0), p1]
        if ex == "b" and en in "lr":
            if ed["via_y"] is not None:
                return [p0, (x0, ed["via_y"]), (ed["via_x"], ed["via_y"]), (ed["via_x"], y1), p1]
            return [p0, (x0, y1), p1]
        if ex in "lr" and en in "lr":
            if abs(y0 - y1) < 0.5 and ed["via_x"] is None:
                return [p0, p1]
            vx = ed["via_x"] if ed["via_x"] is not None else (x0 + x1) / 2
            return [p0, (vx, y0), (vx, y1), p1]
        if ex in "lr" and en == "b":
            return [p0, (x1, y0), p1]
        if ex == "t" and en in "lr":
            return [p0, (x0, y1), p1]
        raise ValueError(ed)

    def edge_svg(self, ed):
        pts = self.route(ed)
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        o = [f'<polyline points="{d}" fill="none" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>']
        (xa, ya), (xb, yb) = pts[-2], pts[-1]
        L = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5 or 1
        ux, uy = (xb - xa) / L, (yb - ya) / L
        px, py = -uy, ux
        s, hw = 14, 6.5
        o.append(f'<polyline points="{xb-ux*s+px*hw:.1f},{yb-uy*s+py*hw:.1f} {xb:.1f},{yb:.1f} {xb-ux*s-px*hw:.1f},{yb-uy*s-py*hw:.1f}" '
                 f'fill="none" stroke="{LINE}" stroke-width="2"/>')
        if ed["label"]:
            t = "[" + ed["label"] + "]"
            tw = text_w(t, _fi)
            (x0, y0), (x1, y1) = pts[0], pts[1]
            if ed["lpos"]:
                lx, ly, anchor = ed["lpos"]
            elif abs(y0 - y1) < 0.5:   # первый отрезок горизонтальный – подпись над ним
                anchor = "start" if x1 > x0 else "end"
                lx, ly = x0 + (10 if x1 > x0 else -10), y0 - 9
            else:                      # вертикальный – подпись справа
                anchor, lx, ly = "start", x0 + 9, y0 + 24
            if anchor == "middle":
                bx = lx - tw / 2
            else:
                bx = lx if anchor == "start" else lx - tw
            o.append(f'<rect x="{bx-3:.1f}" y="{ly-GS+3:.1f}" width="{tw+6:.1f}" height="{GS+3}" fill="#fff" opacity="0.92"/>')
            o.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="{GS}" font-style="italic" fill="#222">{escape(t)}</text>')
        return "\n".join(o)

    def svg(self):
        W, H = self.width, self.height
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}" fill="#111">',
             f'<rect width="100%" height="100%" fill="#fff"/>']
        top, bot = self.top, H - MARGIN
        for i, (title, w, _) in enumerate(self.lanes):
            x = self.lane_x[i]
            o.append(f'<rect x="{x}" y="{top}" width="{w}" height="{HEADH}" fill="#F0F0F0"/>')
            lines = title.split("\n")
            for j, l in enumerate(lines):
                fs, wt, col = (27, "bold", "#111") if j == 0 else (22, "normal", "#555")
                yy = top + HEADH / 2 + (j - (len(lines) - 1) / 2) * 32 + 9
                o.append(f'<text x="{x+w/2}" y="{yy}" text-anchor="middle" font-size="{fs}" font-weight="{wt}" fill="{col}">{escape(l)}</text>')
            if i:
                o.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bot}" stroke="#555" stroke-width="2"/>')
        o.append(f'<line x1="{MARGIN}" y1="{top+HEADH}" x2="{W-MARGIN}" y2="{top+HEADH}" stroke="#555" stroke-width="2"/>')
        o.append(f'<rect x="{MARGIN}" y="{top}" width="{W-2*MARGIN}" height="{bot-top}" fill="none" stroke="#333" stroke-width="2.6"/>')
        o += self.extra
        o += [self.edge_svg(e) for e in self.edges]
        o += [n.svg() for n in self.nodes.values()]
        o.append("</svg>")
        return "\n".join(o)

    def save(self, name):
        # рамка всегда охватывает нижний узел с запасом 34 px
        low = max(n.cy + n.h / 2 for n in self.nodes.values())
        self.height = int(max(self.height, low + 34 + MARGIN))
        open(name + ".svg", "w").write(self.svg())
        return self.width, self.height


U, C, S, B = "user", "client", "server", "chain"


def lanes3(user="Пользователь", wu=520, wc=540, ws=520):
    return [(user, wu, U),
            ("Клиентское приложение\nвеб / мобильное / десктоп", wc, C),
            ("Сервер AEON\nASP.NET Core", ws, S)]


def lanes4(user="Пользователь", wu=470, wc=470, ws=470, wb=380):
    return [(user, wu, U),
            ("Клиентское приложение\nвеб / мобильное / десктоп", wc, C),
            ("Сервер AEON\nASP.NET Core", ws, S),
            ("Блокчейн-сеть\nтестовая", wb, B)]
