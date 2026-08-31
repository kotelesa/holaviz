#!/usr/bin/env python3
"""Élő vízállás- és vízhozamadatok letöltése a hydroinfo.hu napi tábláiból.

Kimenet: live_data.json — folyónkénti friss (reggeli észlelésű) vízhozam,
vízállás, 24 órás változás és vízhőmérséklet, plusz a paksi Duna-mérce.
Futtatás: python3 fetch_live.py && python3 build_page.py
"""
import json, re, html, sys, time, traceback, urllib.error, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = 'https://www.hydroinfo.hu/tables/'
TABLES = ['dunhid_a.html', 'tishid_a.html']   # adatsorok (Duna ill. Tisza vízrendszer)
HEADER = 'dunhid_f.html'                       # fejléc — innen jön az észlelés dátuma

# Böngészőszerű fejlécek: a hydroinfo.hu 2026-08-25 óta elutasítja a
# "gyanús" (bot-UA-jú) kéréseket a GitHub-futtatók felől.
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'hu-HU,hu;q=0.9,en;q=0.8',
}


def get(url, tries=3, wait=15):
    """Letöltés újrapróbálkozással; a végleges hibát részletesen jelenti."""
    for i in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('iso-8859-2')
        except urllib.error.HTTPError as e:
            body = e.read(300).decode('iso-8859-2', 'replace')
            last = f'HTTP {e.code} {e.reason} — válasz eleje: {body!r}'
        except Exception as e:
            last = f'{type(e).__name__}: {e}'
        if i < tries:
            print(f'{url} — {i}. próba sikertelen ({last}), várakozás {wait}s…')
            time.sleep(wait)
    raise RuntimeError(f'{url} letöltése {tries} próbából sem sikerült: {last}')


def num(s):
    """'24,5' -> 24.5; '//' vagy üres -> None."""
    s = s.replace('\xa0', '').strip()
    if not s or '/' in s:
        return None
    try:
        v = float(s.replace(',', '.'))
        return int(v) if v == int(v) and ',' not in s else v
    except ValueError:
        return None


def parse_rows(raw):
    """(folyó, állomás) -> {level, chg, q, temp} — az első előfordulás nyer."""
    out = {}
    for tr in re.findall(r'<tr>(.*?)</tr>', raw, re.S):
        cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip()
                 for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(cells) != 10:
            continue
        _, station, river, _, _, t_am, chg, q, temp, _ = cells
        out.setdefault((river, station), {
            'level': num(t_am), 'chg': num(chg), 'q': num(q), 'temp': num(temp)})
    return out


# folyó-azonosító -> mérőállomás a hydroinfo táblákban
#   in/out: határszelvény (belépő/kilépő), w: hazai vízfolyás jellemző mércéje
#   lab: megjelenítendő állomásnév (ha eltér, magyarázattal)
STATIONS = {
    'duna': {'in':  ('Duna', 'Nagybajcs', 'Nagybajcs (Vámosszabadi)'),
             'out': ('Duna', 'Dunaszekcső', 'Dunaszekcső (Mohács fölött)')},
    'mosoni-duna': {'in': ('Mosoni-Duna', 'Rajka 6. zsilip alvíz', 'Rajka, 6. zsilip')},
    'lajta': {'in': ('Lajta', 'Hegyeshalom (Lendvai tanya)', 'Hegyeshalom')},
    'raba': {'in': ('Rába', 'Szentgotthárd', None)},
    'pinka': {'in': ('Pinka', 'Felsőcsatár', None)},
    'repce': {'in': ('Répce', 'Répcevis', None)},
    'kerka': {},   # nincs a hydroinfo táblákban
    'mura': {'in': ('Mura', 'Letenye', None)},
    'drava': {'in':  ('Dráva', 'Őrtilos', None),
              'out': ('Dráva', 'Drávaszabolcs', None)},
    'ipoly': {'in': ('Ipoly', 'Ipolytarnóc', None)},
    'sajo': {'in': ('Sajó', 'Sajópüspöki', None)},
    'bodva': {'in': ('Bódva', 'Hidvégardó', None)},
    'hernad': {'in': ('Hernád', 'Hidasnémeti', None)},
    'bodrog': {'in': ('Bodrog', 'Felsőberecki', None)},
    'tisza': {'in':  ('Tisza', 'Tiszabecs', None),
              'out': ('Tisza', 'Szeged', None)},
    'ronyva': {},  # nincs a hydroinfo táblákban
    'tur': {'in': ('Túr', 'Garbolc', None)},
    'szamos': {'in': ('Szamos', 'Csenger', None)},
    'kraszna': {'in': ('Kraszna', 'Ágerdőmajor', None)},
    'berettyo': {'in': ('Berettyó', 'Pocsaj', None)},
    'sebes-koros': {'in': ('Sebes-Körös', 'Körösszakál', None)},
    'fekete-koros': {'in': ('Fekete-Körös', 'Sarkad-Malomfok', 'Sarkad')},
    'feher-koros': {'in': ('Fehér-Körös', 'Gyula', None)},
    'maros': {'in': ('Maros', 'Nagylak', None)},
    'kettos-koros': {'w': ('Kettős-Körös', 'Doboz', None)},
    'harmas-koros': {'w': ('Hármas-Körös', 'Kunszentmárton', None)},
    'zagyva': {'w': ('Zagyva', 'Jásztelek', None)},
    'zala': {'w': ('Zala', 'Zalaapáti', None)},
    'sio': {'w': ('Sió', 'Szekszárd (Palánk)', None)},
}

