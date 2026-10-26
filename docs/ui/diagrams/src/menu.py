# Макет главного меню клиентского приложения (полный состав разделов)
from xml.sax.saxutils import escape
from PIL import ImageFont
F = "Arial"
fa = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
SEP = None
MENU = [
    ("Кошелёк", [("Обзор", "Ctrl+1", "1"), ("Отправить…", "Ctrl+Shift+S", "1C"), ("Получить…", "Ctrl+Shift+R", "1G"), SEP,
                 ("История транзакций", "Ctrl+2", "2")]),
    ("P2P", [("Маркетплейс", "Ctrl+3", "3"), ("Мои сделки", "Ctrl+4", "4"), ("Мои объявления", "Ctrl+5", "5"), SEP,
             ("Создать объявление…", "Ctrl+N", "5A")]),
    ("Аналитика", [("Портфель", "", "-"), ("Проверка адреса…", "", "-")]),
    ("Уведомления", [("Центр уведомлений", "Ctrl+6", "6"), SEP, ("Прочитать все", "Ctrl+Shift+A", "6B")]),
    ("Профиль", [("Войти…", "", "0"), SEP, ("Личные данные", "Ctrl+7", "7"), SEP, ("Выход", "Ctrl+Q", "8")]),
    ("Действия", [("Открыть", "Enter", ""), ("Фильтры…", "Ctrl+F", ""), SEP, ("Сохранить", "Ctrl+S", ""),
                  ("Подтвердить…", "Ctrl+Enter", ""), ("Отменить", "Esc", ""), SEP, ("Отключить объявление", "Ctrl+D", "5D"),
                  ("Экспорт журнала…", "Ctrl+E", "4C*")]),
    ("Администрирование", [("Обзор панели", "Ctrl+0", "5*"), ("Пользователи", "Ctrl+Alt+1", "1*"), ("Объявления", "Ctrl+Alt+2", "2*"),
                           ("Сделки", "Ctrl+Alt+3", "3*"), ("Журнал событий", "Ctrl+Alt+4", "4*")]),
    ("Справка", [("Подсказка раздела", "F1", ""), SEP, ("О программе…", "", "")]),
]
ROW, PADX = 44, 18
o = []
def pw_of(title, items):
    wl = max(fa.getlength(i[0]) for i in items if i) + 40
    wh = max(fa.getlength(i[1]) for i in items if i) + 30
    return max(wl + wh + 2 * PADX, fa.getlength(title) + 60)
def ph_of(items):
    return sum(14 if i is None else ROW for i in items) + 16
grid = [MENU[0:3], MENU[3:6], MENU[6:8]]
ncol = 3
colw = [max(pw_of(*grid[r][c]) for r in range(len(grid)) if c < len(grid[r])) for c in range(ncol)]
GAPX, GAPY, TAB = 34, 50, 48
x0s = [30 + sum(colw[:c]) + GAPX * c for c in range(ncol)]
W = int(x0s[-1] + colw[-1] + 30)
y = 30
for r in range(len(grid)):
    rowh = max(ph_of(it) for _, it in grid[r])
    for c, (title, items) in enumerate(grid[r]):
        px, pw = x0s[c], colw[c]
        adm = title == "Администрирование"
        mi = 1 if adm else 0
        tw = fa.getlength(title) + 30
        o.append(f'<rect x="{px}" y="{y}" width="{tw}" height="{TAB-6}" rx="6" fill="#E2E8F0" stroke="#B8C2CF" stroke-width="1.4"/>')
        o.append(f'<text x="{px+15}" y="{y+29}" font-size="23" font-family="{F}" fill="{"#7A1F3A" if adm else "#111"}">'
                 f'{escape(title[:mi])}<tspan text-decoration="underline">{escape(title[mi])}</tspan>{escape(title[mi+1:])}</text>')
        yy0 = y + TAB
        h = ph_of(items)
        o.append(f'<rect x="{px+4}" y="{yy0+4}" width="{pw}" height="{h}" rx="8" fill="#000" opacity="0.08"/>')
        o.append(f'<rect x="{px}" y="{yy0}" width="{pw}" height="{h}" rx="8" fill="#FFFFFF" stroke="#A9A9A9" stroke-width="1.6"/>')
        yy = yy0 + 8
        for it in items:
            if it is None:
                o.append(f'<line x1="{px+12}" y1="{yy+7}" x2="{px+pw-12}" y2="{yy+7}" stroke="#D0D0D0" stroke-width="1.5"/>')
                yy += 14
                continue
            label, key, op = it
            col = "#A8A8A8" if op == "-" else "#111"
            o.append(f'<text x="{px+PADX}" y="{yy+29}" font-size="22" font-family="{F}" fill="{col}">{escape(label)}</text>')
            if key:
                o.append(f'<text x="{px+pw-PADX}" y="{yy+29}" font-size="20" font-family="{F}" fill="#777" text-anchor="end">{escape(key)}</text>')
            yy += ROW
        if adm:
            o.append(f'<text x="{px+6}" y="{yy0+h+32}" font-size="20" font-family="{F}" fill="#7A1F3A" font-style="italic">Отображается только для роли ADMIN</text>')
        if title == "Аналитика":
            o.append(f'<text x="{px+6}" y="{yy0+h+32}" font-size="20" font-family="{F}" fill="#777" font-style="italic">Вне реестра US-0 – US-17, недоступен</text>')
    y += TAB + rowh + GAPY
H = int(y - GAPY + 50)
o.insert(0, f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#fff"/>')
o.append("</svg>")
open("menu.svg", "w").write("\n".join(o))
print(W, H)
