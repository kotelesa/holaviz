#!/usr/bin/env python3
"""Magyarország-térkép geometria a 'Hol a víz?' oldalhoz.
Kimenet: geometry.json — határ, folyók, tavak SVG-koordinátákkal."""
import json, math

# ---- vetítés ----
LON0, LON1 = 16.05, 22.95
LAT0, LAT1 = 45.68, 48.68
COSLAT = math.cos(math.radians(47.15))
W = 960.0  # a határ doboz szélessége px-ben
K = W / ((LON1 - LON0) * COSLAT)
PADX, PADY = 60.0, 46.0

def P(lon, lat):
    x = (lon - LON0) * COSLAT * K + PADX
    y = (LAT1 - lat) * K + PADY
    return round(x, 1), round(y, 1)

VIEW_W = round((LON1 - LON0) * COSLAT * K + 2 * PADX)
VIEW_H = round((LAT1 - LAT0) * K + 2 * PADY)

# ---- határ (Douglas–Peucker egyszerűsítés) ----
def dp(points, eps):
    if len(points) < 3:
        return points
    def pdist(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        dx, dy = bx - ax, by - ay
        if dx == dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        d = pdist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = dp(points[:idx + 1], eps)
        right = dp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]

raw = json.load(open('hungary_hi.json'))['features'][0]['geometry']['coordinates'][0]
border_px = [P(lon, lat) for lon, lat in raw]
border_px = dp(border_px, 1.2)
border_path = 'M' + ' '.join(f'{x},{y}' for x, y in border_px) + 'Z'

# ---- Catmull-Rom -> kubikus Bézier simítás a folyókhoz ----
def smooth_path(pts):
    if len(pts) < 3:
        return 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
    p = [pts[0]] + list(pts) + [pts[-1]]
    d = f'M{p[1][0]},{p[1][1]}'
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (round(p1[0] + (p2[0] - p0[0]) / 6, 1), round(p1[1] + (p2[1] - p0[1]) / 6, 1))
        c2 = (round(p2[0] - (p3[0] - p1[0]) / 6, 1), round(p2[1] - (p3[1] - p1[1]) / 6, 1))
        d += f' C{c1[0]},{c1[1]} {c2[0]},{c2[1]} {p2[0]},{p2[1]}'
    return d

# ---- folyók útvonalai (lon, lat pontok folyásirányban) ----
RIVERS = {
    'duna': [(17.53,48.03),(17.63,47.96),(17.75,47.87),(17.83,47.75),(18.12,47.76),(18.45,47.77),(18.74,47.80),(18.87,47.82),(18.98,47.79),(19.13,47.77),(19.06,47.60),(19.05,47.45),(18.92,47.30),(18.94,46.98),(18.86,46.63),(18.90,46.42),(18.94,46.18),(18.82,46.03),(18.83,45.91)],
    'mosoni-duna': [(17.55,48.00),(17.40,47.92),(17.27,47.87),(17.42,47.83),(17.63,47.69),(17.75,47.75)],
    'lajta': [(17.07,47.91),(17.17,47.89),(17.27,47.87)],
    'raba': [(16.27,46.94),(16.61,47.01),(16.85,47.14),(16.94,47.25),(17.10,47.40),(17.30,47.52),(17.55,47.62),(17.63,47.68)],
    'pinka': [(16.45,47.21),(16.50,47.12),(16.57,47.05),(16.62,47.02)],
    'repce': [(16.68,47.43),(16.85,47.45),(17.02,47.42),(17.20,47.50),(17.45,47.62),(17.62,47.69)],
    'kerka': [(16.55,46.63),(16.58,46.56),(16.61,46.52)],
    'zala': [(16.60,46.85),(16.80,46.83),(17.00,46.72),(17.16,46.72),(17.25,46.76)],
    'sio': [(18.07,46.90),(18.30,46.78),(18.50,46.63),(18.70,46.47),(18.86,46.36)],
    'mura': [(16.52,46.52),(16.62,46.47),(16.72,46.43),(16.88,46.36),(16.93,46.31)],
    'drava': [(16.93,46.31),(17.10,46.20),(17.22,46.10),(17.35,46.02),(17.46,45.96),(17.65,45.87),(17.90,45.80),(18.10,45.77),(18.21,45.77),(18.33,45.76)],
    'ipoly': [(19.64,48.22),(19.52,48.10),(19.29,48.07),(19.13,48.05),(19.03,48.07),(18.95,47.95),(18.90,47.87),(18.86,47.82)],
    'zagyva': [(19.80,48.09),(19.72,47.85),(19.68,47.67),(19.80,47.58),(19.91,47.50),(20.00,47.35),(20.14,47.25),(20.19,47.18)],
    'sajo': [(20.36,48.31),(20.55,48.27),(20.62,48.25),(20.73,48.22),(20.85,48.11),(20.92,48.02),(21.00,47.98),(21.05,47.94)],
    'hernad': [(21.25,48.51),(21.18,48.40),(21.13,48.33),(21.00,48.22),(20.95,48.14),(20.98,48.06),(21.00,48.00)],
    'bodva': [(20.85,48.56),(20.78,48.43),(20.74,48.30),(20.77,48.22),(20.80,48.17)],
    'bodrog': [(21.68,48.36),(21.60,48.31),(21.52,48.25),(21.45,48.17),(21.41,48.12)],
    'tisza': [(22.83,48.10),(22.70,48.09),(22.52,48.07),(22.32,48.12),(22.22,48.26),(22.17,48.40),(22.05,48.38),(21.93,48.26),(21.70,48.19),(21.50,48.14),(21.41,48.11),(21.37,48.02),(21.20,47.97),(21.05,47.93),(20.90,47.80),(20.76,47.62),(20.56,47.56),(20.50,47.49),(20.30,47.32),(20.18,47.17),(20.10,46.93),(20.14,46.71),(20.19,46.53),(20.15,46.38),(20.15,46.25),(20.09,46.10)],
    'tur': [(22.87,47.95),(22.75,48.00),(22.64,48.04),(22.70,48.09)],
    'szamos': [(22.68,47.83),(22.55,47.90),(22.45,47.98),(22.36,48.05),(22.32,48.12)],
    'kraszna': [(22.56,47.78),(22.45,47.85),(22.38,47.95),(22.32,48.05),(22.31,48.12)],
    'berettyo': [(21.81,47.28),(21.65,47.23),(21.54,47.22),(21.35,47.15),(21.20,47.06),(21.17,47.02)],
    'sebes-koros': [(21.60,47.02),(21.45,47.03),(21.30,47.03),(21.17,47.01),(21.05,46.97),(20.95,46.94)],
    'fekete-koros': [(21.45,46.75),(21.35,46.72),(21.25,46.70)],
    'feher-koros': [(21.30,46.66),(21.27,46.68),(21.25,46.70)],
    'kettos-koros': [(21.25,46.70),(21.13,46.77),(21.03,46.88),(20.95,46.94)],
    'harmas-koros': [(20.95,46.94),(20.83,46.93),(20.65,46.90),(20.45,46.88),(20.29,46.84),(20.20,46.78),(20.16,46.72)],
    'maros': [(20.72,46.17),(20.60,46.19),(20.48,46.21),(20.35,46.23),(20.25,46.24),(20.17,46.25)],
    # Szinva: Lillafüred -> Diósgyőr -> Miskolc belváros -> Sajó-torkolat
    'szinva': [(20.59,48.10),(20.66,48.105),(20.73,48.10),(20.80,48.095),(20.87,48.08)],
}

