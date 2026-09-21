# -*- coding: utf-8 -*-
"""Генератор чертежей кукольных шкафов из палитурного картона.

Все размеры в миллиметрах. Запуск:  python3 generator/build.py
Создаёт:  chertezhi.html  и  shablony-1-1.pdf  в корне репозитория.
"""
import os, math, re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm as MM
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cm(v):
    """мм -> строка в см с запятой: 154 -> '15,4', 60 -> '6', 1.5 -> '0,15'."""
    v = float(v) / 10
    t = f"{v:.2f}".rstrip("0").rstrip(".")
    return t.replace(".", ",")


# ---------------------------------------------------------------- размеры
T = 2      # картон стенок, мм
S = 3      # картон полок, мм
W_IN = 150            # ширина в свету (между боками)
W = W_IN + 2 * T      # наружная ширина шкафа = 154
D_UP = 60             # глубина витрины (наружная, с задником)
D_LOW = 70            # глубина тумбы (наружная, с задником)
OVER = 3              # свес столешницы и карниза по бокам и спереди (сзади заподлицо)

# тумба (низ)
H_PLINTH = 10
H_LOW_SIDE = 95       # высота бока тумбы
H_TOP = S             # столешница 3 мм
DRAWER_SUP_Y = 66     # низ опорной полки ящика (от пола)
# витрина (верх), отсчёт от низа бока витрины (стоит на столешнице)
NICHE = 62            # ниша в свету
FLOOR_Y = NICHE       # дно витрины 62..65
SHELF3_Y = FLOOR_Y + S + 40       # 105..108
SHELF2_Y = SHELF3_Y + S + 40      # 148..151
TOPP_Y = SHELF2_Y + S + 56        # 207..209
H_UP_SIDE = TOPP_Y + T            # 209
H_CAP = S
H_TOTAL = H_LOW_SIDE + H_TOP + H_UP_SIDE + H_CAP   # 310
UP_BASE = H_LOW_SIDE + H_TOP      # 98 - низ витрины от пола

VALANCE_H = 15
DOOR_GAP = 2
DOOR_W = (W - DOOR_GAP) // 2      # 76
VDOOR_GAP = 1                          # зазор снизу к планке и сверху к карнизу
VDOOR_Y = FLOOR_Y + S + VDOOR_GAP      # 66 - низ дверцы от низа бока витрины
VDOOR_H = H_UP_SIDE - VDOOR_Y - VDOOR_GAP   # 142
FRAME_SIDE, FRAME_TOP, FRAME_BOT = 7, 14, 12
WIN_W = DOOR_W - 2 * FRAME_SIDE   # 58
WIN_H = VDOOR_H - FRAME_TOP - FRAME_BOT  # 116
GLASS_W, GLASS_H = WIN_W + 10, WIN_H + 10

LDOOR_H = H_LOW_SIDE - H_PLINTH - 1   # 84, зазор 1 мм под столешницей
FRONT_H = 26                      # фасад ящика
FRONT_YS = [H_PLINTH, H_PLINTH + FRONT_H + 2, H_PLINTH + 2 * (FRONT_H + 2)]  # 10, 38, 66; верх 92, до столешницы 3
GAP_SHELF = 74                    # полка между шкафами (у Карины: 22 x 74 x 30)
SHELF_BETWEEN_H = 22
SHELF_TOP_Y = UP_BASE + FLOOR_Y + S   # 163 - верх полки между шкафами
TOTAL_W = 2 * W + GAP_SHELF       # 382
DOLL_H = 280

assert H_TOTAL == 310, H_TOTAL

# ---------------------------------------------------------------- список деталей
# (код, название, ширина, высота, толщина, кол-во на 2 шкафа, примечание, форма)
PARTS = [
    # витрина
    ("В1", "Бок витрины", D_UP - T, H_UP_SIDE, T, 4, "разметить полки: 6,2/6,5; 10,5/10,8; 14,8/15,1; 20,7 см", "side_up"),
    ("В2", "Задняя стенка витрины", W, H_UP_SIDE, T, 2, "клеится на торцы боков и полок сзади", "rect"),
    ("В3", "Верхняя панель", W_IN, D_UP - T, T, 2, "между боками, заподлицо с верхом", "rect"),
    ("В4", "Дно витрины (пол над нишей)", W_IN, D_UP - T, S, 2, "картон 3 мм, между боками", "rect"),
    ("В5", "Полка витрины", W_IN - 1, D_UP - T - 1, S, 4, "картон 3 мм, на 0,1 см уже для лёгкой посадки", "rect"),
    ("В6", "Крышка-карниз", W + 2 * OVER, D_UP + OVER, S, 2, "картон 3 мм, сзади заподлицо, свес 0,3 см", "rect"),
    ("В7", "Планка под витриной", W, VALANCE_H, T, 2, "волнистый низ, 0,3 см закрывает торец дна", "valance"),
    ("В8", "Рамка дверцы витрины", DOOR_W, VDOOR_H, T, 4, f"окно {cm(WIN_W)}×{cm(WIN_H)} см, поля {cm(FRAME_SIDE)}/{cm(FRAME_TOP)}/{cm(FRAME_BOT)} см", "vdoor"),
    ("В9", "«Стекло» дверцы", GLASS_W, GLASS_H, 0, 4, "прозрачный пластик, клеится с изнанки рамки", "rect"),
    # тумба общая
    ("Т1", "Бок тумбы", D_LOW - T, H_LOW_SIDE, T, 4, "разметка: дно 1/1,2 см; в правом шкафу опора 6,6/6,9 см", "side_low"),
    ("Т2", "Задняя стенка тумбы", W, H_LOW_SIDE, T, 2, "на торцы сзади", "rect"),
    ("Т3", "Дно тумбы", W_IN, D_LOW - T, T, 2, "между боками, низ на 1 см от пола", "rect"),
    ("Т4", "Цокольная планка", W_IN, H_PLINTH, T, 2, "под дном, утоплена на 0,4 см от фасада", "rect"),
    ("Т5", "Столешница", W + 2 * OVER, D_LOW + OVER, S, 2, "картон 3 мм, сзади заподлицо, свес 0,3 см", "rect"),
    # левый низ
    ("Л1", "Дверца тумбы (левый шкаф)", DOOR_W, LDOOR_H, T, 2, "накладная, от цоколя до столешницы", "rect"),
    ("Л2", "Филёнка на дверцу", 56, 65, T, 2, "фигурная накладка, по желанию", "panel"),
    # правый низ
    ("П1", "Опора ящика (правый шкаф)", W_IN, D_LOW - T, S, 1, "картон 3 мм, верх на 6,9 см от пола", "rect"),
    ("П2", "Заглушка под ложные фасады", W_IN, DRAWER_SUP_Y - (H_PLINTH + T), T, 1, "вертикально, заподлицо с передними торцами боков", "rect"),
    ("П3", "Фасад ящика", W, FRONT_H, T, 3, "накладной; верхний клеится на ящик", "rect"),
    ("П4", "Дно ящика", W_IN - 3, 60, T, 1, "зазор 0,15 см с каждой стороны", "rect"),
    ("П5", "Бок ящика", 60, 20, T, 2, "стоит на дне ящика", "rect"),
    ("П6", "Передняя и задняя стенка ящика", W_IN - 3 - 2 * T, 20, T, 2, "между боками ящика", "rect"),
]

