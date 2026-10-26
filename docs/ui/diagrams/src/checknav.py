"""Проверка схем навигации и графов состояний: наложения блоков, линий и подписей."""
import sys, importlib, io, contextlib
from check import hit_rect, cross, segs


def inter(p, q, pad=0):
    return p[0] - pad < q[2] and p[2] + pad > q[0] and p[1] - pad < q[3] and p[3] + pad > q[1]


def seg_hits_rect(a, b, r, pad):
    # отрезок любой ориентации: проверка по точкам
    n = 60
    for i in range(n + 1):
        x = a[0] + (b[0] - a[0]) * i / n; y = a[1] + (b[1] - a[1]) * i / n
        if r[0] - pad < x < r[2] + pad and r[1] - pad < y < r[3] + pad:
            return True
    return False


def run(name):
    with contextlib.redirect_stdout(io.StringIO()):
        g = importlib.import_module(name).g
    for e in g.edges:
        g.edge_svg(e)
    boxes = {k: (i.cx - i.w / 2, i.cy - i.h / 2, i.cx + i.w / 2, i.cy + i.h / 2) for k, i in g.items.items()}
    P = []
    ks = list(boxes)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            if inter(boxes[ks[i]], boxes[ks[j]], 20):
                P.append(f"блоки {ks[i]} и {ks[j]} слишком близко")
    for e in g.edges:
        for a, b in segs(e["pts"]):
            for k, r in boxes.items():
                if k in (e["a"], e["b"]):
                    continue
                if seg_hits_rect(a, b, r, 14):
                    P.append(f"линия {e['a']}→{e['b']} задевает {k}")
        if "pill" in e:
            tips = [e["pts"][-1]] + ([e["pts"][0]] if e["both"] else [])
            for (x, y) in tips:
                r = e["pill"]
                if r[0] - 14 < x < r[2] + 14 and r[1] - 14 < y < r[3] + 14:
                    P.append(f"подпись {e['label']} ({e['a']}→{e['b']}) закрывает стрелку")
            for k, r in boxes.items():
                if inter(e["pill"], r, 14):
                    P.append(f"подпись {e['label']} ({e['a']}→{e['b']}) задевает {k}")
            for f in g.edges:
                if f is e:
                    continue
                if "pill" in f and inter(e["pill"], f["pill"], 4):
                    P.append(f"подписи {e['label']} и {f['label']} накладываются")
                for a, b in segs(f["pts"]):
                    if seg_hits_rect(a, b, e["pill"], 2):
                        P.append(f"подпись {e['label']} ({e['a']}→{e['b']}) лежит на линии {f['a']}→{f['b']}")
                        break
    return sorted(set(P))


if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:]:
        p = run(n); bad += len(p)
        print(n, "OK" if not p else "")
        for x in p:
            print("   ", x)
    sys.exit(1 if bad else 0)
