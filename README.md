# PhotoRoom API Tesztelő és Batch Feldolgozó Szkriptek

Ez a repository különböző szkripteket tartalmaz a PhotoRoom API teszteléséhez és képek kötegelt feldolgozásához.

## Szkriptek

1. **photoroom_api_test.py** - Egyszerű teszt szkript a PhotoRoom API alapvető használatához
2. **photoroom_api_params.py** - Az összes API paraméter tesztelése különböző beállításokkal
3. **batch_process.py** - Képek kötegelt feldolgozása és opcionális feltöltése Shopify-ra
4. **photoroom_api_parameters.md** - Részletes dokumentáció az API paraméterekről

## PhotoRoom API Tervek

A PhotoRoom két fő API tervet kínál:
- **Basic terv**: Remove Background API - Egyszerű háttér eltávolítás
- **Plus terv**: Image Editing API - Fejlett funkciók, beleértve az AI árnyékokat, háttérképeket, újravilágítást és egyebeket

## Telepítés

A szükséges csomagok telepítéséhez futtasd:

```bash
pip install -r requirements.txt
```

## Használat

### 1. Egyszerű API Teszt

```bash
python photoroom_api_test.py --image /path/to/image.jpg --output /path/to/output.webp --api-key YOUR_API_KEY
```

### 2. API Paraméterek Tesztelése

```bash
python photoroom_api_params.py --image /path/to/image.jpg --output-dir /path/to/output --use-live --debug
```

Opciók:
- `--image` - A feldolgozandó kép elérési útja
- `--output-dir` - A kimeneti képek mappája
- `--use-live` - Live API használata (alapértelmezett: sandbox)
- `--debug` - Debug mód bekapcsolása
- `--param-set N` - Csak egy adott paraméter-készlet futtatása (1-35)
- `--use-plus` - Plus API használata (v2 API)
- `--bg-image` - Háttérkép elérési útja a bg_image paraméterhez

### 3. Kötegelt Feldolgozás

```bash
python batch_process.py --input-dir /path/to/images --output-dir /path/to/output --batch-size 10 --photoroom-api-key YOUR_API_KEY [további opciók]
```

#### Alap Opciók:
- `--input-dir` - Bemeneti képek mappája
- `--output-dir` - Kimeneti képek mappája
- `--batch-size` - Köteg mérete (alapértelmezett: 10)
- `--photoroom-api-key` - PhotoRoom API kulcs

#### Shopify Feltöltés Opciók:
- `--shopify-api-key` - Shopify API kulcs (opcionális)
- `--shopify-password` - Shopify jelszó (opcionális)
- `--shopify-store` - Shopify bolt URL (opcionális)

#### PhotoRoom API Paraméterek:
- `--bg-color` - Háttérszín (alapértelmezett: #EEEEE5)
- `--shadow` - Árnyék típusa (soft/natural/none, alapértelmezett: soft)
- `--position` - Pozíció (alapértelmezett: center)
- `--scale` - Méretezés százalékban (alapértelmezett: 13)
- `--size` - Méret (portrait/square/original, alapértelmezett: portrait)
- `--crop` - Automatikus vágás (alapértelmezett: kikapcsolva)
- `--quality` - Minőség (1-100, alapértelmezett: 90)
- `--format` - Formátum (png/jpg/webp, alapértelmezett: webp)

#### Plus API Specifikus Paraméterek:
- `--use-plus` - Plus API használata (v2 API)
- `--hd` - HD háttér eltávolítás
- `--dpi` - DPI beállítás (pl. 300)
- `--bg-prompt` - AI generált háttér prompt (pl. "A beautiful beach at sunset")
- `--bg-style` - AI generált háttér stílusa (photographic/flat_color/gradient/pattern)
- `--relight` - AI újravilágítás
- `--relight-direction` - Fény iránya (front/left/right/top)
- `--relight-strength` - Fény erőssége (low/medium/high)
- `--remove-text` - Szöveg eltávolítása
- `--expand` - Kép kiterjesztése
- `--expand-factor` - Kiterjesztés mértéke (pl. 1.5)
- `--upscale` - AI felskálázás
- `--upscale-factor` - Felskálázás mértéke (2/4)
- `--bg-image` - Egyedi háttérkép elérési útja
- `--bg-image-url` - Egyedi háttérkép URL

#### Egyéb Opciók:
- `--debug` - Debug mód bekapcsolása

## Példák

### Alap Háttér Eltávolítás

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY
```

### Egyedi Háttérszín és Árnyék

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY --bg-color "#FFFFFF" --shadow natural
```

### Shopify Optimalizált Beállítások

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY --bg-color "#EEEEE5" --shadow soft --position center --scale 13 --size portrait --crop --format webp --quality 90
```

### AI Generált Háttér (Plus API)

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY --use-plus --bg-prompt "A beautiful beach at sunset" --bg-style photographic
```

### AI Újravilágítás (Plus API)

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY --use-plus --relight --relight-direction left --relight-strength medium
```

### Shopify Feltöltés

```bash
python batch_process.py --input-dir ./images --output-dir ./output --photoroom-api-key YOUR_API_KEY --shopify-api-key YOUR_SHOPIFY_API_KEY --shopify-password YOUR_SHOPIFY_PASSWORD --shopify-store your-store.myshopify.com
```

## Megjegyzések

- A PhotoRoom API-nak korlátai vannak, a kötegelt feldolgozás segít elkerülni a túlterhelést.
- A sandbox API kulcs használható teszteléshez (prefix: "sandbox_").
- A Plus API fejlettebb funkciókat kínál, de külön előfizetést igényel.
- A részletes API dokumentáció elérhető a [PhotoRoom weboldalán](https://docs.photoroom.com/image-editing-api-plus-plan).

## Hibaelhárítás

- Ha "API korlát elérve" hibát kapsz, próbáld meg a sandbox API kulcsot.
- Ha a Plus API funkciókat használod, győződj meg róla, hogy a megfelelő előfizetésed van.
- A debug mód (`--debug`) részletes információkat ad a hibákról.

## Licenc

MIT 