# ---------------------------------------------------------------- SVG helpers
def unit(label):
    """Числовую подпись размера (в мм) переводит в см и добавляет «см»."""
    m = re.fullmatch(r"(.*?)(\d+(?:[.,]\d+)?)", label)
    if not m:
        return label
    return m.group(1) + cm(m.group(2).replace(",", ".")) + " см"

class Svg:
    """Чертёж в мм; y считается от пола (вверх), пересчёт в SVG внутри."""
    def __init__(self, w, h, pad=(30, 30, 30, 30), scale=1.0):
        self.w, self.h = w, h
        self.pl, self.pt, self.pr, self.pb = pad
        self.scale = scale
        self.el = []
    def X(self, x): return self.pl + x
    def Y(self, y): return self.pt + (self.h - y)
    def rect(self, x, y, w, h, cls="part", extra=""):
        self.el.append(f'<rect class="{cls}" x="{self.X(x):.1f}" y="{self.Y(y+h):.1f}" width="{w:.1f}" height="{h:.1f}" {extra}/>')
    def line(self, x1, y1, x2, y2, cls="thin"):
        self.el.append(f'<line class="{cls}" x1="{self.X(x1):.1f}" y1="{self.Y(y1):.1f}" x2="{self.X(x2):.1f}" y2="{self.Y(y2):.1f}"/>')
    def path(self, d, cls="part"):
        self.el.append(f'<path class="{cls}" d="{d}"/>')
    def text(self, x, y, s, cls="lbl", anchor="middle", rot=0):
        tr = f' transform="rotate({rot} {self.X(x):.1f} {self.Y(y):.1f})"' if rot else ""
        self.el.append(f'<text class="{cls}" x="{self.X(x):.1f}" y="{self.Y(y):.1f}" text-anchor="{anchor}"{tr}>{s}</text>')
    def dim_h(self, x1, x2, y, label=None, ext=None):
        """горизонтальный размер на высоте y; ext=(y_from) выносные линии"""
        label = label if label is not None else f"{abs(x2-x1):g}"
        if ext is not None:
            for x in (x1, x2):
                self.line(x, ext, x, y + (2 if y > ext else -2), "ext")
        self.el.append(f'<line class="dim" x1="{self.X(x1):.1f}" y1="{self.Y(y):.1f}" x2="{self.X(x2):.1f}" y2="{self.Y(y):.1f}" marker-start="url(#a)" marker-end="url(#a)"/>')
        self.text((x1 + x2) / 2, y + 1.6, unit(label), "dimt")
    def dim_v(self, x, y1, y2, label=None, ext=None, side="left"):
        label = label if label is not None else f"{abs(y2-y1):g}"
        if ext is not None:
            for y in (y1, y2):
                self.line(ext, y, x + (-2 if x < ext else 2), y, "ext")
        self.el.append(f'<line class="dim" x1="{self.X(x):.1f}" y1="{self.Y(y1):.1f}" x2="{self.X(x):.1f}" y2="{self.Y(y2):.1f}" marker-start="url(#a)" marker-end="url(#a)"/>')
        ym = (y1 + y2) / 2
        if side == "left":
            self.text(x - 1.5, ym, unit(label), "dimt", rot=-90)
        else:
            self.text(x + 4.2, ym, unit(label), "dimt", rot=-90)
    def render(self, title=""):
        vw = self.pl + self.w + self.pr
        vh = self.pt + self.h + self.pb
        return (f'<svg class="dwg" viewBox="0 0 {vw:.0f} {vh:.0f}" width="{vw*self.scale:.0f}" '
                f'role="img" aria-label="{title}"><defs><marker id="a" viewBox="0 0 6 6" refX="3" refY="3" '
                f'markerWidth="6" markerHeight="6" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
                f'<path d="M0,3 L6,0.6 L6,5.4 z" class="arr"/></marker></defs>' + "".join(self.el) + '</svg>')

def valance_path(svg, x, y, w, h):
    """Планка: прямая сверху, волнистый низ. y = низ планки."""
    X, Y = svg.X, svg.Y
    d = f"M{X(x):.1f},{Y(y+h):.1f} H{X(x+w):.1f} V{Y(y+4):.1f} "
    n = 6; seg = w / n
    for i in range(n):
        x1 = x + w - seg * (i + 1)
        cx = x1 + seg / 2
        d += f"Q{X(cx):.1f},{Y(y - 3):.1f} {X(x1):.1f},{Y(y+4):.1f} "
    d += "Z"
    return d

