#!/usr/bin/env python3
"""Élő vízállás- és vízhozamadatok letöltése a hydroinfo.hu napi tábláiból.

Kimenet: live_data.json — folyónkénti friss (reggeli észlelésű) vízhozam,
vízállás, 24 órás változás és vízhőmérséklet, plusz a paksi Duna-mérce.
Futtatás: python3 fetch_live.py && python3 build_page.py
"""
import json, re, html, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = 'https://www.hydroinfo.hu/tables/'
TABLES = ['dunhid_a.html', 'tishid_a.html']   # adatsorok (Duna ill. Tisza vízrendszer)
HEADER = 'dunhid_f.html'                       # fejléc — innen jön az észlelés dátuma


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'holaviz/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('iso-8859-2')


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


def main():
    rows = {}
    for t in TABLES:
        rows.update(parse_rows(get(BASE + t)))

    m = re.search(r'szlel\S*:\s*([0-9]{4}\.[^<]*[0-9]{2}\.)',
                  html.unescape(get(BASE + HEADER)))
    obs = m.group(1).strip() if m else None

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

    now = datetime.now(ZoneInfo('Europe/Budapest'))
    out = {
        'obs': obs,
        'fetched': now.isoformat(timespec='minutes'),
        'fetched_hu': now.strftime('%Y. %m. %d. %H:%M'),
        'source': 'hydroinfo.hu (Országos Vízjelző Szolgálat)',
        'rivers': rivers,
        'paks': rec((*PAKS, None)),
    }
    json.dump(out, open('live_data.json', 'w'), ensure_ascii=False, indent=1)

    n_in = sum(1 for r in rivers.values() if r.get('in') and r['in']['q'] is not None)
    print(f"live_data.json — észlelés: {obs} · {len(rows)} állomás beolvasva, "
          f"{n_in} belépő szelvényen van élő hozam · Paks: {out['paks']}")


if __name__ == '__main__':
    main()
