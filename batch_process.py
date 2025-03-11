#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photoroom API Batch Processor és Shopify Uploader

Ez a szkript képek kötegelt feldolgozását végzi a Photoroom API segítségével,
majd opcionálisan feltölti a feldolgozott képeket a Shopify-ra.

Funkciók:
1. Háttér eltávolítása és új háttér hozzáadása a Photoroom API-val
2. Feldolgozott képek mentése WebP formátumban
3. Feldolgozott képek feltöltése a Shopify-ra

Használat:
    python batch_process.py --input-dir /path/to/images --output-dir /path/to/output --batch-size 10 --photoroom-api-key YOUR_API_KEY [további opciók]

További opciók:
    --shopify-api-key YOUR_API_KEY - Shopify API kulcs (opcionális)
    --shopify-password YOUR_PASSWORD - Shopify jelszó (opcionális)
    --shopify-store your-store.myshopify.com - Shopify bolt URL (opcionális)
    --use-plus - Plus API használata (v2 API) a speciális funkciókhoz
    --bg-color #EEEEE5 - Háttérszín (alapértelmezett: #EEEEE5)
    --shadow soft - Árnyék típusa (soft/natural, alapértelmezett: soft)
    --position center - Pozíció (alapértelmezett: center)
    --scale 13 - Méretezés százalékban (alapértelmezett: 13)
    --size portrait - Méret (portrait/square, alapértelmezett: portrait)
    --crop - Automatikus vágás (alapértelmezett: bekapcsolva)
    --quality 90 - Minőség (1-100, alapértelmezett: 90)
    --format webp - Formátum (png/jpg/webp, alapértelmezett: webp)
    --hd - HD háttér eltávolítás (csak Plus API)
    --dpi 300 - DPI beállítás (csak Plus API)
    --bg-prompt "prompt" - AI generált háttér prompt (csak Plus API)
    --bg-style photographic - AI generált háttér stílusa (photographic/flat_color/gradient/pattern, csak Plus API)
    --relight - AI újravilágítás (csak Plus API)
    --relight-direction front - Fény iránya (front/left/right/top, csak Plus API)
    --relight-strength medium - Fény erőssége (low/medium/high, csak Plus API)
    --remove-text - Szöveg eltávolítása (csak Plus API)
    --expand - Kép kiterjesztése (csak Plus API)
    --expand-factor 1.5 - Kiterjesztés mértéke (csak Plus API)
    --upscale - AI felskálázás (csak Plus API)
    --upscale-factor 2 - Felskálázás mértéke (csak Plus API)
    --bg-image /path/to/image - Egyedi háttérkép (csak Plus API)
    --bg-image-url URL - Egyedi háttérkép URL (csak Plus API)
    --debug - Debug mód bekapcsolása