def door_cabinet_front(svg, x0, right=False):
    """Фасад одного шкафа. x0 - левый край. right=True: ящики вместо дверок."""
    y_low = 0
    # тумба
    svg.rect(x0 + T + 4, 0, W_IN - 8, H_PLINTH, "part")             # цоколь (утоплен)
    svg.rect(x0, 0, T, H_LOW_SIDE, "cut"); svg.rect(x0 + W - T, 0, T, H_LOW_SIDE, "cut")
    svg.rect(x0 - OVER, H_LOW_SIDE, W + 2 * OVER, H_TOP, "cut")     # столешница
    if not right:
        for dx in (0, DOOR_W + DOOR_GAP):
            svg.rect(x0 + dx, H_PLINTH, DOOR_W, LDOOR_H, "door")
            px = x0 + dx + (DOOR_W - 56) / 2
            svg.rect(px, H_PLINTH + (LDOOR_H - 65) / 2, 56, 65, "panel")
        # замочные скважины
        for dx in (DOOR_W - 6, DOOR_W + DOOR_GAP + 6):
            svg.el.append(f'<circle class="hw" cx="{svg.X(x0+dx):.1f}" cy="{svg.Y(H_PLINTH+LDOOR_H*0.55):.1f}" r="1.4"/>')
    else:
        for y in FRONT_YS:
            svg.rect(x0, y, W, FRONT_H, "door")
            for hx in (39, 115):   # центры ручек
                svg.rect(x0 + hx - 21, y + 8, 42, 9, "hw")
    # витрина
    ub = UP_BASE
    svg.rect(x0, ub, T, H_UP_SIDE, "cut"); svg.rect(x0 + W - T, ub, T, H_UP_SIDE, "cut")
    svg.rect(x0 + T, ub + FLOOR_Y, W_IN, S, "cut")                  # дно витрины
    svg.rect(x0 + T, ub + SHELF3_Y, W_IN, S, "shelf")
    svg.rect(x0 + T, ub + SHELF2_Y, W_IN, S, "shelf")
    svg.rect(x0 + T, ub + TOPP_Y, W_IN, T, "cut")
    svg.rect(x0 - OVER, ub + H_UP_SIDE, W + 2 * OVER, H_CAP, "cut")  # карниз
    # дверцы витрины
    for dx in (0, DOOR_W + DOOR_GAP):
        dy = ub + VDOOR_Y
        svg.rect(x0 + dx, dy, DOOR_W, VDOOR_H, "door")
        svg.rect(x0 + dx + FRAME_SIDE, dy + FRAME_BOT, WIN_W, WIN_H, "glass")
    # планка
    svg.path(valance_path(svg, x0, ub + FLOOR_Y + S - VALANCE_H, W, VALANCE_H), "door")
    # петли
    for dx in (x0 + 1, x0 + W - 1):
        for hy in (ub + VDOOR_Y + 15, ub + VDOOR_Y + VDOOR_H - 25):
            svg.rect(dx - 2, hy, 4, 10, "hw")
        if not right:
            for hy in (H_PLINTH + 10, H_PLINTH + LDOOR_H - 20):
                svg.rect(dx - 2, hy, 4, 10, "hw")

def front_view():
    s = Svg(TOTAL_W + 60, H_TOTAL + 40, pad=(40, 30, 60, 40), scale=2.2)
    s.line(-20, 0, TOTAL_W + 20, 0, "floor")
    # кукла для масштаба (силуэт)
    dx = W + GAP_SHELF / 2
    s.el.append(f'<path class="doll" d="M{s.X(dx):.1f},{s.Y(0):.1f} l-9,0 l3,-110 l-6,-30 l2,-95 l10,-25 l0,-20 l-9,-5 a9,9 0 1 1 18,0 l-9,5 l0,20 l10,25 l2,95 l-6,30 l3,110 z"/>')
    door_cabinet_front(s, 0)
    door_cabinet_front(s, W + GAP_SHELF, right=True)
    # полка между шкафами
    s.rect(W, SHELF_TOP_Y - SHELF_BETWEEN_H, GAP_SHELF, SHELF_BETWEEN_H, "part")
    s.text(W + GAP_SHELF / 2, SHELF_TOP_Y - 15, "полка 2,2×7,4×3 см", "lbl")
    # размеры
    s.dim_h(0, W, H_TOTAL + 12, ext=H_TOTAL)
    s.dim_h(W, W + GAP_SHELF, H_TOTAL + 12, ext=H_TOTAL)
    s.dim_h(W + GAP_SHELF, TOTAL_W, H_TOTAL + 12, ext=H_TOTAL)
    s.dim_h(0, TOTAL_W, H_TOTAL + 26, ext=H_TOTAL + 14)
    s.dim_v(-18, 0, H_TOTAL, ext=-4)
    s.dim_v(-30, 0, DOLL_H, "кукла 280", ext=-20)
    s.dim_v(TOTAL_W + 18, 0, H_LOW_SIDE + H_TOP, "тумба 98", ext=TOTAL_W + 4, side="right")
    s.dim_v(TOTAL_W + 18, H_LOW_SIDE + H_TOP, H_TOTAL, "витрина 212", ext=TOTAL_W + 4, side="right")
    s.dim_v(TOTAL_W + 34, 0, SHELF_TOP_Y, "верх полки 163", ext=TOTAL_W + 20, side="right")
    s.text(W / 2, -18, "ЛЕВЫЙ ШКАФ — дверцы · размеры в см", "cap")
    s.text(W + GAP_SHELF + W / 2, -18, "ПРАВЫЙ ШКАФ — 3 ящика · размеры в см", "cap")
    return s.render("Фасад композиции")

