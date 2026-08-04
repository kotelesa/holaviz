# Hol a víz? — Magyarország folyóvíz-forgalma

A holadelej.hu stílusát követő oldal, amely az országba belépő és onnan kilépő
folyók vízhozamát (m³/s) mutatja térképen, kártyákon és táblázatban.

**Publikált artifact:** https://claude.ai/code/artifact/09b358d9-1bad-44e0-a033-515304a4dc84

## Fájlok

| Fájl | Szerep |
|---|---|
| `holaviz.html` | a kész, publikált oldal (önálló, minden inline) |
| `holaviz_template.html` | sablon — CSS/HTML/JS, a `/*__GEO__*/`, `/*__RIVERS__*/` és `/*__LIVE__*/` helyére kerül az adat |
| `rivers_data.json` | folyónkénti adatok: KÖQ hozam (qin/qout), határszelvény, feliratpozíciók (labIn/labOut), tooltip-szövegek |
| `fetch_live.py` | élő adatok letöltése a hydroinfo.hu napi tábláiból → `live_data.json` |
| `live_data.json` | friss (reggeli észlelésű) hozam/vízállás folyónként + a paksi Duna-mérce |
| `build_geometry.py` | térkép-geometria generálása lon/lat pontokból (határ, folyók, tavak, Paks-jelölő) → `geometry.json` |
| `build_page.py` | sablon + geometria + folyóadatok + élő adatok összefűzése → `holaviz.html` |
| `geometry.json` | generált SVG-geometria |
| `hungary_hi.json` | Magyarország részletes körvonala (georgique/world-geojson) |
| `elonezet.png` | asztali nézet előnézeti képe (a 2026-08-03-i, még KÖQ-alapú állapotról) |

## Frissítés / újraépítés

```sh
python3 fetch_live.py       # friss adatok letöltése (hydroinfo.hu)
python3 build_geometry.py   # csak ha a folyóútvonalak/térkép változik
python3 build_page.py       # holaviz.html előállítása
```

Frissítés után az artifactot ugyanarra az URL-re kell újrapublikálni. Az
artifact futásidőben nem tud külső adatot lekérni (CSP), ezért az „élő" adat a
publikáláskori legfrissebb reggeli észlelés — a lábléc mutatja az észlelés és a
lekérdezés időpontját.

## Adatok

**Élő adatok**: hydroinfo.hu (OVSZ) napi hidrológiai táblái —
`tables/dunhid_a.html` (Duna-vízrendszer), `tables/tishid_a.html`
(Tisza-vízrendszer), dátum a `tables/dunhid_f.html`-ből. ISO-8859-2 kódolás,
10 cellás sorok: állomáskód, állomás, folyó, vízállás (tegnap reggel/este, ma
reggel), 24 h változás, reggeli vízhozam, vízhő, jégállapot. Mérce-választás:
Duna belépő = **Nagybajcs** (a bősi üzemvízcsatorna visszatorkollása alatt),
Duna kilépő = **Dunaszekcső** (Mohács nem közöl hozamot), Dráva belépő élőben
közvetlenül **Őrtilos**. A Lajta, Kerka, Ronyva nem közöl élő hozamot → KÖQ
jelöléssel, az élő összegekben nem szerepelnek. **Paks** külön jelölőt és
KPI-kártyát kap (vízállás, változás, hozam, vízhő).

**Viszonyítás**: sokéves középvízhozamok (KÖQ, 1981–2010), forrás: VGT3 6-8.
háttéranyag határszelvény-táblázata (vizeink.hu / OVF). Kulcsszámok: belépő
~3 252 m³/s (24 vízfolyás), kilépő ~3 699 m³/s (Duna Mohács 2 342, Tisza 855,
Dráva 502). A Dráva KÖQ belépő értéke számított: Botovo 473 − Mura 169 = 304.

## Publikálás saját domainre

Az msklc.hu-ra (vagy aldomainre) való kitétel lépései a
[PUBLIKALAS.md](PUBLIKALAS.md)-ben: GitHub Pages + a kész
`.github/workflows/refresh.yml` (napi automatikus adatfrissítéssel), illetve
alternatívaként hagyományos FTP-s tárhely.

## Lehetséges folytatás

- automatikus napi frissítés (ütemezett agent: fetch_live + build + republish)
- EN nyelvi változat (a holadelej.hu-hoz hasonló HU/EN kapcsoló)
- kisvízfolyások hivatalos adat nélkül (Ikva, Gyöngyös, Lendva, Karasica) — most csak láblécben említve
