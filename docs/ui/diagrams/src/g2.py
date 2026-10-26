# Граф состояний главного меню: администратор
from nav import *
g = Graph(1840, 860)
CX0, CY0, CX1, CY1 = 330, 40, 1810, 700
g.extra.append(f'<rect x="{CX0}" y="{CY0}" width="{CX1-CX0}" height="{CY1-CY0}" rx="30" fill="#FBFBFB" stroke="{BLUE}" stroke-width="2.6"/>')
g.extra.append(f'<line x1="{CX0}" y1="{CY0+52}" x2="{CX1}" y2="{CY0+52}" stroke="{BLUE}" stroke-width="1.6"/>')
g.extra.append(f'<text x="{CX0+26}" y="{CY0+36}" font-size="25" font-weight="bold" fill="{BLUE}">Работа администратора</text>')
S = dict(kind="state", w=290)
g.box("m0", 150, 370, "M0. Гость", "Ф2", kind="state", w=220)
g.box("a1", 600, 370, "MA1. Обзор", "Ф19", **S)
g.box("a2", 1000, 250, "MA2. Списки", "Ф20, Ф22, Ф24", **S)
g.box("a3", 1610, 250, "MA3. Карточка (редактирование)", "Ф21, Ф23", w=310, kind="state")
g.box("a4", 1610, 520, "MA4. Карточка сделки", "Ф25", **S)
g.box("a5", 1000, 560, "MA5. Журнал событий", "Ф26", **S)
I = g.items
b = I["a2"]; g.e("a2", "a2", "1, 2, 3", start=(b.cx, CY0 + 52), end=(b.cx, b.y0), lpos=(b.cx, (CY0 + 52 + b.y0) / 2))
b = I["a5"]; g.e("a5", "a5", "4", start=(b.cx, CY1), end=(b.cx, b.y1), lpos=(b.cx, (CY1 + b.y1) / 2))
b = I["a1"]; g.e("a1", "a1", "5", start=(b.cx, CY1), end=(b.cx, b.y1), lpos=(b.cx, (CY1 + b.y1) / 2))
g.e("m0", "a1", "0", lpos=(395, 370 - 30))
g.e("m0", "m0", "6", start=(CX0, 560), end=(I["m0"].cx, I["m0"].y1), points=[(I["m0"].cx, 560)], lpos=(250, 560))
g.e("a2", "a3", "1B, 2B / 1C, 2C, 9", both=True, lpos=(1300, 250 - 46))
g.e("a2", "a4", "3B / 9", both=True)
g.extra.append(note(40, 740, 1760, [
    "Команды раздела «Администрирование» (1–5) доступны из любого вложенного состояния; команда 6 – выход из панели."]))
print(*g.save("g2"))