def section_view(right=False):
    """Боковой разрез через середину шкафа. x = глубина от задника."""
    s = Svg(D_LOW + OVER + 10, H_TOTAL, pad=(90, 20, 70, 34), scale=2.4)
    s.line(-10, 0, D_LOW + 20, 0, "floor")
    # боковые стенки (за плоскостью разреза)
    s.rect(T, 0, D_LOW - T, H_LOW_SIDE, "behind")
    s.rect(T, UP_BASE, D_UP - T, H_UP_SIDE, "behind")
    # тумба
    s.rect(0, 0, T, H_LOW_SIDE, "cut")                              # задник
    s.rect(T, H_PLINTH, D_LOW - T, T, "cut")                        # дно
    s.rect(D_LOW - 4 - T, 0, T, H_PLINTH, "cut")                    # цоколь
    if right:
        s.rect(T, DRAWER_SUP_Y, D_LOW - T, S, "shelf")               # опора ящика
        s.rect(D_LOW - T, H_PLINTH + T, T, DRAWER_SUP_Y - H_PLINTH - T, "cut")  # заглушка
        s.rect(D_LOW - 60, DRAWER_SUP_Y + S, 60, T, "cut")            # дно ящика
        s.rect(D_LOW - 60, DRAWER_SUP_Y + S + T, T, 20, "cut")        # задняя стенка ящика
        s.rect(D_LOW - T, DRAWER_SUP_Y + S + T, T, 20, "cut")         # передняя стенка ящика
        for y in FRONT_YS:
            s.rect(D_LOW, y, T, FRONT_H, "door")
    else:
        s.rect(D_LOW, H_PLINTH, T, LDOOR_H, "door")
    s.rect(0, H_LOW_SIDE, D_LOW + OVER, H_TOP, "shelf")              # столешница
    # витрина
    s.rect(0, UP_BASE, T, H_UP_SIDE, "cut")
    s.rect(T, UP_BASE + FLOOR_Y, D_UP - T, S, "shelf")
    s.rect(T, UP_BASE + SHELF3_Y, D_UP - T - 1, S, "shelf")
    s.rect(T, UP_BASE + SHELF2_Y, D_UP - T - 1, S, "shelf")
    s.rect(T, UP_BASE + TOPP_Y, D_UP - T, T, "cut")
    s.rect(0, UP_BASE + H_UP_SIDE, D_UP + OVER, H_CAP, "shelf")       # карниз
    s.rect(D_UP, UP_BASE + FLOOR_Y + S - VALANCE_H, T, VALANCE_H, "door")
    s.rect(D_UP, UP_BASE + VDOOR_Y, T, VDOOR_H, "door")
    # размеры слева: в свету
    xl = -12
    s.dim_v(xl, 0, H_PLINTH, "10", ext=0)
    s.dim_v(xl, H_PLINTH + T, H_LOW_SIDE, "83", ext=0)
    s.dim_v(xl, UP_BASE, UP_BASE + FLOOR_Y, "ниша 62", ext=0)
    s.dim_v(xl, UP_BASE + FLOOR_Y + S, UP_BASE + SHELF3_Y, "40", ext=0)
    s.dim_v(xl, UP_BASE + SHELF3_Y + S, UP_BASE + SHELF2_Y, "40", ext=0)
    s.dim_v(xl, UP_BASE + SHELF2_Y + S, UP_BASE + TOPP_Y, "56", ext=0)
    xl2 = -40
    s.dim_v(xl2, 0, H_LOW_SIDE, "бок тумбы 95", ext=0)
    s.dim_v(xl2, UP_BASE, UP_BASE + H_UP_SIDE, "бок витрины 209", ext=0)
    s.dim_v(-66, 0, H_TOTAL, "310", ext=0)
    # справа: отметки от низа бока витрины
    xr = D_LOW + 22
    s.dim_v(xr, UP_BASE, UP_BASE + FLOOR_Y, "62", ext=D_LOW + 8, side="right")
    s.dim_v(xr, UP_BASE, UP_BASE + SHELF3_Y, "105", ext=D_LOW + 8, side="right")
    s.dim_v(xr + 14, UP_BASE, UP_BASE + SHELF2_Y, "148", ext=D_LOW + 8, side="right")
    s.dim_v(xr + 28, UP_BASE, UP_BASE + TOPP_Y, "207", ext=D_LOW + 8, side="right")
    if right:
        s.dim_v(xr, 0, DRAWER_SUP_Y, "66", ext=D_LOW + 8, side="right")
    s.dim_v(xr + 14, 0, H_PLINTH, "10", ext=D_LOW + 8, side="right")
    # глубины
    s.dim_h(0, D_LOW + OVER, -10, "столешница 73", ext=0)
    s.dim_h(0, D_UP + OVER, H_TOTAL + 8, "карниз 63", ext=H_TOTAL)
    s.dim_h(0, D_UP, UP_BASE + NICHE / 2, "60")
    s.dim_h(0, D_LOW, H_LOW_SIDE / 2, "70")
    s.text(D_LOW / 2, -22, "ПРАВЫЙ ШКАФ, разрез · см" if right else "ЛЕВЫЙ ШКАФ, разрез · см", "cap")
    return s.render("Боковой разрез")

