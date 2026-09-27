# -*- coding: utf-8 -*-
"""Пошаговая визуальная инструкция по сборке серванта.

Запуск: python3 generator/instrukciya.py  ->  sborka.html в корне репозитория.
Все размеры берутся из generator/build.py (в мм), подписи в см.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B
from build import cm

ROOT = B.ROOT
W, T, S = B.W, B.T, B.S
C, SN = 0.866, 0.5

# ---------------------------------------------------------------- изометрия
def P(x, y, z):
    return ((x - y) * C, (x + y) * SN - z)

def part(b, k="done", off=(0, 0, 0), tag=None, name=None, win=None, glue_to=None, ghost=True):
    return dict(b=b, k=k, off=off, tag=tag, name=name, win=win, glue_to=glue_to, ghost=ghost)

def shift(parts, dx=0, dy=0, dz=0, **over):
    out = []
    for p in parts:
        x0, x1, y0, y1, z0, z1 = p["b"]
        q = dict(p, b=(x0 + dx, x1 + dx, y0 + dy, y1 + dy, z0 + dz, z1 + dz))
        q.update(over)
        out.append(q)
    return out

def scene(parts, rot=False, sid="s"):
    def tr(b):
        if not rot:
            return b
        x0, x1, y0, y1, z0, z1 = b
        return (-x1, -x0, -y1, -y0, z0, z1)
    def tro(o):
        return o if not rot else (-o[0], -o[1], o[2])
    items = []
    for i, p in enumerate(parts):
        fb = tr(p["b"]); o = tro(p["off"])
        db = (fb[0] + o[0], fb[1] + o[0], fb[2] + o[1], fb[3] + o[1], fb[4] + o[2], fb[5] + o[2])
        items.append(dict(p, fb=fb, db=db, o=o, i=i))
    # --- зоны клея
    glue = {it["i"]: [] for it in items}
    def rect(axis, v, r1, r2):
        (a0, a1), (b0, b1) = r1, r2
        if axis == 0:
            return [(v, a0, b0), (v, a1, b0), (v, a1, b1), (v, a0, b1)]
        if axis == 1:
            return [(a0, v, b0), (a1, v, b0), (a1, v, b1), (a0, v, b1)]
        return [(a0, b0, v), (a1, b0, v), (a1, b1, v), (a0, b1, v)]
    for n in items:
        if n["k"] != "new" or n["glue_to"] == []:
            continue
        for a in items:
            if a["k"] == "new" or (n["glue_to"] is not None and a["name"] not in n["glue_to"]):
                continue
            for ax in range(3):
                others = [o for o in range(3) if o != ax]
                ov = []
                for o in others:
                    lo = max(a["fb"][2 * o], n["fb"][2 * o]); hi = min(a["fb"][2 * o + 1], n["fb"][2 * o + 1])
                    ov.append((lo, hi))
                if any(hi - lo < 0.3 for lo, hi in ov):
                    continue
                if abs(a["fb"][2 * ax + 1] - n["fb"][2 * ax]) < 0.01:      # видимая грань A
                    glue[a["i"]].append(rect(ax, a["fb"][2 * ax + 1], ov[0], ov[1]))
                elif abs(a["fb"][2 * ax] - n["fb"][2 * ax + 1]) < 0.01:    # видимая грань новой детали
                    o = n["o"]
                    pts = rect(ax, n["fb"][2 * ax + 1], ov[0], ov[1])
                    glue[n["i"]].append([(x + o[0], y + o[1], z + o[2]) for x, y, z in pts])
    # --- порядок отрисовки
    def behind(a, b):
        e = 0.01
        return a["db"][1] <= b["db"][0] + e or a["db"][3] <= b["db"][2] + e or a["db"][5] <= b["db"][4] + e
    order, rest = [], items[:]
    while rest:
        pick = None
        for x in rest:
            if not any(y is not x and behind(y, x) and not behind(x, y) for y in rest):
                pick = x; break
        if pick is None:
            pick = min(rest, key=lambda it: it["db"][0] + it["db"][2] + it["db"][4])
        order.append(pick); rest.remove(pick)
    # --- рамка
    pts = []
    for it in items:
        for bb in (it["db"], it["fb"]):
            pts += [P(x, y, z) for x in bb[:2] for y in bb[2:4] for z in bb[4:6]]
    minx = min(p[0] for p in pts) - 8; maxx = max(p[0] for p in pts) + 8
    miny = min(p[1] for p in pts) - 8; maxy = max(p[1] for p in pts) + 8
    vw, vh = maxx - minx, maxy - miny
    fs = max(vw, vh) / 26
    def pp(pt3):
        x, y = P(*pt3); return f"{x - minx:.1f},{y - miny:.1f}"
    def poly(p3, cls):
        return f'<polygon class="{cls}" points="{" ".join(pp(q) for q in p3)}"/>'
    def faces(bb):
        x0, x1, y0, y1, z0, z1 = bb
        return ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
                [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])
    el = []
    for it in order:
        t, f, r = faces(it["db"])
        k = it["k"]
        el += [poly(t, f"k-{k}-t"), poly(f, f"k-{k}-f"), poly(r, f"k-{k}-r")]
        if it["win"] and not rot:
            mx, mb, mt = it["win"]; x0, x1, y0, y1, z0, z1 = it["db"]
            el.append(poly([(x0 + mx, y1, z0 + mb), (x1 - mx, y1, z0 + mb), (x1 - mx, y1, z1 - mt), (x0 + mx, y1, z1 - mt)], "k-glass"))
        for g in glue[it["i"]]:
            el.append(poly(g, "glue"))
    # --- призрак и стрелки
    for it in items:
        if it["k"] != "new" or it["o"] == (0, 0, 0):
            continue
        if it["ghost"]:
            t, f, r = faces(it["fb"])
            for fc in (t, f, r):
                el.append(f'<polygon class="ghost" points="{" ".join(pp(q) for q in fc)}"/>')
            x0, x1, y0, y1, z0, z1 = it["fb"]; o = it["o"]
            for (x, y, z) in [(x0, y1, z1), (x1, y1, z0)]:
                a = P(x + o[0], y + o[1], z + o[2]); b = P(x, y, z)
                el.append(f'<line class="drop" x1="{a[0]-minx:.1f}" y1="{a[1]-miny:.1f}" x2="{b[0]-minx:.1f}" y2="{b[1]-miny:.1f}" marker-end="url(#m{sid})"/>')
    # --- подписи
    few = len(items) <= 7
    for it in items:
        if not it["tag"] or (it["k"] != "new" and not few):
            continue
        x0, x1, y0, y1, z0, z1 = it["db"]
        cx, cy = P((x0 + x1) / 2, y1, (z0 + z1) / 2)
        if (x1 - x0) < 8 and (z1 - z0) > 20:  # тонкий бок — подпись по центру правой грани
            cx, cy = P(x1, (y0 + y1) / 2, (z0 + z1) / 2)
        cls = "tag-new" if it["k"] == "new" else "tag"
        el.append(f'<text class="{cls}" x="{cx - minx:.1f}" y="{cy - miny + fs * .35:.1f}" style="font-size:{fs:.1f}px" text-anchor="middle">{it["tag"]}</text>')
    ms = fs * 0.55
    return (f'<svg class="iso" viewBox="0 0 {vw:.0f} {vh:.0f}" role="img">'
            f'<defs><marker id="m{sid}" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="{ms:.1f}" markerHeight="{ms:.1f}" '
            f'markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L6,3 L0,6 z" class="arrowhead"/></marker></defs>'
            + "".join(el) + "</svg>")

# ---------------------------------------------------------------- детали в координатах
DU, DL, HS, HL = B.D_UP, B.D_LOW, B.H_UP_SIDE, B.H_LOW_SIDE
O = B.OVER

def vit(k="done"):
    """Витрина, z от низа бока. Словарь код -> деталь."""
    d = {}
    d["В1л"] = part((0, T, T, DU, 0, HS), k, tag="В1", name="В1л")
    d["В4"] = part((T, W - T, T, DU, B.FLOOR_Y, B.FLOOR_Y + S), k, tag="В4", name="В4")
    d["В5a"] = part((T + .5, W - T - .5, T, DU - 1, B.SHELF3_Y, B.SHELF3_Y + S), k, tag="В5", name="В5a")
    d["В5b"] = part((T + .5, W - T - .5, T, DU - 1, B.SHELF2_Y, B.SHELF2_Y + S), k, tag="В5", name="В5b")
    d["В3"] = part((T, W - T, T, DU, B.TOPP_Y, B.TOPP_Y + T), k, tag="В3", name="В3")
    d["В1п"] = part((W - T, W, T, DU, 0, HS), k, tag="В1", name="В1п")
    d["В2"] = part((0, W, 0, T, 0, HS), k, tag="В2", name="В2")
    d["В6"] = part((-O, W + O, 0, DU + O, HS, HS + S), k, tag="В6", name="В6")
    return d

def tum(k="done", right=False):
    d = {}
    d["Т1л"] = part((0, T, T, DL, 0, HL), k, tag="Т1", name="Т1л")
    d["Т3"] = part((T, W - T, T, DL, B.H_PLINTH, B.H_PLINTH + T), k, tag="Т3", name="Т3")
    d["Т1п"] = part((W - T, W, T, DL, 0, HL), k, tag="Т1", name="Т1п")
    d["Т4"] = part((T, W - T, DL - 4 - T, DL - 4, 0, B.H_PLINTH), k, tag="Т4", name="Т4")
    if right:
        d["П1"] = part((T, W - T, T, DL, B.DRAWER_SUP_Y, B.DRAWER_SUP_Y + S), k, tag="П1", name="П1")
        d["П2"] = part((T, W - T, DL - T, DL, B.H_PLINTH + T, B.DRAWER_SUP_Y), k, tag="П2", name="П2")
    d["Т2"] = part((0, W, 0, T, 0, HL), k, tag="Т2", name="Т2")
    d["Т5"] = part((-O, W + O, 0, DL + O, HL, HL + S), k, tag="Т5", name="Т5")
    return d

UB = B.UP_BASE
VD_Y0 = UB + B.VDOOR_Y
def vfronts(k="done"):
    d = {}
    d["В7"] = part((0, W, DU, DU + T, UB + B.FLOOR_Y + S - B.VALANCE_H, UB + B.FLOOR_Y + S), "dark" if k == "done" else k, tag="В7", name="В7")
    win = (B.FRAME_SIDE, B.FRAME_BOT, B.FRAME_TOP)
    d["В8л"] = part((0, B.DOOR_W, DU, DU + T, VD_Y0, VD_Y0 + B.VDOOR_H), "dark" if k == "done" else k, tag="В8", name="В8л", win=win, glue_to=[])
    d["В8п"] = part((W - B.DOOR_W, W, DU, DU + T, VD_Y0, VD_Y0 + B.VDOOR_H), "dark" if k == "done" else k, tag="В8", name="В8п", win=win, glue_to=[])
    hk = "metal" if k == "done" else k
    for side, x in (("л", -1.5), ("п", W)):
        for j, hz in enumerate((VD_Y0 + 15, VD_Y0 + B.VDOOR_H - 25)):
            d[f"hv{side}{j}"] = part((x, x + 1.5, DU - 6, DU + 1, hz, hz + 10), hk, name=f"hv{side}{j}", glue_to=[], ghost=False)
    return d

def ldoors(k="done"):
    d = {}
    z0 = B.H_PLINTH
    for nm, x in (("л", 0), ("п", W - B.DOOR_W)):
        d["Л1" + nm] = part((x, x + B.DOOR_W, DL, DL + T, z0, z0 + B.LDOOR_H), "dark" if k == "done" else k, tag="Л1", name="Л1" + nm, glue_to=[])
        px = x + (B.DOOR_W - B.PANEL_W) / 2; pz = z0 + (B.LDOOR_H - B.PANEL_H) / 2
        d["Л2" + nm] = part((px, px + B.PANEL_W, DL + T, DL + 2 * T, pz, pz + B.PANEL_H), "dark" if k == "done" else k, tag="Л2", name="Л2" + nm, glue_to=["Л1" + nm], ghost=False)
    hk = "metal" if k == "done" else k
    for side, x in (("л", -1.5), ("п", W)):
        for j, hz in enumerate((z0 + 10, z0 + B.LDOOR_H - 20)):
            d[f"hl{side}{j}"] = part((x, x + 1.5, DL - 6, DL + 1, hz, hz + 10), hk, name=f"hl{side}{j}", glue_to=[], ghost=False)
    return d

DW = B.W_IN - 3               # ширина коробки ящика
DD = B.DRAWER_D
def drawer_box(k="done", x0=T + 1.5, y0=DL - DD, z0=B.DRAWER_SUP_Y + S):
    d = {}
    d["П4"] = part((x0, x0 + DW, y0, y0 + DD, z0, z0 + T), k, tag="П4", name="П4")
    d["П5л"] = part((x0, x0 + T, y0, y0 + DD, z0 + T, z0 + T + 20), k, tag="П5", name="П5л")
    d["П6з"] = part((x0 + T, x0 + DW - T, y0, y0 + T, z0 + T, z0 + T + 20), k, tag="П6", name="П6з")
    d["П6п"] = part((x0 + T, x0 + DW - T, y0 + DD - T, y0 + DD, z0 + T, z0 + T + 20), k, tag="П6", name="П6п")
    d["П5п"] = part((x0 + DW - T, x0 + DW, y0, y0 + DD, z0 + T, z0 + T + 20), k, tag="П5", name="П5п")
    return d

def dfronts(k="done"):
    d = {}
    names = ["П3н", "П3с", "П3в"]
    for nm, y in zip(names, B.FRONT_YS):
        d[nm] = part((0, W, DL, DL + T, y, y + B.FRONT_H), "dark" if k == "done" else k, tag="П3", name=nm,
                     glue_to=(["П6п"] if nm == "П3в" else ["П2"]))
    return d

def handles(k="done"):
    d = {}
    for y in B.FRONT_YS:
        for cx in B.HANDLE_CX:
            d[f"h{y}{cx}"] = part((cx - 21, cx + 21, DL + T, DL + T + 1.5, y + 8, y + 17), "metal" if k == "done" else k, name=f"h{y}{cx}", glue_to=[], ghost=False)
    return d

def L(d, *keys, **over):
    out = []
    for k in keys:
        p = dict(d[k]); p.update(over); out.append(p)
    return out

def up(parts):  # витрина на свою высоту в полном шкафу
    return shift(parts, dz=UB)

# ---------------------------------------------------------------- шаги
steps = []
def step(group, title, parts_codes, svg, bullets, check=None, who=None):
    steps.append(dict(group=group, title=title, codes=parts_codes, svg=svg, bullets=bullets, check=check, who=who))

sid = iter(range(1000))
def S_(parts, rot=False):
    return scene(parts, rot=rot, sid=str(next(sid)))

# --- А. Витрина
v, vn = vit(), vit("new")
step("А. Витрина", "Бок и дно витрины", ["В1", "В4"],
     S_(L(v, "В1л") + L(vn, "В4", off=(45, 0, 0))),
     ["Положи бок В1 на стол разметкой вверх. На картинке шкаф стоит, но клеить удобнее лёжа.",
      f"Нанеси тонкую полоску клея на короткий торец дна В4 ({cm(DU - T)} см).",
      f"Приставь В4 к боку между линиями {cm(B.FLOOR_Y)} и {cm(B.FLOOR_Y + S)} см. Передний и задний края В4 ровно по краям бока.",
      "Прижми угольник и держи 15 секунд, пока клей не схватится."],
     check="В4 стоит под прямым углом к боку и не качается.")
step("А. Витрина", "Полки и верхняя панель", ["В5", "В3"],
     S_(L(v, "В1л", "В4") + L(vn, "В5a", "В5b", "В3", off=(45, 0, 0))),
     ["Так же, по одной, приклей две полки В5 и верхнюю панель В3.",
      f"Полки: между линиями {cm(B.SHELF3_Y)}–{cm(B.SHELF3_Y + S)} и {cm(B.SHELF2_Y)}–{cm(B.SHELF2_Y + S)} см. Задний край ровно по заднему краю бока, спереди полка будет на 0,1 см короче, так и задумано.",
      f"Верхняя панель В3: от линии {cm(B.TOPP_Y)} см до самого верха бока, верх в одну плоскость с торцом бока."],
     check="Все четыре детали параллельны, расстояния между ними одинаковые спереди и сзади.")
step("А. Витрина", "Второй бок", ["В1"],
     S_(L(v, "В1л", "В4", "В5a", "В5b", "В3") + L(vn, "В1п", off=(40, 0, 0))),
     ["Нанеси клей на свободные торцы всех четырёх деталей сразу. Работай быстро: клей стынет за 5–10 секунд. Можно по две детали за раз.",
      "Накрой вторым боком В1 разметкой внутрь. Линии разметки должны совпасть с деталями.",
      "Зелёным на картинке показаны торцы, куда нужен клей."],
     check="Коробка стоит ровно, углы прямые.")
step("А. Витрина", "Задняя стенка (вид сзади)", ["В2"],
     S_(L(v, "В1л", "В4", "В5a", "В5b", "В3", "В1п") + L(vn, "В2", off=(0, -45, 0)), rot=True),
     ["Положи коробку передом вниз. Нанеси клей на задние торцы боков, дна, полок и верха (зелёные полосы).",
      "Положи задник В2 сверху так, чтобы он совпал с краями коробки со всех сторон.",
      "Задник выравнивает коробку: если она была чуть перекошена, подвинь её до совпадения краёв, пока клей мягкий."],
     check="Диагонали коробки спереди равны, углы прямые.")
step("А. Витрина", "Крышка-карниз", ["В6"],
     S_(L(v, "В1л", "В4", "В5a", "В5b", "В3", "В1п", "В2") + L(vn, "В6", off=(0, 0, 45))),
     ["Нанеси клей на верх коробки: торцы боков и задника и верхнюю панель.",
      "Положи крышку В6 сверху. Сзади ровно по заднику, спереди и по бокам она выступает на 0,3 см.",
      "Совет: заранее проведи на нижней стороне В6 карандашом линии в 0,3 см от боков и переднего края. По ним легко выровнять."],
     check="Свес одинаковый слева и справа. Витрину повтори второй раз для второго шкафа.")

# --- Б. Тумба
t, tn = tum(), tum("new")
tr_, trn = tum(right=True), tum("new", right=True)
step("Б. Тумба", "Бок и дно тумбы", ["Т1", "Т3"],
     S_(L(t, "Т1л") + L(tn, "Т3", off=(45, 0, 0))),
     [f"Дно Т3 клеится между линиями {cm(B.H_PLINTH)} и {cm(B.H_PLINTH + T)} см на боку Т1, как дно витрины.",
      "Передний и задний края дна ровно по краям бока."],
     check="Под дном остаётся место 1 см для цоколя.")
step("Б. Тумба", "Второй бок", ["Т1"],
     S_(L(t, "Т1л", "Т3") + L(tn, "Т1п", off=(40, 0, 0))),
     ["Клей на свободный торец дна, накрой вторым боком разметкой внутрь."],
     check="Бока параллельны, коробка не заваливается.")
step("Б. Тумба", "Цоколь", ["Т4"],
     S_(L(t, "Т1л", "Т3", "Т1п") + L(tn, "Т4", off=(0, 40, 0))),
     ["Цокольная планка Т4 встаёт под дно, между боками.",
      "Она утоплена: её передняя сторона на 0,4 см глубже передних краёв боков. Так цоколь выглядит тенью, как у настоящей мебели.",
      "Клей на верхний торец и на оба коротких торца."],
     check="Тумба стоит на боках и цоколе без качания.")
step("Б. Тумба", "Опора ящика", ["П1"],
     S_(L(tr_, "Т1л", "Т3", "Т4", "Т1п") + L(trn, "П1", off=(0, 0, 45))),
     [f"Опора П1 из картона 3 мм клеится между боками по линиям {cm(B.DRAWER_SUP_Y)}–{cm(B.DRAWER_SUP_Y + S)} см.",
      "Края ровно по переднему и заднему краю боков. На ней будет ездить выдвижной ящик."],
     check="Опора горизонтальная, иначе ящик будет съезжать.", who="только правый шкаф")
step("Б. Тумба", "Заглушка под ложные ящики", ["П2"],
     S_(L(tr_, "Т1л", "Т3", "Т4", "Т1п", "П1") + L(trn, "П2", off=(0, 40, 0))),
     ["Заглушка П2 стоит вертикально спереди, между дном и опорой.",
      "Её лицевая сторона в одну плоскость с передними краями боков. На неё потом приклеятся два нижних фасада."],
     check="П2 не выступает вперёд и не утоплена.", who="только правый шкаф")
step("Б. Тумба", "Задняя стенка (вид сзади)", ["Т2"],
     S_(L(t, "Т1л", "Т3", "Т4", "Т1п") + L(tn, "Т2", off=(0, -40, 0)), rot=True),
     ["Как у витрины: коробку передом вниз, клей на задние торцы, задник Т2 сверху по краям."],
     check="Диагонали равны.")
step("Б. Тумба", "Столешница", ["Т5"],
     S_(L(t, "Т1л", "Т3", "Т4", "Т1п", "Т2") + L(tn, "Т5", off=(0, 0, 40))),
     ["Клей на верхние торцы боков и задника.",
      "Столешница Т5 сзади ровно по заднику, спереди и по бокам свес 0,3 см, как у крышки витрины."],
     check="Тумбу тоже сделай две: левую с дверцами и правую с опорой и заглушкой.")

# --- В. Соединение
full_t = L(t, "Т1л", "Т3", "Т4", "Т1п", "Т2", "Т5")
full_v = up(L(v, "В1л", "В4", "В5a", "В5b", "В3", "В1п", "В2", "В6"))
full_vn = [dict(p, k="new", off=(0, 0, 45), ghost=False, tag=None) for p in full_v]
full_vn[0]["tag"] = "витрина"
step("В. Соединение", "Витрина на тумбу", ["витрина", "тумба"],
     S_(full_t + full_vn),
     ["Клей на нижние торцы боков и задника витрины (зелёные полосы на столешнице показывают, куда они встанут).",
      "Поставь витрину на столешницу: сзади ровно по заднику тумбы, бока витрины точно над боками тумбы.",
      "Спереди столешница выступит на 1,3 см: это пол ниши, там будут лампа и телефон."],
     check="Если посмотреть сбоку, задняя стенка шкафа ровная, без ступеньки.")

# --- Г. Фасады
vf, vfn = vfronts(), vfronts("new")
body = full_t + full_v
step("Г. Фасады", "Планка над нишей", ["В7"],
     S_(body + L(vfn, "В7", off=(0, 40, 0))),
     ["Волнистая планка В7 клеится на передние торцы боков витрины и на передний торец её дна.",
      "Верх планки в одну линию с верхом дна витрины. Вниз она свисает в нишу на 1,2 см и прячет торец дна."],
     check="Планка горизонтальная и не выходит за бока.")
step("Г. Фасады", "Дверцы витрины на петлях", ["В8", "петли"],
     S_(body + L(vf, "В7") + L(vfn, "В8л", "В8п", off=(0, 35, 0)) + [dict(p, off=(0, 35, 0)) for k_, p in vfn.items() if k_.startswith("hv")]),
     ["До навешивания вклей в каждую рамку «стекло» из прозрачного пластика с изнанки, по краю окна тонкой линией клея.",
      "Дверцы накладные: закрытые, они лежат на передних торцах боков. Сверху зазор 0,1 см до крышки, снизу 0,1 см до планки, между дверцами 0,2 см.",
      "Петли снаружи, по две на дверцу: одно крыло на бок шкафа, второе на дверцу. Верхняя петля в 1,5–2,5 см от верха дверцы, нижняя так же от низа.",
      "Дверцы саму на шкаф не клей, только петли. Совет: вставь в зазоры полоски бумаги, пока клеишь петли, потом вынь."],
     check="Дверцы открываются и закрываются, не задевая крышку и планку.")
ld, ldn = ldoors(), ldoors("new")
step("Г. Фасады", "Дверцы тумбы", ["Л1", "Л2", "петли"],
     S_(body + L(vf, "В7", "В8л", "В8п") + L(ldn, "Л1л", "Л1п", "Л2л", "Л2п", off=(0, 35, 0)) + [dict(p, off=(0, 35, 0)) for k_, p in ldn.items() if k_.startswith("hl")]),
     ["Сначала приклей фигурные филёнки Л2 по центру дверец Л1, пока дверцы лежат на столе.",
      "Дверцы вешаются так же, на петлях снаружи: низ на уровне дна тумбы (1 см от пола), сверху зазор 0,1 см до столешницы."],
     check="Дверцы закрываются вровень друг с другом.", who="только левый шкаф")
dbx_n = drawer_box("new", x0=0, y0=0, z0=0)
dbx_done = drawer_box("done", x0=0, y0=0, z0=0)
step("Г. Фасады", "Собери ящик", ["П4", "П5", "П6"],
     S_(L(dbx_done, "П4") + L(dbx_n, "П5л", off=(-25, 0, 0)) + L(dbx_n, "П6з", off=(0, -25, 0)) + L(dbx_n, "П6п", off=(0, 25, 0)) + L(dbx_n, "П5п", off=(25, 0, 0))),
     ["Ящик собирается отдельно на столе. Дно П4 лежит, на него ставятся бока П5 по длинным краям.",
      "Между боками клеятся передняя и задняя стенки П6.",
      f"Готовая коробка {cm(DW)} × {cm(DD)} см, высота {cm(T + 20)} см."],
     check="Коробка свободно входит в проём над опорой, с зазором по бокам.", who="только правый шкаф")
rt = L(tr_, "Т1л", "Т3", "Т4", "Т1п", "П1", "П2", "Т2", "Т5") + full_v + L(vf, "В7", "В8л", "В8п")
db_in = list(drawer_box("done").values())
df, dfn = dfronts(), dfronts("new")
step("Г. Фасады", "Фасады ящиков", ["П3"],
     S_(rt + db_in + L(dfn, "П3н", "П3с", "П3в", off=(0, 35, 0))),
     ["Вставь ящик на опору, не приклеивая.",
      f"Верхний фасад П3 клеится только на переднюю стенку ящика: его низ на {cm(B.FRONT_YS[2])} см от пола, края вровень с боками шкафа. Между верхом фасада и столешницей остаётся 0,3 см.",
      f"Два нижних фасада ложные, клеятся на заглушку П2: средний на {cm(B.FRONT_YS[1])}–{cm(B.FRONT_YS[1] + B.FRONT_H)} см, нижний на {cm(B.FRONT_YS[0])}–{cm(B.FRONT_YS[0] + B.FRONT_H)} см от пола. Зазоры между фасадами 0,2 см.",
      "Совет: подложи под верхний фасад две монетки, пока клей не застынет, чтобы выдержать высоту."],
     check="Верхний ящик выдвигается и ничего не цепляет. Проверь до того, как клей остынет.", who="только правый шкаф")
hn = handles("new")
step("Г. Фасады", "Ручки", ["ручки"],
     S_(rt + db_in + list(df.values()) + [dict(p, off=(0, 20, 0)) for p in hn.values()]),
     [f"На каждый фасад по две ручки, центры на {cm(B.HANDLE_CX[0])} и {cm(B.HANDLE_CX[1])} см от левого края, по высоте посередине фасада.",
      "Капля клея на ручку, прижми пинцетом. Если тесно, ставь по одной ручке по центру."],
     check="Ручки на одной высоте на всех трёх фасадах.", who="только правый шкаф")

# --- Д. Финал
left_all = full_t + full_v + L(vf, "В7", "В8л", "В8п") + list(ld.values()) + [p for k_, p in vf.items() if k_.startswith("hv")]
right_all = rt + list(df.values()) + list(handles().values()) + [p for k_, p in vf.items() if k_.startswith("hv")]
gx = B.GAP_SHELF
shelf = part((W, W + gx, 0, 30, B.SHELF_TOP_Y - B.SHELF_BETWEEN_H, B.SHELF_TOP_Y), "new", tag="полка", name="shelf", glue_to=[], ghost=False)
final = [dict(p, tag=None) for p in left_all] + [dict(p, tag=None) for p in shift(right_all, dx=W + gx)] + [dict(shelf, off=(0, 0, 30))]
step("Д. Финал", "Расстановка и полка между шкафами", ["полка"],
     S_(final),
     [f"Поставь шкафы на расстоянии {cm(gx)} см друг от друга, задними стенками к заднику комнаты.",
      f"Полку клей к бокам витрин так, чтобы её верх был на {cm(B.SHELF_TOP_Y)} см от пола, вровень с полом витрин.",
      "В конце заклей видимые передние торцы боков и столешниц полосками текстуры шириной 3–4 мм и срежь лишнее ножом."],
     check="Кукла по центру, полка ровная, всё стоит устойчиво.")

# ---------------------------------------------------------------- разметка боков (2D)
def side_marks(title, h, d, bands):
    """bands: (низ, верх, код детали, только_правый)"""
    pad_l, pad_r, pad_t, pad_b = 34, 62, 18, 22
    vw, vh = d + pad_l + pad_r, h + pad_t + pad_b
    el = [f'<rect class="k-done-f" x="{pad_l}" y="{pad_t}" width="{d}" height="{h}"/>']
    for z0, z1, code, red in bands:
        y0, y1 = pad_t + h - z1, pad_t + h - z0
        cls = "-r" if red else ""
        el.append(f'<rect class="band{cls}" x="{pad_l}" y="{y0:.1f}" width="{d}" height="{max(y1 - y0, 1.2):.1f}"/>')
        el.append(f'<line class="mark{cls}" x1="{pad_l}" y1="{y0:.1f}" x2="{pad_l + d}" y2="{y0:.1f}"/>')
        el.append(f'<line class="mark{cls}" x1="{pad_l}" y1="{y1:.1f}" x2="{pad_l + d}" y2="{y1:.1f}"/>')
        el.append(f'<text class="bcode{cls}" x="{pad_l - 3}" y="{(y0 + y1) / 2 + 2.6:.1f}" text-anchor="end">{code} →</text>')
        lab = f"{cm(z0)}–{cm(z1)}" if z1 - z0 > 0.5 and z1 < h else f"{cm(z0)}"
        el.append(f'<text class="mtxt{cls}" x="{pad_l + d + 3}" y="{(y0 + y1) / 2 + 2.4:.1f}">{lab} см</text>')
    el.append(f'<text class="mhead" x="{pad_l + d / 2}" y="{pad_t - 6}" text-anchor="middle">{title}</text>')
    el.append(f'<text class="mtxt" x="{pad_l + d / 2}" y="{pad_t + h + 13}" text-anchor="middle">низ · высота {cm(h)} см</text>')
    return f'<svg class="marks" viewBox="0 0 {vw} {vh}" role="img" aria-label="{title}">' + "".join(el) + "</svg>"

marks_svg = (side_marks("В1 · бок витрины", HS, DU - T, [
                 (B.FLOOR_Y, B.FLOOR_Y + S, "В4", False), (B.SHELF3_Y, B.SHELF3_Y + S, "В5", False),
                 (B.SHELF2_Y, B.SHELF2_Y + S, "В5", False), (B.TOPP_Y, B.TOPP_Y + T, "В3", False)]) +
             side_marks("Т1 · бок тумбы", HL, DL - T, [
                 (B.H_PLINTH, B.H_PLINTH + T, "Т3", False), (B.DRAWER_SUP_Y, B.DRAWER_SUP_Y + S, "П1", True)]))

# ---------------------------------------------------------------- HTML
CSS = """
:root{--paper:#f5f1ea;--ink:#2a2420;--muted:#6d6259;--rule:#ddd3c4;--card:#fffdf9;--acc:#a8432f;--acc-soft:#f6dcd4;
--w1:#ecd6b4;--w2:#d6b081;--w3:#b08457;--edge:#7a5634;--d1:#a27049;--d2:#83553a;--d3:#643f29;
--n1:#f2b7a6;--n2:#dd7a63;--n3:#b4523e;--nedge:#8b3a2f;--glue:#3f9a48;--glass:#d3e3df;--metal:#6b6b6b;--ghost:#a8432f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#1c1916;--ink:#eee6db;--muted:#a99e91;--rule:#3a332c;--card:#25211d;--acc:#ec8d74;--acc-soft:#4a2a22;
--w1:#8a6a47;--w2:#72552f;--w3:#5a4024;--edge:#c9a27a;--d1:#6a4630;--d2:#553624;--d3:#40281a;--n1:#e39a86;--n2:#c9674f;--n3:#9c4332;--nedge:#f0a38f;--glue:#6fd07a;--glass:#355049;--metal:#aaa;--ghost:#ec8d74}}
:root[data-theme="dark"]{--paper:#1c1916;--ink:#eee6db;--muted:#a99e91;--rule:#3a332c;--card:#25211d;--acc:#ec8d74;--acc-soft:#4a2a22;
--w1:#8a6a47;--w2:#72552f;--w3:#5a4024;--edge:#c9a27a;--d1:#6a4630;--d2:#553624;--d3:#40281a;--n1:#e39a86;--n2:#c9674f;--n3:#9c4332;--nedge:#f0a38f;--glue:#6fd07a;--glass:#355049;--metal:#aaa;--ghost:#ec8d74}
body{background:var(--paper);color:var(--ink);font-family:"Nunito Sans",system-ui,sans-serif;font-size:17px;line-height:1.5;padding-block:24px 64px;padding-inline:16px}
main{max-width:1040px;margin:0 auto}
h1,h2,h3{font-family:"Fraunces",Georgia,serif;font-weight:600;line-height:1.15;text-wrap:balance;margin:0}
h1{font-size:2.3rem}h2{font-size:1.55rem;margin:2.6rem 0 1rem;padding-top:1rem;border-top:2px solid var(--rule)}
h3{font-size:1.25rem}
p{max-width:66ch;margin:.5rem 0}
.lead{color:var(--muted);font-size:1.08rem}
a{color:var(--acc)}
.legend{display:flex;flex-wrap:wrap;gap:10px 22px;margin:1.2rem 0;font-size:.95rem}
.legend span{display:inline-flex;align-items:center;gap:8px}
.sw{width:18px;height:14px;border:1px solid var(--edge);display:inline-block}
.prep{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.box{background:var(--card);border:1px solid var(--rule);padding:14px 18px}
.box h3{margin-bottom:.4rem}
.box ul{margin:.3rem 0;padding-left:1.1rem}.box li{margin:.25rem 0}
.tex{width:100%;border-collapse:collapse;font-size:.95rem}.tex td{padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
.chip{display:inline-block;font-weight:700;font-size:.8rem;padding:1px 8px;border-radius:10px;background:var(--acc-soft);color:var(--acc);margin-right:4px}
.step{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:22px;align-items:center;background:var(--card);border:1px solid var(--rule);padding:16px 18px;margin:14px 0}
.step.done{opacity:.55}
.fig{display:flex;justify-content:center}
.fig svg.iso{width:100%;max-width:400px;height:auto;max-height:430px}
.num{font-family:"Fraunces",serif;font-size:2rem;font-weight:600;color:var(--acc);line-height:1;margin-right:10px}
.st-head{display:flex;align-items:baseline;gap:4px;flex-wrap:wrap;margin-bottom:.5rem}
.who{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border:1px solid var(--rule);padding:1px 8px;border-radius:10px;margin-left:6px}
.step ul{margin:.4rem 0;padding-left:1.1rem}.step li{margin:.3rem 0}
.check{border-left:3px solid var(--glue);padding:4px 10px;font-size:.95rem;margin-top:.6rem}
.done-toggle{margin-top:.7rem;display:flex;align-items:center;gap:8px;font-size:.95rem;cursor:pointer}
.done-toggle input{width:18px;height:18px;accent-color:var(--acc)}
.marks-wrap{display:flex;gap:20px;flex-wrap:wrap;justify-content:center}
svg.marks{width:230px;max-width:46%;height:auto;font-family:"Nunito Sans",sans-serif}
.mark{stroke:var(--ink);stroke-width:.7;stroke-dasharray:3 2}.mark-r{stroke:var(--acc);stroke-width:.8;stroke-dasharray:3 2}
.mtxt{fill:var(--ink);font-size:7.5px}.mtxt-r{fill:var(--acc);font-size:7.5px;font-weight:700}.mhead{fill:var(--ink);font-size:8px;font-weight:700}\n.band{fill:var(--n1);opacity:.8}.band-r{fill:var(--acc);opacity:.35}.bcode,.bcode-r{font-size:7px;font-weight:800;fill:var(--ink)}.bcode-r{fill:var(--acc)}
.k-done-t{fill:var(--w1);stroke:var(--edge);stroke-width:.35}.k-done-f{fill:var(--w2);stroke:var(--edge);stroke-width:.35}.k-done-r{fill:var(--w3);stroke:var(--edge);stroke-width:.35}
.k-dark-t{fill:var(--d1);stroke:var(--edge);stroke-width:.35}.k-dark-f{fill:var(--d2);stroke:var(--edge);stroke-width:.35}.k-dark-r{fill:var(--d3);stroke:var(--edge);stroke-width:.35}
.k-new-t{fill:var(--n1);stroke:var(--nedge);stroke-width:.5}.k-new-f{fill:var(--n2);stroke:var(--nedge);stroke-width:.5}.k-new-r{fill:var(--n3);stroke:var(--nedge);stroke-width:.5}
.k-metal-t,.k-metal-f,.k-metal-r{fill:var(--metal);stroke:none}
.k-glass{fill:var(--glass);stroke:var(--edge);stroke-width:.3}
.glue{fill:var(--glue);fill-opacity:.85;stroke:none}
.ghost{fill:none;stroke:var(--ghost);stroke-width:.6;stroke-dasharray:2.2 1.6}
.drop{stroke:var(--ghost);stroke-width:.7;stroke-dasharray:2.5 1.8}.arrowhead{fill:var(--ghost)}
.tag,.tag-new{font-family:"Nunito Sans",sans-serif;font-weight:800;paint-order:stroke;stroke-linejoin:round}
.tag{fill:var(--ink);stroke:var(--card);stroke-width:2.2px}.tag-new{fill:#fff;stroke:var(--nedge);stroke-width:2.6px}
@media (max-width:720px){.step{grid-template-columns:1fr}.fig svg.iso{max-height:360px}}
"""

def build_html():
    groups = []
    for s_ in steps:
        if not groups or groups[-1][0] != s_["group"]:
            groups.append((s_["group"], []))
        groups[-1][1].append(s_)
    intro_group = {
        "А. Витрина": "Верхняя часть со стеклянными дверцами. Делается одинаково для обоих шкафов, собери подряд две.",
        "Б. Тумба": "Нижняя часть. Отличается только правым шкафом: у него есть опора ящика и заглушка.",
        "В. Соединение": "Витрина ставится на тумбу и получается целый шкаф.",
        "Г. Фасады": "Всё, что спереди: планка, дверцы, ящики, ручки.",
        "Д. Финал": "",
    }
    parts_html = []
    n = 0
    for g, ss in groups:
        parts_html.append(f"<h2>{g}</h2>")
        if intro_group.get(g):
            parts_html.append(f'<p class="lead">{intro_group[g]}</p>')
        for s_ in ss:
            n += 1
            chips = "".join(f'<span class="chip">{c}</span>' for c in s_["codes"])
            who = f'<span class="who">{s_["who"]}</span>' if s_["who"] else ""
            lis = "".join(f"<li>{b}</li>" for b in s_["bullets"])
            chk = f'<div class="check"><b>Проверь:</b> {s_["check"]}</div>' if s_["check"] else ""
            parts_html.append(f'''<section class="step" id="step{n}">
<div class="fig">{s_["svg"]}</div>
<div><div class="st-head"><span class="num">{n}</span><h3>{s_["title"]}</h3>{who}</div>
<div>{chips}</div><ul>{lis}</ul>{chk}
<label class="done-toggle"><input type="checkbox" id="done{n}" data-step="{n}"> Сделано</label></div>
</section>''')
    html = f"""<title>Сборка серванта</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Nunito+Sans:wght@400;700;800&display=swap">
<style>{CSS}</style>
<main>
<h1>Сборка серванта по шагам</h1>
<p class="lead">Картинка на каждый шаг. Уже собранное показано деревом, деталь, которую клеишь сейчас, выделена розовым и нарисована «на подлёте», пунктир показывает, куда она встанет. Зелёное — куда наносить клей. Размеры в сантиметрах, коды деталей как в <a href="https://claude.ai/artifact/Kgab8JFE1U5CgramSDSKHH">чертежах и таблице деталей</a>.</p>
<div class="legend">
<span><i class="sw" style="background:var(--w2)"></i>уже собрано</span>
<span><i class="sw" style="background:var(--n2);border-color:var(--nedge)"></i>клеишь сейчас</span>
<span><i class="sw" style="background:var(--glue);border-color:var(--glue)"></i>сюда клей</span>
<span><i class="sw" style="background:var(--d2)"></i>фасады</span>
<span><i class="sw" style="background:none;border:1.5px dashed var(--ghost)"></i>куда встанет деталь</span>
</div>

<h2>Перед началом</h2>
<div class="prep">
<div class="box"><h3>Что понадобится</h3><ul>
<li>Макетный нож и запас лезвий: картон 2 мм быстро тупит лезвие.</li>
<li>Металлическая линейка и коврик для резки.</li>
<li>Угольник или любой предмет с точным прямым углом, например коробка от телефона.</li>
<li>Клеевой пистолет с тонкими стержнями 7 мм.</li>
<li>Карандаш, пинцет, распечатанные шаблоны и текстуры.</li></ul></div>
<div class="box"><h3>Как резать</h3><ul>
<li>Нож держи вертикально, делай 4–6 лёгких проходов по линейке вместо одного сильного. Картон 3 мм требует больше проходов.</li>
<li>Окна дверок режь от углов к середине, чтобы не перерезать углы.</li>
<li>Сразу подпиши каждую деталь карандашом: код и стрелку «перед».</li></ul></div>
<div class="box"><h3>Как клеить горячим клеем</h3><ul>
<li>Клей наносится на торец, тонкой полоской, не на плоскость.</li>
<li>После нанесения есть 5–10 секунд: сразу ставь деталь, прижми и держи с угольником 15 секунд.</li>
<li>Клей, вылезший наружу, срезай ножом после остывания. Паутинку снимай пальцем.</li>
<li>Первый раз попробуй на двух обрезках картона.</li></ul></div>
</div>

<h3 style="margin-top:1.6rem">Оклейка текстурой: до сборки</h3>
<p>Деталям удобнее клеить наклейку, пока они плоские. Вырезай наклейку на 1–2 мм больше детали, наклей, потом срежь лишнее ножом по краю. Волокна вдоль длинной стороны детали. Торцы оклеиваются в самом конце узкими полосками. Если бумага глянцевая, горячий клей держится на ней хуже: поцарапай ножом место будущей склейки.</p>
<div class="box" style="overflow-x:auto"><table class="tex">
<tr><td><b>Лист 1, тёмный</b></td><td>Лицевая сторона дверок В8 и Л1, филёнки Л2, фасады П3, планка В7, верх крышки В6 и столешницы Т5.</td></tr>
<tr><td><b>Лист 2, средний</b></td><td>Внутренние стороны боков В1 и Т1 и задников В2 и Т2, полки В5 и дно витрины В4 с двух сторон, низ верхней панели В3, дно Т3, опора П1.</td></tr>
<tr><td><b>Лист 3, светлый</b></td><td>Наружные стороны боков В1 и Т1, цоколь Т4.</td></tr>
</table></div>

<h3 style="margin-top:1.6rem">Разметка боков</h3>
<p>Разметку рисуй на <b>внутренней</b> стороне бока, от нижнего края. Положи два бока рядом разметкой вверх, передними краями друг к другу: так получится зеркальная пара, левый и правый. Розовые полосы показывают, где встанет каждая деталь, цифры в см от нижнего края. П1 (красная) только на двух боках тумбы правого шкафа. Верхняя панель В3 встаёт от линии 19,7 см до самого верха.</p>
<div class="marks-wrap">{marks_svg}</div>

{"".join(parts_html)}
</main>
<script>
(function(){{
  var KEY='sborka-servanta-done';
  var saved={{}};
  try{{saved=JSON.parse(localStorage.getItem(KEY)||'{{}}')||{{}};}}catch(e){{saved={{}};}}
  document.querySelectorAll('.done-toggle input').forEach(function(cb){{
    var n=cb.getAttribute('data-step'); var sec=document.getElementById('step'+n);
    if(saved[n]){{cb.checked=true;sec.classList.add('done');}}
    cb.addEventListener('change',function(){{
      sec.classList.toggle('done',cb.checked); saved[n]=cb.checked;
      try{{localStorage.setItem(KEY,JSON.stringify(saved));}}catch(e){{}}
    }});
  }});
}})();
</script>
"""
    with open(os.path.join(ROOT, "sborka.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("ok steps:", len(steps))

if __name__ == "__main__":
    build_html()
