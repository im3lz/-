# -*- coding: utf-8 -*-
"""Три текстуры древесины под сервант, A4 300 dpi, для печати на клейкой бумаге.

Запуск: python3 generator/textures.py
Создаёт textures/1-fasad.png, 2-nisha-polki.png, 3-boka.png и tekstury-a4.pdf.
Волокна идут вдоль длинной стороны листа (по вертикали A4).
"""
import os
import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "textures")
os.makedirs(OUT, exist_ok=True)

DPI = 300
W, H = 2480, 3508          # A4 при 300 dpi
MM = DPI / 25.4            # пикселей в мм
rng = np.random.default_rng(7)

def noise(shape, cell_x, cell_y, octaves=3, seed=0):
    """Фрактальный шум с анизотропными ячейками (cell в пикселях)."""
    r = np.random.default_rng(seed)
    out = np.zeros(shape, np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        cy = max(2, int(shape[0] / (cell_y / 2 ** o)) + 2)
        cx = max(2, int(shape[1] / (cell_x / 2 ** o)) + 2)
        g = r.standard_normal((cy, cx)).astype(np.float32)
        z = zoom(g, (shape[0] / cy, shape[1] / cx), order=3)[:shape[0], :shape[1]]
        out += amp * z; tot += amp; amp *= 0.5
    return out / tot

def wood(dark, mid, light, period_mm, ring_contrast, fiber_contrast, warp_mm, patch_contrast, seed, sharp=2.0, arc=0.06):
    """dark/mid/light — цвета RGB; period_mm — средний шаг годовых колец; всё в мм.
    Кольца — дуги от центра бревна, вынесенного за лист (тангенциальный распил), с неравномерной шириной."""
    r = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = -W * r.uniform(0.15, 0.6)                    # центр бревна левее листа
    cy = H * r.uniform(0.3, 0.7)
    dist = np.sqrt((xs - cx) ** 2 + ((ys - cy) * arc) ** 2)
    warp = noise((H, W), 40 * MM, 300 * MM, octaves=3, seed=seed) * warp_mm * MM
    warp += noise((H, W), 8 * MM, 90 * MM, octaves=2, seed=seed + 1) * warp_mm * 0.2 * MM
    phase = (dist + warp) / (period_mm * MM)
    # неравномерная ширина колец: 0.55..1.8 среднего шага
    n_rings = int(phase.max()) + 3
    widths = r.uniform(0.55, 1.8, n_rings).astype(np.float32)
    edges = np.concatenate([[0], np.cumsum(widths)])
    idx = np.searchsorted(edges, phase, side="right") - 1
    idx = np.clip(idx, 0, n_rings - 1)
    frac = (phase - edges[idx]) / widths[idx]
    ring = np.power(np.clip(frac, 0, 1), sharp)       # 0 — тёмная кромка кольца, 1 — светлая часть
    # контраст кольца плавает от кольца к кольцу
    rc = r.uniform(0.5, 1.0, n_rings).astype(np.float32)[idx]
    ring = 0.5 + (ring - 0.5) * rc
    ring = gaussian_filter(ring, 0.7)
    # волокна: вытянутый по y шум, с обрывами
    fiber = noise((H, W), 0.35 * MM, 20 * MM, octaves=2, seed=seed + 2)
    fiber = fiber / (np.abs(fiber).max() + 1e-6)
    breaks = noise((H, W), 3 * MM, 30 * MM, octaves=1, seed=seed + 4)
    fiber = fiber * (0.6 + 0.4 * np.clip(breaks * 2, -1, 1))
    # крупные пятна тона
    patch = noise((H, W), 60 * MM, 200 * MM, octaves=2, seed=seed + 3)
    patch = patch / (np.abs(patch).max() + 1e-6)
    t = 0.5 + ring_contrast * (ring - 0.5) + fiber_contrast * fiber + patch_contrast * patch
    t = np.clip(t, 0, 1)
    dark, mid, light = (np.array(c, np.float32) for c in (dark, mid, light))
    img = np.where(t[..., None] < 0.5,
                   dark + (mid - dark) * (t[..., None] * 2),
                   mid + (light - mid) * ((t[..., None] - 0.5) * 2))
    img += rng.standard_normal(img.shape).astype(np.float32) * 1.5
    return np.clip(img, 0, 255).astype(np.uint8)

TEX = [
    ("1-fasad", "1 · ФАСАДЫ: дверцы, фасады ящиков, планка, карниз, столешница · тёмный орех",
     dict(dark=(58, 28, 12), mid=(96, 52, 26), light=(138, 84, 46),
          period_mm=1.4, ring_contrast=0.6, fiber_contrast=0.2, warp_mm=8, patch_contrast=0.14, seed=10, sharp=1.5, arc=0.05)),
    ("2-nisha-polki", "2 · НИША И ПОЛКИ: внутренние стенки, полки, дно и верх витрины · средний орех",
     dict(dark=(112, 68, 38), mid=(150, 100, 60), light=(190, 140, 92),
          period_mm=1.6, ring_contrast=0.5, fiber_contrast=0.18, warp_mm=7, patch_contrast=0.12, seed=20, sharp=1.7, arc=0.07)),
    ("3-boka", "3 · БОКА И ЦОКОЛЬ: наружные боковины, цоколь · светлый ламинат",
     dict(dark=(158, 114, 66), mid=(182, 136, 82), light=(206, 162, 108),
          period_mm=1.0, ring_contrast=0.28, fiber_contrast=0.14, warp_mm=4, patch_contrast=0.07, seed=30, sharp=2.2, arc=0.04)),
]

def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

pages = []
for name, title, params in TEX:
    arr = wood(**params)
    im = Image.fromarray(arr, "RGB")
    # узкая белая полоса с подписью и линейкой 10 см по нижнему краю (обрезать)
    d = ImageDraw.Draw(im)
    band = int(7 * MM)
    d.rectangle([0, H - band, W, H], fill=(255, 255, 255))
    d.text((int(6 * MM), H - band + int(1.5 * MM)), title + " · печать 100 %, 300 dpi", fill=(0, 0, 0), font=font(int(2.6 * MM)))
    x0, y = int(6 * MM), H - int(1.6 * MM)
    d.line([x0, y, x0 + int(100 * MM), y], fill=(0, 0, 0), width=3)
    for i in range(0, 101, 10):
        d.line([x0 + int(i * MM), y - int(1.2 * MM), x0 + int(i * MM), y], fill=(0, 0, 0), width=3)
    d.text((x0 + int(102 * MM), y - int(2.2 * MM)), "10 см", fill=(0, 0, 0), font=font(int(2 * MM)))
    im.save(os.path.join(OUT, name + ".png"), dpi=(DPI, DPI), optimize=True)
    pages.append(im)
    print("ok", name)

pages[0].save(os.path.join(ROOT, "tekstury-a4.pdf"), save_all=True, append_images=pages[1:], resolution=DPI, quality=92)
print("pdf ok")