def door_drawing():
    s = Svg(DOOR_W + 30, VDOOR_H + 30, pad=(30, 20, 40, 30), scale=2.6)
    s.rect(0, 0, DOOR_W, VDOOR_H, "door")
    s.rect(FRAME_SIDE, FRAME_BOT, WIN_W, WIN_H, "glass")
    # декоративная волна вверху окна
    s.path(f"M{s.X(FRAME_SIDE):.1f},{s.Y(FRAME_BOT+WIN_H-8):.1f} q{WIN_W/4:.1f},-9 {WIN_W/2:.1f},0 q{WIN_W/4:.1f},9 {WIN_W/2:.1f},0", "thin")
    s.rect(-8, 15, 4, 10, "hw"); s.rect(-8, VDOOR_H - 25, 4, 10, "hw")
    s.dim_h(0, DOOR_W, VDOOR_H + 10, ext=VDOOR_H)
    s.dim_h(0, FRAME_SIDE, -8, ext=0); s.dim_h(FRAME_SIDE, FRAME_SIDE + WIN_W, -8, ext=0); s.dim_h(FRAME_SIDE + WIN_W, DOOR_W, -8, ext=0)
    s.dim_v(DOOR_W + 14, 0, VDOOR_H, ext=DOOR_W, side="right")
    s.dim_v(DOOR_W + 4, 0, FRAME_BOT, "12", ext=DOOR_W, side="right")
    s.dim_v(DOOR_W + 4, FRAME_BOT, FRAME_BOT + WIN_H, ext=DOOR_W, side="right")
    s.dim_v(DOOR_W + 4, FRAME_BOT + WIN_H, VDOOR_H, "14", ext=DOOR_W, side="right")
    s.text(-18, VDOOR_H / 2, "петли снаружи", "lbl", rot=-90)
    s.text(DOOR_W / 2, -18, "ДВЕРЦА ВИТРИНЫ · см", "cap")
    return s.render("Дверца витрины")

def drawer_drawing():
    """Ящик: вид спереди + сбоку с зазорами."""
    s = Svg(W + 100, 42, pad=(20, 14, 20, 22), scale=2.6)
    # проём
    s.rect(0, 0, T, 26, "cut"); s.rect(W - T, 0, T, 26, "cut"); s.rect(-OVER, 26, W + 2 * OVER, S, "shelf")
    s.rect(T, 0, W_IN, S, "shelf")                       # опора
    s.rect(T + 1.5, S, W_IN - 3, T, "cut")               # дно ящика
    s.rect(T + 1.5, S + T, T, 20, "cut"); s.rect(W - T - 1.5 - T, S + T, T, 20, "cut")
    s.rect(0, 0, W, FRONT_H, "doorline")                 # фасад (контур), низ на 66 = низ опоры
    s.dim_h(T, T + 1.5, 32, "1,5", ext=26); s.dim_h(W - T - 1.5, W - T, 32, "1,5", ext=26)
    s.dim_h(T + 1.5, W - T - 1.5, -7, "ящик 147", ext=0)
    s.dim_h(0, W, 38, "фасад 154", ext=32)
    s.dim_v(W + 8, S, S + T + 20, "коробка 22", ext=W, side="right")
    s.dim_v(W + 20, 0, FRONT_H, "фасад 26", ext=W, side="right")
    s.dim_v(W + 32, FRONT_H, 26 + S, "3", ext=W, side="right")
    s.text(W / 2, 12, "над фасадом 0,3 см до столешницы, над коробкой 0,4 см", "lbl")
    s.text(W / 2, -13, "ЯЩИК, вид спереди · см", "cap")
    return s.render("Ящик")

# ---------------------------------------------------------------- HTML
CSS = """
:root{--paper:#f6f3ec;--ink:#2b2622;--muted:#6f655b;--line:#3d3833;--cut:#8b5a2b;--cutfill:#d9b98f;
--shelf:#c99a63;--door:#eadfcd;--glass:#dbe6e3;--dim:#1f5f8b;--acc:#8b3a2f;--rule:#d8d0c2;--card:#fffdf8;--hw:#6a6a6a;--behind:#efe8db}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#1d1a17;--ink:#ece5da;--muted:#a79d90;--line:#d9d0c3;--cut:#c98f57;--cutfill:#6b4a2b;
--shelf:#a4783f;--door:#3a332b;--glass:#2c3d3b;--dim:#7cb8e0;--acc:#e0876f;--rule:#3a342e;--card:#26221e;--hw:#bbb;--behind:#2a2621}}
:root[data-theme="dark"]{--paper:#1d1a17;--ink:#ece5da;--muted:#a79d90;--line:#d9d0c3;--cut:#c98f57;--cutfill:#6b4a2b;
--shelf:#a4783f;--door:#3a332b;--glass:#2c3d3b;--dim:#7cb8e0;--acc:#e0876f;--rule:#3a342e;--card:#26221e;--hw:#bbb;--behind:#2a2621}
body{background:var(--paper);color:var(--ink);font-family:"Alegreya Sans",system-ui,sans-serif;font-size:17px;line-height:1.45;padding-block:24px 60px;padding-inline:16px}
main{max-width:1100px;margin:0 auto}
h1,h2,h3{font-family:"Alegreya",Georgia,serif;text-wrap:balance;line-height:1.15;margin:0}
h1{font-size:2.4rem;font-weight:600}
h2{font-size:1.6rem;margin-top:2.6rem;padding-top:1rem;border-top:2px solid var(--rule)}
h3{font-size:1.2rem;margin-top:1.4rem}
p{max-width:68ch;margin:.6rem 0}
.lead{color:var(--muted);font-size:1.05rem;max-width:70ch}
.eyebrow{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);font-weight:600}
.keys{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:1.4rem 0}
.key{background:var(--card);border:1px solid var(--rule);padding:12px 14px}
.key b{display:block;font-family:"JetBrains Mono",monospace;font-size:1.5rem;font-weight:500;font-variant-numeric:tabular-nums}
.key span{font-size:.85rem;color:var(--muted)}
figure{margin:1.2rem 0;overflow-x:auto;background:var(--card);border:1px solid var(--rule);padding:12px}
figcaption{font-size:.9rem;color:var(--muted);margin-top:6px}
svg.dwg{display:block;max-width:100%;height:auto;font-family:"JetBrains Mono",monospace}
.part{fill:none;stroke:var(--line);stroke-width:.5}
.cut{fill:var(--cutfill);stroke:var(--cut);stroke-width:.5}
.shelf{fill:var(--shelf);stroke:var(--cut);stroke-width:.5}
.door{fill:var(--door);stroke:var(--line);stroke-width:.6}
.doorline{fill:none;stroke:var(--line);stroke-width:.6;stroke-dasharray:2 1.5}
.panel{fill:none;stroke:var(--line);stroke-width:.5;rx:4}
.glass{fill:var(--glass);stroke:var(--line);stroke-width:.4}
.behind{fill:var(--behind);stroke:none}
.hw{fill:var(--hw);stroke:none}
.thin{fill:none;stroke:var(--line);stroke-width:.4}
.floor{stroke:var(--ink);stroke-width:1}
.doll{fill:none;stroke:var(--muted);stroke-width:.6;stroke-dasharray:2 1.5}
.dim{stroke:var(--dim);stroke-width:.45}
.ext{stroke:var(--dim);stroke-width:.3;stroke-dasharray:1.5 1}
.arr{fill:var(--dim)}
.dimt{fill:var(--dim);font-size:4.4px;paint-order:stroke;stroke:var(--card);stroke-width:1.6px;stroke-linejoin:round}
.lbl{fill:var(--muted);font-size:4.2px;paint-order:stroke;stroke:var(--card);stroke-width:1.4px}
.cap{fill:var(--ink);font-size:6px;font-family:"Alegreya Sans",sans-serif;font-weight:600;letter-spacing:.06em}
table{border-collapse:collapse;width:100%;font-size:.95rem}
.tbl{overflow-x:auto;background:var(--card);border:1px solid var(--rule)}
th,td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
td.n{font-family:"JetBrains Mono",monospace;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.grp td{background:var(--paper);font-family:"Alegreya",serif;font-size:1.05rem;font-weight:600;padding-top:12px}
.note{border-left:3px solid var(--acc);padding:6px 14px;background:var(--card);margin:1rem 0;max-width:72ch}
ol,ul{max-width:72ch;padding-left:1.3rem}li{margin:.35rem 0}
.check{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 20px;max-width:900px;font-size:.95rem}
.check div{padding:6px 0;border-bottom:1px dashed var(--rule)}
.check b{font-family:"JetBrains Mono",monospace;font-weight:500}
"""

