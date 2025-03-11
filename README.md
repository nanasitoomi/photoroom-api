# Photoroom API Tesztelő és Batch Feldolgozó

Ez a projekt a Photoroom API használatát mutatja be, beleértve a különböző paraméterek tesztelését és a batch feldolgozást.

## Projekt Struktúra

A projekt a következő fájlokat tartalmazza:

- **`photoroom_api_test.py`**: Egyszerű tesztfájl a Photoroom API alapvető használatához
- **`photoroom_api_params.py`**: Részletes szkript a Photoroom API különböző paramétereinek teszteléséhez
- **`batch_process.py`**: Batch feldolgozó szkript, amely nagy mennyiségű képet dolgoz fel és feltölti azokat Shopify-ra
- **`requirements.txt`**: A szükséges Python csomagok listája
- **`.cursorignore`**: Cursor szabályok a projekt fókuszának megtartásához

## Telepítés

A szükséges csomagok telepítéséhez futtasd a következő parancsot:

```bash
pip install -r requirements.txt
```

## Használat

### 1. Photoroom API Paraméterek Tesztelése

A `photoroom_api_params.py` szkript bemutatja a Photoroom API különböző paramétereit és azok hatását. A szkript 20 különböző paraméter-készletet tartalmaz, amelyek bemutatják a Photoroom API összes funkcióját.

```bash
./photoroom_api_params.py --image test.jpg --output-dir ./output
```

Opcionális paraméterek:
- `--use-live`: Live API használata (alapértelmezett: sandbox)
- `--debug`: Debug mód bekapcsolása (részletes információk)
- `--param-set N`: Csak egy adott paraméter-készlet futtatása (1-20)

#### Elérhető Paraméter-készletek:

1. **Alap háttér eltávolítás**: Átlátszó háttér
2. **Különböző formátumok**: PNG, JPG, WebP
3. **Háttérszínek**: Fehér, #EEEEE5, Fekete
4. **Árnyékok**: Lágy AI árnyék, Természetes árnyék
5. **Pozícionálás és méretezés**: Középre igazítás, 13%-os méretezés
6. **Shopify méretek**: Portré (4:5), Négyzet (1:1)
7. **Vágás**: Portré és négyzet automatikus vágással
8. **Minőség beállítások**: Magas (100%), Alacsony (50%)
9. **Egyedi méretezés**: 800x600 pixel
10. **Egyedi háttérkép**: Háttér elmosás (10 pixel)
11. **Teljes beállítás**: Shopify-ra optimalizált beállítások

### 2. Egyszerű API Teszt

A `photoroom_api_test.py` szkript egy egyszerű példát mutat a Photoroom API használatára:

```bash
./photoroom_api_test.py --image test.jpg --output output/result.png --api-key YOUR_API_KEY
```

### 3. Batch Feldolgozás

A `batch_process.py` szkript nagy mennyiségű képet dolgoz fel és feltölti azokat Shopify-ra:

```bash
./batch_process.py --input-dir /path/to/images --output-dir /path/to/output --batch-size 10 --photoroom-api-key YOUR_PHOTOROOM_API_KEY --shopify-api-key YOUR_SHOPIFY_API_KEY --shopify-password YOUR_SHOPIFY_PASSWORD --shopify-store your-store.myshopify.com
```

## API Kulcsok

A projektben a következő API kulcsokat használjuk:

- **Live API kulcs**: `6e69e09db21879242dd351cc16c526c8fe2053b1`
- **Sandbox API kulcs**: `sandbox_6e69e09db21879242dd351cc16c526c8fe2053b1`

A sandbox API kulcs használata javasolt teszteléshez, mivel ez nem számít bele a fizetős API hívásokba.

## Dokumentáció

A Photoroom API hivatalos dokumentációja: [https://www.photoroom.com/api/docs/reference/b0fb6beb9cd7e-photoroom-api](https://www.photoroom.com/api/docs/reference/b0fb6beb9cd7e-photoroom-api)

## Megjegyzések

- A szkriptek végrehajthatóvá lettek téve a `chmod +x` paranccsal, így közvetlenül futtathatók a terminálból.
- A debug mód (`--debug`) részletes információkat jelenít meg a feldolgozás során, beleértve a fájlméretet, a tömörítési arányt, a feldolgozási időt és a válasz fejléceket.
- A Photoroom API fizetős szolgáltatás, a használat előtt ellenőrizd a díjszabást és a korlátokat. 