"""

import os
import sys
import requests
import argparse
import logging
import json
import time
import concurrent.futures
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_process.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Photoroom API Batch Processor és Shopify Uploader')
    parser.add_argument('--input-dir', required=True, help='Bemeneti képek mappája')
    parser.add_argument('--output-dir', required=True, help='Kimeneti képek mappája')
    parser.add_argument('--batch-size', type=int, default=10, help='Köteg mérete (alapértelmezett: 10)')
    parser.add_argument('--photoroom-api-key', required=True, help='Photoroom API kulcs')
    parser.add_argument('--shopify-api-key', help='Shopify API kulcs (opcionális)')
    parser.add_argument('--shopify-password', help='Shopify jelszó (opcionális)')
    parser.add_argument('--shopify-store', help='Shopify bolt URL (opcionális)')
    
    # Photoroom API paraméterek
    parser.add_argument('--bg-color', default='#EEEEE5', help='Háttérszín (alapértelmezett: #EEEEE5)')
    parser.add_argument('--shadow', default='soft', choices=['soft', 'natural', 'none'], help='Árnyék típusa (soft/natural/none, alapértelmezett: soft)')
    parser.add_argument('--position', default='center', help='Pozíció (alapértelmezett: center)')
    parser.add_argument('--scale', default='13', help='Méretezés százalékban (alapértelmezett: 13)')
    parser.add_argument('--size', default='portrait', choices=['portrait', 'square', 'original'], help='Méret (portrait/square/original, alapértelmezett: portrait)')
    parser.add_argument('--crop', action='store_true', help='Automatikus vágás (alapértelmezett: kikapcsolva)')
    parser.add_argument('--quality', default='90', help='Minőség (1-100, alapértelmezett: 90)')
    parser.add_argument('--format', default='webp', choices=['png', 'jpg', 'webp'], help='Formátum (png/jpg/webp, alapértelmezett: webp)')
    
    # Plus API specifikus paraméterek
    parser.add_argument('--use-plus', action='store_true', help='Plus API használata (v2 API)')
    parser.add_argument('--hd', action='store_true', help='HD háttér eltávolítás (csak Plus API)')
    parser.add_argument('--dpi', help='DPI beállítás (csak Plus API)')
    parser.add_argument('--bg-prompt', help='AI generált háttér prompt (csak Plus API)')
    parser.add_argument('--bg-style', choices=['photographic', 'flat_color', 'gradient', 'pattern'], help='AI generált háttér stílusa (csak Plus API)')
    parser.add_argument('--relight', action='store_true', help='AI újravilágítás (csak Plus API)')
    parser.add_argument('--relight-direction', choices=['front', 'left', 'right', 'top'], default='front', help='Fény iránya (csak Plus API)')
    parser.add_argument('--relight-strength', choices=['low', 'medium', 'high'], default='medium', help='Fény erőssége (csak Plus API)')
    parser.add_argument('--remove-text', action='store_true', help='Szöveg eltávolítása (csak Plus API)')
    parser.add_argument('--expand', action='store_true', help='Kép kiterjesztése (csak Plus API)')
    parser.add_argument('--expand-factor', default='1.2', help='Kiterjesztés mértéke (csak Plus API)')
    parser.add_argument('--upscale', action='store_true', help='AI felskálázás (csak Plus API)')
    parser.add_argument('--upscale-factor', choices=['2', '4'], default='2', help='Felskálázás mértéke (csak Plus API)')
    parser.add_argument('--bg-image', help='Egyedi háttérkép elérési útja (csak Plus API)')
    parser.add_argument('--bg-image-url', help='Egyedi háttérkép URL (csak Plus API)')
    
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása')
    return parser.parse_args()

def process_image_with_photoroom(image_path, output_path, api_key, params, debug=False, use_plus=False, bg_image_path=None):
    """
    Feldolgozza a képet a Photoroom API-val a megadott paraméterekkel
    """
    if debug:
        logger.debug(f"Kép feldolgozása: {image_path} - Paraméterek: {params}")
    else:
        logger.info(f"Kép feldolgozása: {image_path}")
    
    # API végpont kiválasztása (v1 vagy v2)
    if use_plus:
        url = "https://api.photoroom.com/v2/edit"
    else:
        url = "https://sdk.photoroom.com/v1/segment"
    
    # Fájl előkészítése
    try:
        # Fájl méretének ellenőrzése
        file_size = os.path.getsize(image_path) / 1024  # KB-ban
        if debug:
            logger.debug(f"Fájl mérete: {file_size:.2f} KB")
        
        # Fájl megnyitása
        files = {
            'image_file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')
        }
        
        # Ha van háttérkép, azt is hozzáadjuk
        if bg_image_path and os.path.isfile(bg_image_path):
            files['bg_image'] = (os.path.basename(bg_image_path), open(bg_image_path, 'rb'), 'image/jpeg')
            if debug:
                logger.debug(f"Háttérkép hozzáadva: {bg_image_path}")
        
        # Fejlécek beállítása
        headers = {
            'x-api-key': api_key
        }
        
        if debug:
            logger.debug(f"API végpont: {url}")
            logger.debug(f"Fejlécek: {headers}")
            logger.debug(f"Paraméterek: {params}")
        
        # API kérés küldése
        start_time = time.time()
        response = requests.post(url, files=files, data=params, headers=headers)
        request_time = time.time() - start_time
        
        if debug:
            logger.debug(f"Válasz státuszkód: {response.status_code}")
            logger.debug(f"Kérés időtartama: {request_time:.2f} másodperc")
            logger.debug(f"Válasz fejlécek: {response.headers}")
            
            # Kinyerjük a hasznos információkat a fejlécekből
            if 'x-uncertainty-score' in response.headers:
                logger.debug(f"Bizonytalansági pontszám: {response.headers.get('x-uncertainty-score')}")
            if 'x-foreground-top' in response.headers:
                logger.debug(f"Előtér pozíció - Felső: {response.headers.get('x-foreground-top')}")
            if 'x-foreground-left' in response.headers:
                logger.debug(f"Előtér pozíció - Bal: {response.headers.get('x-foreground-left')}")
            if 'x-foreground-height' in response.headers:
                logger.debug(f"Előtér méret - Magasság: {response.headers.get('x-foreground-height')}")
            if 'x-foreground-width' in response.headers:
                logger.debug(f"Előtér méret - Szélesség: {response.headers.get('x-foreground-width')}")
        
        # Ellenőrizzük a válasz státuszkódját
        if response.status_code == 200:
            # Sikeres válasz esetén mentjük a képet
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Kimeneti fájl méretének ellenőrzése
            output_size = os.path.getsize(output_path) / 1024  # KB-ban
            compression_ratio = (file_size / output_size) if output_size > 0 else 0
            
            logger.info(f"Kép sikeresen feldolgozva és mentve: {output_path}")
            
            if debug:
                logger.debug(f"Kimeneti fájl mérete: {output_size:.2f} KB")
                logger.debug(f"Tömörítési arány: {compression_ratio:.2f}x")
                logger.debug(f"Válasz tartalomtípus: {response.headers.get('Content-Type', 'ismeretlen')}")
            
            return True
        else:
            # Részletes hibaüzenet megjelenítése
            try:
                error_detail = json.loads(response.text)
                if response.status_code == 402:
                    logger.error(f"API korlát elérve (402): {error_detail.get('detail', 'Ismeretlen hiba')}")
                else:
                    logger.error(f"API hiba ({response.status_code}): {error_detail.get('detail', 'Ismeretlen hiba')}")
                
                if debug:
                    logger.debug(f"Teljes hibaválasz: {response.text}")
            except json.JSONDecodeError:
                logger.error(f"Hiba a feldolgozás során: {response.status_code} - {response.text}")
            return False
    except FileNotFoundError:
        logger.error(f"A fájl nem található: {image_path}")
        return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        if debug:
            import traceback
            logger.debug(f"Kivétel részletei: {traceback.format_exc()}")
        return False
    finally:
        # Bezárjuk a fájlokat, ha sikerült megnyitni
        if 'files' in locals():
            for key in files:
                if hasattr(files[key][1], 'close'):
                    files[key][1].close()

def upload_to_shopify(image_path, api_key, password, store):
    """
    Feltölti a képet a Shopify-ra
    """
    logger.info(f"Kép feltöltése a Shopify-ra: {image_path}")
    
    try:
        # Shopify API végpont
        url = f"https://{api_key}:{password}@{store}/admin/api/2023-07/products/images.json"
        
        # Fájl előkészítése
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Fájlnév kinyerése
        filename = os.path.basename(image_path)
        
        # Kérés adatok
        data = {
            "image": {
                "attachment": image_data.encode('base64').decode('utf-8'),
                "filename": filename
            }
        }
        
        # Kérés küldése
        response = requests.post(url, json=data)
        
        # Válasz ellenőrzése
        if response.status_code in [200, 201]:
            logger.info(f"Kép sikeresen feltöltve a Shopify-ra: {filename}")
            return True
        else:
            logger.error(f"Hiba a Shopify feltöltés során: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a Shopify feltöltés során: {str(e)}")
        return False

def process_batch(image_paths, output_dir, photoroom_api_key, params, shopify_api_key=None, shopify_password=None, shopify_store=None, debug=False, use_plus=False, bg_image_path=None):
    """
    Feldolgoz egy köteg képet
    """
    results = []
    
    for image_path in image_paths:
        try:
            # Kimeneti fájlnév előkészítése
            filename = os.path.basename(image_path)
            name, _ = os.path.splitext(filename)
            output_format = params.get('format', 'png')
            output_path = os.path.join(output_dir, f"{name}.{output_format}")
            
            # Kép feldolgozása a Photoroom API-val
            success = process_image_with_photoroom(image_path, output_path, photoroom_api_key, params, debug, use_plus, bg_image_path)
            
            if success:
                # Ha a Shopify feltöltés is kérve van
                if shopify_api_key and shopify_password and shopify_store:
                    shopify_success = upload_to_shopify(output_path, shopify_api_key, shopify_password, shopify_store)
                    results.append((image_path, success, shopify_success))
                else:
                    results.append((image_path, success, None))
            else:
                results.append((image_path, False, None))
        except Exception as e:
            logger.error(f"Kivétel a kép feldolgozása során: {image_path} - {str(e)}")
            results.append((image_path, False, None))
    
    return results

def main():
    args = parse_args()
    
    # Debug mód beállítása
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mód bekapcsolva")
        logger.debug(f"Parancssori argumentumok: {args}")
    
    # Ellenőrizzük, hogy a bemeneti mappa létezik-e
    if not os.path.isdir(args.input_dir):
        logger.error(f"A bemeneti mappa nem létezik: {args.input_dir}")
        sys.exit(1)
    
    # Ellenőrizzük, hogy a kimeneti mappa létezik-e
    if not os.path.exists(args.output_dir):
        logger.info(f"Kimeneti mappa létrehozása: {args.output_dir}")
        os.makedirs(args.output_dir, exist_ok=True)
    
    # Képek listázása a bemeneti mappából
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    image_paths = []
    
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_paths.append(os.path.join(root, file))
    
    if not image_paths:
        logger.error(f"Nem találhatók képek a bemeneti mappában: {args.input_dir}")
        sys.exit(1)
    
    logger.info(f"Összesen {len(image_paths)} kép található a bemeneti mappában")
    
    # Photoroom API paraméterek összeállítása
    params = {}
    
    # Alap paraméterek
    if args.bg_color:
        params['bg_color'] = args.bg_color
    
    if args.shadow and args.shadow != 'none':
        params['shadow'] = args.shadow
    
    if args.position:
        params['position'] = args.position
    
    if args.scale:
        params['scale'] = args.scale
    
    if args.size and args.size != 'original':
        params['size'] = args.size
    
    if args.crop:
        params['crop'] = 'true'
    
    if args.quality:
        params['quality'] = args.quality
    
    if args.format:
        params['format'] = args.format
    
    # Plus API specifikus paraméterek
    if args.use_plus:
        if args.hd:
            params['hd'] = 'true'
        
        if args.dpi:
            params['dpi'] = args.dpi
        
        if args.bg_prompt:
            params['bg_prompt'] = args.bg_prompt
            
            if args.bg_style:
                params['bg_style'] = args.bg_style
        
        if args.bg_image_url:
            params['bg_image_url'] = args.bg_image_url
        
        if args.relight:
            params['relight'] = 'true'
            params['relight_direction'] = args.relight_direction
            params['relight_strength'] = args.relight_strength
        
        if args.remove_text:
            params['remove_text'] = 'true'
        
        if args.expand:
            params['expand'] = 'true'
            params['expand_factor'] = args.expand_factor
        
        if args.upscale:
            params['upscale'] = 'true'
            params['upscale_factor'] = args.upscale_factor
    
    logger.info(f"Használt API paraméterek: {params}")
    
    # API verzió kiválasztása
    if args.use_plus:
        logger.info("Plus API (v2) használata")
    else:
        logger.info("Alap API (v1) használata")
    
    # Képek feldolgozása kötegekben
    batch_size = args.batch_size
    batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
    
    logger.info(f"Képek feldolgozása {len(batches)} kötegben, kötegenként {batch_size} kép")
    
    total_success = 0
    total_error = 0
    total_shopify_success = 0
    total_shopify_error = 0
    
    start_time = time.time()
    
    # Párhuzamos feldolgozás ThreadPoolExecutor-ral
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for i, batch in enumerate(batches):
            logger.info(f"Köteg feldolgozása: {i+1}/{len(batches)}")
            
            future = executor.submit(
                process_batch, 
                batch, 
                args.output_dir, 
                args.photoroom_api_key, 
                params,
                args.shopify_api_key, 
                args.shopify_password, 
                args.shopify_store,
                args.debug,
                args.use_plus,
                args.bg_image
            )
            
            futures.append(future)
        
        # Eredmények összegyűjtése
        for future in concurrent.futures.as_completed(futures):
            batch_results = future.result()
            
            for image_path, success, shopify_success in batch_results:
                if success:
                    total_success += 1
                else:
                    total_error += 1
                
                if shopify_success is not None:
                    if shopify_success:
                        total_shopify_success += 1
                    else:
                        total_shopify_error += 1
    
    total_time = time.time() - start_time
    
    # Összesítés
    logger.info("Feldolgozás befejezve")
    logger.info(f"Összesen {len(image_paths)} kép feldolgozva")
    logger.info(f"Sikeres Photoroom API feldolgozás: {total_success}")
    logger.info(f"Sikertelen Photoroom API feldolgozás: {total_error}")
    
    if args.shopify_api_key and args.shopify_password and args.shopify_store:
        logger.info(f"Sikeres Shopify feltöltés: {total_shopify_success}")
        logger.info(f"Sikertelen Shopify feltöltés: {total_shopify_error}")
    
    logger.info(f"Teljes futási idő: {total_time:.2f} másodperc")
    logger.info(f"Átlagos feldolgozási idő képenként: {total_time/len(image_paths):.2f} másodperc")

if __name__ == "__main__":
    main() 