def parts_table():
    rows = []
    groups = {"В": "Витрина (одинаково для обоих шкафов)", "Т": "Тумба, общие детали", "Л": "Левый шкаф, низ с дверцами", "П": "Правый шкаф, низ с ящиками"}
    seen = set()
    for code, name, w, h, t, n, note, shape in PARTS:
        g = code[0]
        if g not in seen:
            seen.add(g); rows.append(f'<tr class="grp"><td colspan="6">{groups[g]}</td></tr>')
        th = "пластик" if t == 0 else f"{cm(t)} см ({t} мм)"
        rows.append(f'<tr><td class="n">{code}</td><td>{name}</td><td class="n">{cm(w)} × {cm(h)} см</td><td class="n">{th}</td><td class="n">{n} шт</td><td>{note}</td></tr>')
    return ('<div class="tbl"><table><thead><tr><th>№</th><th>Деталь</th><th>Размер, см (ширина × высота)</th><th>Толщина</th><th>Всего</th><th>Примечание</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")

def build_html():
    fv, sl, sr, dd, dr = front_view(), section_view(False), section_view(True), door_drawing(), drawer_drawing()
    html = f"""<title>Сервант для Спектры</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:wght@500;600&family=Alegreya+Sans:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<main>
<div class="eyebrow">Палитурный картон 2 мм · полки 3 мм · размеры в см · под куклу 28 см</div>
<h1>Два шкафа-серванта из картона</h1>
<p class="lead"><b>Все размеры на чертежах и в таблице в сантиметрах</b>, как в твоих замерах. Толщина картона по привычке указана в мм (2 мм = 0,2 см).</p>
<p class="lead">Все размеры уже с учётом толщины картона и склейки «торец к плоскости». Обводить можно прямо по таблице деталей или распечатать PDF-шаблоны 1:1.</p>
<div class="keys">
<div class="key"><b>31</b><span>высота шкафа, см (кукла 28 + 3)</span></div>
<div class="key"><b>15,4</b><span>ширина шкафа, см</span></div>
<div class="key"><b>6 / 7</b><span>глубина витрины / тумбы, см</span></div>
<div class="key"><b>38,2</b><span>ширина композиции по корпусам, см (38,8 по карнизам)</span></div>
<div class="key"><b>15</b><span>внутри между боками, см</span></div>
</div>

<h2>Фасад</h2>
<figure>{fv}<figcaption>Вид спереди. Столешница и карниз выступают на 0,3 см по бокам и спереди, сзади заподлицо с задником. Полка между шкафами (готовая, 2,2×7,4×3 см) клеится к бокам на высоте 16,3 см от пола по верхней грани, вровень с полом витрины.</figcaption></figure>

<h2>Разрезы</h2>
<figure style="display:flex;gap:24px;flex-wrap:wrap;justify-content:center">{sl}{sr}<figcaption style="flex-basis:100%">Разрез через середину. Слева — размеры в свету, справа — отметки, которые переносятся на бока карандашом (низ соответствующей полки, от нижнего края бока). Задняя стенка клеится на торцы сзади, поэтому глубина боков на 0,2 см меньше наружной.</figcaption></figure>

<h2>Дверца витрины и ящик</h2>
<figure style="display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start">{dd}{dr}<figcaption style="flex-basis:100%">Дверца витрины: рамка из картона 2 мм, «стекло» из прозрачного пластика 7,2×12,6 см приклеивается с изнанки. Сверху и снизу дверцы зазор 0,1 см, чтобы не тёрлась о карниз и планку. Волна в верху окна вырезается по желанию. Ящик правого шкафа: выдвигается только верхний, два нижних фасада ложные и клеятся на заглушку П2.</figcaption></figure>

<h2>Карта деталей</h2>
<p>Все размеры в сантиметрах. Количество указано сразу на оба шкафа. Ширина везде первая, высота (или глубина для горизонтальных панелей) вторая. Ориентация «ширина × глубина» у полок: 15 — поперёк шкафа, 5,8 — от фасада к заднику.</p>
{parts_table()}

<h2>Отступы на клей: не нужны</h2>
<div class="note">
<p>Ты клеишь торец одной детали к плоскости другой, поэтому никаких клапанов и припусков не требуется. Вместо припусков в размерах уже учтена толщина картона: например, верхняя панель витрины 15 см, а не 15,4, потому что она встаёт между боками толщиной по 0,2 см.</p>
<p>Термоклей сам добавляет 0,3–0,5 мм, если не прижать. Поэтому: тонкая полоска клея, сразу сильно прижать, лишнее срезать лезвием. Внутренние полки В5 специально на 0,1 см уже боков, чтобы входить без распора. У ящика зазоры 0,15 см по бокам и 0,3–0,4 см сверху заложены под наклейку и клей.</p>
</div>

<h2>Порядок сборки</h2>
<ol>
<li><b>Разметка боков.</b> На всех боках витрины В1 проведи линии на 6,2; 6,5; 10,5; 10,8; 14,8; 15,1 и 20,7 см от нижнего края: это низ и верх дна витрины, полок и низ верхней панели. На боках тумбы Т1 отметь 1 и 1,2 см, а на двух боках правого шкафа ещё 6,6 и 6,9 см.</li>
<li><b>Витрина.</b> Приклей к одному боку дно В4, полки В5 и верхнюю панель В3 по отметкам, затем накрой вторым боком. Пока клей горячий, выровняй по угольнику. Сзади приклей задник В2 на все торцы, он выправит коробку. Сверху карниз В6 заподлицо по заднику, свес 0,3 см спереди и по бокам.</li>
<li><b>Тумба.</b> Дно Т3 между боками на 1 см от низа, под ним цокольная планка Т4, утопленная на 0,4 см от передних торцов. В правом шкафу добавь опору ящика П1 (верх на 6,9 см) и заглушку П2 вертикально под ней, заподлицо с передними торцами. Задник Т2, потом столешница Т5 сверху с тем же свесом.</li>
<li><b>Оклейка.</b> Наклейку с текстурой дерева удобно клеить на собранные коробки: одной полосой по боку с заворотом на передний торец, отдельно на карниз и столешницу. Дверцы, фасады и планку оклеивай до установки петель и ручек.</li>
<li><b>Планка и дверцы.</b> Планка В7 клеится на передние торцы так, чтобы её верх был вровень с верхом дна витрины (закрывает торец 0,3 см и висит в нишу на 1,2 см). Планку клей по всей длине к торцу дна витрины и к торцам боков. Дверцы витрины В8 накладные: закрытые лежат на передних торцах боков, низ на 0,1 см выше планки, верх на 0,1 см ниже карниза. Петли снаружи: одно крыло на бок, второе на дверцу, по две на дверцу; каждая петля занимает участок 1,5–2,5 см от верхнего и от нижнего края дверцы. Дверцы тумбы Л1 так же, от цоколя до столешницы с зазором 0,1 см сверху. Если дверцы не держатся закрытыми, добавь крошечный магнит или бусину-защёлку изнутри.</li>
<li><b>Ящик.</b> Дно П4, на нём бока П5, между ними стенки П6. Проверь ход в проёме, потом приклей фасад П3 так, чтобы он перекрывал коробку ящика на 0,35 см по бокам, 0,3 см снизу и 0,1 см сверху; между фасадом и столешницей остаётся 0,3 см. Ложные фасады: средний на 3,8–6,4 см от пола, нижний на 1–3,6 см, зазоры 0,2 см. В щели над средним фасадом виден торец опоры П1, его стоит закрасить. Ручки по две на фасад, центры на 3,9 и 11,5 см от левого края.</li>
<li><b>Стыковка.</b> Витрину ставь на столешницу вровень по заднику и приклей по нижним торцам боков и дна ниши; спереди столешница выступит на 1,3 см и получится полка ниши для лампы и телефона. Между шкафами полка 7,4 см на высоте 16,3 см по верху.</li>
</ol>

<h2>Проверка по декору (см)</h2>
<div class="check">
<div>Верхняя полка витрины в свету <b>5,6</b> · чайник 4,1, кукла 3,4 ✓</div>
<div>Средняя и нижняя полки в свету <b>4</b> · стопка книг 2,8, часы 1,8 ✓</div>
<div>Ширина за стеклом <b>15</b> · кукла + чайник + тарелки 11,3 ✓ (окна 2×6,2, стойки рамок 0,7 см частично прикрывают крайние предметы, как на фото оригинала)</div>
<div>Ниша под планкой спереди <b>5</b>, в глубине <b>6,2</b> · лампа 4,6 + салфетка 0,1 ✓ (у самой кромки запас 0,3 см, глубже свободно)</div>
<div>Глубина полок <b>5,7</b> · тарелки 3, полка между шкафами 3 ✓</div>
<div>Фасад ящика <b>15,4 × 2,6</b> · две ручки 4,2 × 0,9 ✓</div>
<div>Ниша правого шкафа · сундук 2,5 × 3,4 × 2,4 ✓</div>
<div>Задник комнаты · рекомендуемая высота <b>33–35</b> (кукла + 5…7)</div>
</div>
</main>
"""
    with open(os.path.join(ROOT, "chertezhi.html"), "w", encoding="utf-8") as f:
        f.write(html)

# ---------------------------------------------------------------- PDF 1:1
def find_font():
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(p):
            return p
    return None

def build_pdf():
    path = os.path.join(ROOT, "shablony-1-1.pdf")
    fp = find_font()
    font = "Helvetica"
    if fp:
        pdfmetrics.registerFont(TTFont("Body", fp)); font = "Body"
    c = canvas.Canvas(path, pagesize=A4)
    PW, PH = A4
    margin = 10 * MM
    usable_w, usable_h = PW - 2 * margin, PH - 2 * margin - 14 * MM

    def header(page):
        c.setFont(font, 9)
        c.drawString(margin, PH - margin, f"Шаблоны 1:1 · сервант для Спектры · стр. {page} · размеры в см · печатать в масштабе 100% (не «по размеру страницы»)")
        # контрольная линейка 100 мм
        y = PH - margin - 5 * MM
        c.setLineWidth(0.6); c.line(margin, y, margin + 100 * MM, y)
        for i in range(0, 101, 10):
            c.line(margin + i * MM, y, margin + i * MM, y + 2.5 * MM)
        c.setFont(font, 7); c.drawString(margin + 101 * MM, y, "контрольная линейка 10 см")

    def draw_part(x, y, part):
        code, name, w, h, t, n, note, shape = part
        W_, H_ = w * MM, h * MM
        c.setLineWidth(0.7); c.setStrokeColorRGB(0, 0, 0); c.setFillColorRGB(1, 1, 1)
        if shape == "valance":
            p = c.beginPath(); p.moveTo(x, y + H_); p.lineTo(x + W_, y + H_); p.lineTo(x + W_, y + 4 * MM)
            n_ = 6; seg = W_ / n_
            for i in range(n_):
                x1 = x + W_ - seg * (i + 1); p.curveTo(x1 + seg * .75, y - 1.3 * MM, x1 + seg * .25, y - 1.3 * MM, x1, y + 4 * MM)
            p.close(); c.drawPath(p, stroke=1, fill=0)
        elif shape == "panel":
            c.roundRect(x, y, W_, H_, 6 * MM, stroke=1, fill=0)
            c.setLineWidth(0.3); c.roundRect(x + 4 * MM, y + 4 * MM, W_ - 8 * MM, H_ - 8 * MM, 4 * MM, stroke=1, fill=0)
        else:
            c.rect(x, y, W_, H_, stroke=1, fill=0)
        if shape == "vdoor":
            c.setLineWidth(0.7)
            c.rect(x + FRAME_SIDE * MM, y + FRAME_BOT * MM, WIN_W * MM, WIN_H * MM, stroke=1, fill=0)
            c.setFont(font, 7); c.drawCentredString(x + W_ / 2, y + H_ / 2, "вырезать окно")
        if shape in ("side_up", "side_low"):
            marks = [62, 65, 105, 108, 148, 151, 207] if shape == "side_up" else [10, 12, 66, 69]
            c.setLineWidth(0.3); c.setDash(2, 2)
            for m in marks:
                c.line(x, y + m * MM, x + W_, y + m * MM)
                c.setFont(font, 6); c.drawString(x + 1 * MM, y + m * MM + 0.6 * MM, cm(m) + " см")
            c.setDash()
            if shape == "side_low":
                c.setFont(font, 8); c.drawString(x + 12 * MM, y + 72 * MM, "6,6/6,9 — ТОЛЬКО 2 бока"); c.drawString(x + 12 * MM, y + 75.5 * MM, "правого шкафа")
            c.setFont(font, 6); c.drawString(x + W_ - 14 * MM, y + 1 * MM, "перед →")
        c.setFont(font, 8)
        label = f"{code} {name} · {cm(w)}×{cm(h)} см · {'пластик' if t==0 else str(t)+' мм картон'} · {n} шт"
        if W_ > H_ * 1.2 or H_ < 20 * MM:
            c.drawString(x + 2 * MM, y + H_ - 4 * MM if H_ > 8 * MM else y + H_ + 1 * MM, label)
        else:
            c.saveState(); c.translate(x + 5 * MM, y + 3 * MM); c.rotate(90); c.drawString(0, 0, label); c.restoreState()

    # раскладка: по полкам (rows), детали по убыванию высоты; при необходимости поворот
    items = []
    for p in PARTS:
        code, name, w, h, t, n, note, shape = p
        if shape in ("side_up", "side_low", "vdoor", "valance", "panel"):
            items.append((p, False))
        else:
            items.append((p, w > h and h * MM <= usable_w and w * MM > usable_h))  # поворот если не влезает
    def dims(it):
        p, rot = it; w, h = p[2], p[3]
        return (h, w) if rot else (w, h)
    items.sort(key=lambda it: -dims(it)[1])
    page = 1; header(page)
    cx, cy = margin, PH - margin - 14 * MM
    row_h = 0; gap = 6 * MM
    for it in items:
        p, rot = it
        w, h = dims(it)
        W_, H_ = w * MM + gap, h * MM + gap
        if cx + W_ > margin + usable_w + 0.1:
            cx = margin; cy -= row_h; row_h = 0
        if cy - H_ < margin:
            c.showPage(); page += 1; header(page)
            cx = margin; cy = PH - margin - 14 * MM; row_h = 0
        y0 = cy - h * MM - 4 * MM
        if rot:
            c.saveState(); c.translate(cx + w * MM, y0); c.rotate(90); draw_part(0, 0, p); c.restoreState()
            c.setFont(font, 7); c.drawString(cx, y0 - 3 * MM, "(повернуто на 90°)")
        else:
            draw_part(cx, y0, p)
        cx += W_; row_h = max(row_h, H_)
    c.showPage(); c.save()

if __name__ == "__main__":
    build_html(); build_pdf()
    print("ok", H_TOTAL, W, TOTAL_W)
