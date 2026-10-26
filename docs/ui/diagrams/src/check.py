"""Проверка маршрутов связей: короткие отрезки у узлов, пересечения линий с чужими узлами и между собой."""
import sys, importlib, io, contextlib
import act

MIN_OUT, MIN_IN = 18, 30


def segs(pts):
    return list(zip(pts, pts[1:]))


def hit_rect(a, b, r, pad=3):
    (x0, y0), (x1, y1) = a, b
    rx0, ry0, rx1, ry1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    if abs(x0 - x1) < 0.5:
        lo, hi = sorted((y0, y1))
        return rx0 < x0 < rx1 and lo < ry1 and hi > ry0
    lo, hi = sorted((x0, x1))
    return ry0 < y0 < ry1 and lo < rx1 and hi > rx0


def cross(s, t):
    (a, b), (c, d) = s, t
    h1, h2 = abs(a[1] - b[1]) < .5, abs(c[1] - d[1]) < .5
    if h1 == h2:
        return False
    if not h1:
        (a, b), (c, d) = (c, d), (a, b)
    y = a[1]; x = c[0]
    lo, hi = sorted((a[0], b[0])); lo2, hi2 = sorted((c[1], d[1]))
    return lo + 1 < x < hi - 1 and lo2 + 1 < y < hi2 - 1


def run(name):
    with contextlib.redirect_stdout(io.StringIO()):
        mod = importlib.import_module(name)
    d = mod.d
    d.place_labels()
    rects = {k: (n.cx - n.w / 2, n.cy - n.h / 2, n.cx + n.w / 2, n.cy + n.h / 2) for k, n in d.nodes.items()}
    routes = []
    probs = []
    for ed in d.edges:
        pts = d.route(ed)
        routes.append((ed, pts))
        ss = segs(pts)
        if len(ss) == 1:
            (a, b) = ss[0]
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 32:
                probs.append(f"короткая стрелка {ed['a']}→{ed['b']}: {abs(a[0]-b[0]) + abs(a[1]-b[1]):.0f}")
        if len(ss) > 1:
            (a, b) = ss[0]
            if abs(a[0] - b[0]) < .5 and abs(a[1] - b[1]) < MIN_OUT:
                probs.append(f"короткий выход {ed['a']}→{ed['b']}: {abs(a[1]-b[1]):.0f}")
            (a, b) = ss[-1]
            L = abs(a[1] - b[1]) + abs(a[0] - b[0])
            if L < MIN_IN:
                probs.append(f"короткий вход {ed['a']}→{ed['b']}: {L:.0f}")
        for s in ss:
            for k, r in rects.items():
                if k in (ed["a"], ed["b"]):
                    continue
                if hit_rect(*s, r, pad=20):
                    probs.append(f"линия {ed['a']}→{ed['b']} задевает {k}")
    for ed in d.edges:
        if ed.get("lbl_bad"):
            probs.append(f"подпись [{ed['label']}] {ed['a']}→{ed['b']} не помещается без наложения")
    keys = list(rects)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            p, q = rects[keys[i]], rects[keys[j]]
            if p[0] < q[2] + 12 and p[2] > q[0] - 12 and p[1] < q[3] + 12 and p[3] > q[1] - 12:
                probs.append(f"узлы {keys[i]} и {keys[j]} слишком близко")
    ports = {}
    for ed, pts in routes:
        ports.setdefault((ed["a"], ed["exit"]), set()).add("out")
        ports.setdefault((ed["b"], ed["enter"]), set()).add("in")
    for (k, side), v in ports.items():
        if len(v) > 1 and d.nodes[k].kind != "bar":
            probs.append(f"у {k} сторона {side} и вход, и выход")
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            for s in segs(routes[i][1]):
                for t in segs(routes[j][1]):
                    if cross(s, t):
                        probs.append(f"пересечение {routes[i][0]['a']}→{routes[i][0]['b']} и {routes[j][0]['a']}→{routes[j][0]['b']}")
    return probs


if __name__ == "__main__":
    total = 0
    for n in sys.argv[1:]:
        p = run(n)
        total += len(p)
        print(n, "OK" if not p else "")
        for x in p:
            print("   ", x)
    sys.exit(1 if total else 0)