# ---- tavak ----
LAKES = {
    'balaton': [(17.25,46.77),(17.38,46.81),(17.45,46.80),(17.52,46.80),(17.62,46.83),(17.75,46.88),(17.87,46.92),(17.91,46.90),(17.95,46.94),(18.02,47.00),(18.10,47.04),(18.14,47.01),(18.10,46.96),(18.05,46.90),(17.95,46.87),(17.90,46.88),(17.88,46.86),(17.75,46.81),(17.62,46.77),(17.52,46.74),(17.40,46.72),(17.31,46.72),(17.25,46.77)],
    'tisza-to': [(20.52,47.56),(20.60,47.61),(20.70,47.63),(20.74,47.60),(20.66,47.57),(20.58,47.53),(20.52,47.56)],
    'ferto': [(16.68,47.66),(16.72,47.69),(16.78,47.71),(16.80,47.68),(16.75,47.65),(16.70,47.63),(16.68,47.66)],
    'velencei': [(18.53,47.17),(18.60,47.20),(18.66,47.22),(18.64,47.19),(18.57,47.15),(18.53,47.17)],
}

# ---- kis tavak pontként ----
# A térkép léptékén (~0,5 km/px) körvonalként nem látszanának, ezért pontjelet
# kapnak. Mályi-tó: ~1,0 × 0,6 km-es bányató Miskolctól délre (OSM-középpont).
LAKE_POINTS = {
    'malyi': (20.8408, 48.0168),
}

out = {
    'view': {'w': VIEW_W, 'h': VIEW_H},
    'border': border_path,
    'rivers': {},
    'lakes': {},
}
for rid, pts in RIVERS.items():
    px = [P(lon, lat) for lon, lat in pts]
    out['rivers'][rid] = {
        'path': smooth_path(px),
        'start': px[0], 'end': px[-1],
        # irányszög fokban az első ill. utolsó szakaszból
        'a0': round(math.degrees(math.atan2(px[1][1]-px[0][1], px[1][0]-px[0][0])), 1),
        'a1': round(math.degrees(math.atan2(px[-1][1]-px[-2][1], px[-1][0]-px[-2][0])), 1),
    }
for lid, pts in LAKES.items():
    px = [P(lon, lat) for lon, lat in pts]
    out['lakes'][lid] = smooth_path(px) + 'Z'
out['lakepts'] = {lid: P(lon, lat) for lid, (lon, lat) in LAKE_POINTS.items()}

# városjelek referenciának
CITIES = {'Budapest': (19.05, 47.50), 'Szeged': (20.15, 46.25), 'Győr': (17.63, 47.69),
          'Miskolc': (20.78, 48.10), 'Pécs': (18.23, 46.07), 'Debrecen': (21.63, 47.53)}
out['cities'] = {n: P(lon, lat) for n, (lon, lat) in CITIES.items()}

# kiemelt mércék (a paksi pont a Duna kirajzolt vonalán ül)
MARKERS = {'paks': (18.86, 46.625)}
out['markers'] = {n: P(lon, lat) for n, (lon, lat) in MARKERS.items()}

json.dump(out, open('geometry.json', 'w'), ensure_ascii=False)
print('viewBox:', VIEW_W, VIEW_H, '| border pts:', len(border_px), '| rivers:', len(out['rivers']))
