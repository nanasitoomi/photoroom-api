# PhotoRoom API Scripts

Ez a projekt különböző szkripteket tartalmaz a PhotoRoom API használatához, amelyek segítségével képeket dolgozhatunk fel automatikusan.

## Telepítés

A szkriptek futtatásához a következő függőségekre van szükség:

```bash
pip install -r requirements.txt
```

## Szkriptek

### 1. photoroom_edit_script.py

Ez a szkript a PhotoRoom API v2 végpontját használja képek feldolgozásához a következő paraméterekkel:
- Háttér eltávolítás: bekapcsolva
- Háttérszín: EEEEEE (világos szürke)
- Kimeneti méret: 1600x2000
- Padding: 15%
- Szöveg eltávolítás: ai.all
- Árnyék: ai.soft
- Formátum: WebP
- Automatikus vágás: bekapcsolva
- Minőség: 80
- HD háttér eltávolítás: bekapcsolva
- Pixel sűrűség (DPI): 150
- Scaling: fit
- Centered: bekapcsolva

#### Használat

```bash
python photoroom_edit_script.py --input-file input/image.jpg --output-file output/result.webp --api-key YOUR_API_KEY
```

Paraméterek:
- `--input-file`: A feldolgozandó kép elérési útja
- `--output-file`: A kimeneti kép elérési útja (.webp kiterjesztéssel)
- `--api-key`: PhotoRoom API kulcs
- `--image-url`: (Opcionális) Kép URL-je, ha nem helyi fájlt szeretnénk feldolgozni
- `--debug`: (Opcionális) Debug mód bekapcsolása

A szkript automatikusan ellenőrzi, hogy a kimeneti fájl .webp kiterjesztésű-e, és ha nem, akkor átnevezi.

### 2. batch_process.py

Ez a szkript képek kötegelt feldolgozását végzi a Photoroom API segítségével, majd opcionálisan feltölti a feldolgozott képeket a Shopify-ra.

#### Használat

```bash
python batch_process.py --input-dir /path/to/images --output-dir /path/to/output --batch-size 10 --photoroom-api-key YOUR_API_KEY [további opciók]
```

További opciók és részletek a szkript dokumentációjában találhatók.

### 3. photoroom_api_params.py

Ez a szkript a PhotoRoom API különböző paramétereit teszteli, és az eredményeket menti.

#### Használat

```bash
python photoroom_api_params.py --input-file input/test.jpg --output-dir output/params_test --api-key YOUR_API_KEY [további opciók]
```

További opciók és részletek a szkript dokumentációjában találhatók.

## API Kulcsok

- Live API kulcs: 6e69e09db21879242dd351cc16c526c8fe2053b1
- Sandbox API kulcs: sandbox_6e69e09db21879242dd351cc16c526c8fe2053b1

## Dokumentáció

A PhotoRoom API hivatalos dokumentációja: https://www.photoroom.com/api/docs/reference/b0fb6beb9cd7e-photoroom-api 