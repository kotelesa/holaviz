# „Hol a víz?" publikálása az msklc.hu domainre

Az oldal egyetlen önálló HTML-fájl (`holaviz.html`), ezért bármilyen statikus
tárhelyen elfut. Az ajánlott megoldás a **GitHub Pages + GitHub Actions**:

- ingyenes (publikus repóval), automatikus HTTPS (Let's Encrypt),
- a napi adatfrissítést a GitHub beépített ütemezője végzi — a szerver
  minden reggel letölti a hydroinfo.hu adatait, újraépíti és kiteszi az oldalt,
- ha az adatletöltés hibázik, a deploy elmarad, és a tegnapi oldal marad kint
  (sosem kerül ki félkész állapot).

A `.github/workflows/refresh.yml` fájl már elkészült ebben a mappában.

---

## 1. GitHub-repó létrehozása és feltöltés

Kell hozzá egy GitHub-fiók. A mappából (Terminal):

```sh
cd ~/Downloads/Water
git init -b main
git add .
git commit -m "Hol a víz? — élő folyóvíz-forgalmi oldal"
```

Ha fent van a `gh` CLI (be van jelentkezve: `gh auth login`):

```sh
gh repo create holaviz --public --source . --push
```

Kézzel: GitHub-on hozz létre egy **publikus** repót (pl. `holaviz` néven,
README nélkül), majd:

```sh
git remote add origin https://github.com/<FELHASZNALONEV>/holaviz.git
git push -u origin main
```

> A GitHub Pages ingyenes csomagban csak **publikus** repóval működik.
> Az oldal forrása amúgy is nyilvánosan látszik a böngészőben, titok nincs benne.

## 2. GitHub Pages bekapcsolása

A repó oldalán: **Settings → Pages → Build and deployment → Source:
„GitHub Actions"**. (Nem kell branch-et választani — a workflow deployol.)

## 3. Első futtatás

A repó **Actions** fülén válaszd a „Napi frissítés és publikálás" workflow-t,
majd **Run workflow** (kézi indítás). 1–2 perc után az oldal él a
`https://<FELHASZNALONEV>.github.io/holaviz/` címen. Ezután minden nap
**08:35 UTC-kor** (nyáron 10:35, télen 9:35 magyar idő) automatikusan újraépül
friss adatokkal.

## 4. Az msklc.hu rákötése

Két lehetőség — döntsd el, a fődomainen legyen-e az oldal, vagy aldomainen
(pl. `viz.msklc.hu`), ha a főoldalt másra tartogatod.

**A) Fődomain (msklc.hu):**

1. Repó → Settings → Pages → **Custom domain**: `msklc.hu` → Save.
2. A domain-regisztrátorod DNS-kezelőjében vedd fel:

   | Típus | Név | Érték |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | `<FELHASZNALONEV>.github.io` |

3. Ha a DNS átállt (pár perc–pár óra), a Pages beállításnál pipáld be az
   **Enforce HTTPS**-t (a tanúsítványt a GitHub magától intézi).

**B) Aldomain (pl. viz.msklc.hu):** csak egy DNS-rekord kell:

   | Típus | Név | Érték |
   |---|---|---|
   | CNAME | viz | `<FELHASZNALONEV>.github.io` |

   és a Custom domain mezőbe `viz.msklc.hu` kerül.

Ellenőrzés: `dig +short msklc.hu` (a négy A-rekordot kell visszaadja), majd
nyisd meg a https://msklc.hu -t.

## 5. Későbbi módosítások

Bármilyen változtatás (sablon, adatok, szövegek) után:

```sh
git add -A && git commit -m "..." && git push
```

— a push magától újraépíti és kiteszi az oldalt (a workflow push-ra is fut).

---

## Alternatíva: meglévő magyar tárhely (FTP/cPanel)

Ha az msklc.hu-hoz már van webtárhelyed és azt akarod használni:

1. Építsd meg helyben az oldalt: `python3 fetch_live.py && python3 build_page.py`
2. Töltsd fel a `holaviz.html`-t a tárhely gyökerébe **`index.html`** néven.
3. A napi frissítéshez vagy a tárhely cron + Python (ha van), vagy GitHub
   Actions + FTP-feltöltés (pl. `SamKirkland/FTP-Deploy-Action`) — ez utóbbihoz
   az FTP-jelszót a repó Settings → Secrets alatt kell tárolni, soha ne a kódban.

A GitHub Pages-es út ennél egyszerűbb és robusztusabb, ezt csak akkor érdemes,
ha a tárhely már úgyis fizetve van és ott akarsz mindent tartani.

---

## Megjegyzések

- **A claude.ai-s artifact és a napi rutin** (claude.ai/code/routines) ettől
  függetlenül tovább él; ha az msklc.hu lesz az elsődleges hely, a rutin
  kikapcsolható — de meg is tartható, nem zavarják egymást.
- **Forrásmegjelölés**: az oldal lábléce feltünteti a hydroinfo.hu-t (OVSZ) és
  a vizugy.hu-t. Nyilvános megjelenés előtt érdemes átfutni a hydroinfo.hu
  „Jogi nyilatkozat" oldalát az adatok újraközlésének feltételeiről.
- Az oldal láblécében a „lekérdezve" időpont mutatja, melyik napi állapot van
  kint — ha ez elavul, az Actions fülön látszik, melyik futás és miért hibázott.