PAKS = ('Duna', 'Paks')

# tavak — vízszint a jellemző mércén; a Tisza-tavat a Kisköre-felső
# (duzzasztott tér) mérce adja. A kulcsok a geometry.json tó-azonosítói.
LAKES = {
    'balaton':  ('Balaton', 'Balaton átlag', 'Balaton (átlag)'),
    'velencei': ('Velencei-tó', 'Agárd', 'Agárd'),
    'ferto':    ('Fertő-tó', 'Fertőrákos', 'Fertőrákos'),
    'tisza-to': ('Tisza', 'Kisköre felső', 'Kisköre-felső (duzzasztott tér)'),
}


def main():
    rows = {}
    for t in TABLES:
        rows.update(parse_rows(get(BASE + t)))

    m = re.search(r'szlel\S*:\s*([0-9]{4}\.[^<]*[0-9]{2}\.)',
                  html.unescape(get(BASE + HEADER)))
    obs = m.group(1).strip() if m else None

    # ISO dátum az angol megjelenítéshez ("2026. augusztus 05." -> "2026-08-05")
    MONTHS = {'január': 1, 'február': 2, 'március': 3, 'április': 4, 'május': 5,
              'június': 6, 'július': 7, 'augusztus': 8, 'szeptember': 9,
              'október': 10, 'november': 11, 'december': 12}
    obs_iso = None
    if obs:
        dm = re.match(r'(\d{4})\.\s*(\S+)\s*(\d{1,2})\.', obs)
        if dm and dm.group(2).lower() in MONTHS:
            obs_iso = f'{dm.group(1)}-{MONTHS[dm.group(2).lower()]:02d}-{int(dm.group(3)):02d}'

    def rec(spec):
        river, station, lab = spec
        d = rows.get((river, station))
        if not d:
            return None
        return {'st': lab or station, **d}

    rivers = {}
    for rid, spec in STATIONS.items():
        entry = {k: rec(v) for k, v in spec.items()}
        if entry:
            rivers[rid] = entry

    lakes = {lid: r for lid, spec in LAKES.items() if (r := rec(spec))}
    # a Balaton-átlag mérce vízhőt nem közöl — a siófokiét vesszük át
    if 'balaton' in lakes and lakes['balaton'].get('temp') is None:
        sio = rows.get(('Balaton', 'Siófok'))
        if sio and sio.get('temp') is not None:
            lakes['balaton']['temp'] = sio['temp']
            lakes['balaton']['tempst'] = 'Siófok'

    now = datetime.now(ZoneInfo('Europe/Budapest'))
    out = {
        'obs': obs,
        'obs_iso': obs_iso,
        'fetched': now.isoformat(timespec='minutes'),
        'fetched_hu': now.strftime('%Y. %m. %d. %H:%M'),
        'source': 'hydroinfo.hu (Országos Vízjelző Szolgálat)',
        'rivers': rivers,
        'lakes': lakes,
        'paks': rec((*PAKS, None)),
    }
    json.dump(out, open('live_data.json', 'w'), ensure_ascii=False, indent=1)

    n_in = sum(1 for r in rivers.values() if r.get('in') and r['in']['q'] is not None)
    print(f"live_data.json — észlelés: {obs} · {len(rows)} állomás beolvasva, "
          f"{n_in} belépő szelvényen van élő hozam · {len(lakes)} tó · Paks: {out['paks']}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # GitHub Actions annotáció: a hiba oka a futás összefoglalójában
        # olvasható, nem kell hozzá a logot bogarászni.
        print(f'::error title=fetch_live.py hiba::{e}')
        traceback.print_exc()
        sys.exit(1)
