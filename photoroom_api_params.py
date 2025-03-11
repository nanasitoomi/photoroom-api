#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photoroom API Paraméterek Tesztelése

Ez a szkript bemutatja a Photoroom API különböző paramétereit és azok hatását.
Egy képet küld az API-nak különböző beállításokkal, és elmenti az eredményeket.

A hivatalos API dokumentáció alapján: https://www.photoroom.com/api/docs/reference/b0fb6beb9cd7e-photoroom-api
"""

import os
import sys
import requests
import argparse
import logging
import json
import time
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API kulcsok
LIVE_API_KEY = "6e69e09db21879242dd351cc16c526c8fe2053b1"
SANDBOX_API_KEY = "sandbox_6e69e09db21879242dd351cc16c526c8fe2053b1"

def parse_args():
    parser = argparse.ArgumentParser(description='Photoroom API Paraméterek Tesztelése')
    parser.add_argument('--image', required=True, help='A feldolgozandó kép elérési útja')
    parser.add_argument('--output-dir', required=True, help='A kimeneti képek mappája')
    parser.add_argument('--use-live', action='store_true', help='Live API használata (alapértelmezett: sandbox)')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása (részletes információk)')
    parser.add_argument('--param-set', type=int, help='Csak egy adott paraméter-készlet futtatása (1-20)')
    return parser.parse_args()

def process_image_with_params(image_path, output_path, api_key, params, debug=False):
    """
    Feldolgozza a képet a Photoroom API-val a megadott paraméterekkel
    """
    logger.info(f"Kép feldolgozása: {image_path} - Paraméterek: {params}")
    
    # API végpont
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
        
        # Fejlécek beállítása
        headers = {
            'x-api-key': api_key
        }
        
        if debug:
            logger.debug(f"API végpont: {url}")
            logger.debug(f"Fejlécek: {headers}")
            logger.debug(f"Paraméterek: {params}")
        
        # API kérés küldése
        logger.info("API kérés küldése...")
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
                    logger.error("Próbáld meg a sandbox API-val a --use-live kapcsoló nélkül.")
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
        # Bezárjuk a fájlt, ha sikerült megnyitni
        if 'files' in locals() and 'image_file' in files and hasattr(files['image_file'][1], 'close'):
            files['image_file'][1].close()

def main():
    args = parse_args()
    
    # Debug mód beállítása
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mód bekapcsolva")
        logger.debug(f"Parancssori argumentumok: {args}")
    
    # Ellenőrizzük, hogy a bemeneti fájl létezik-e
    if not os.path.isfile(args.image):
        logger.error(f"A bemeneti fájl nem létezik: {args.image}")
        sys.exit(1)
    
    # Ellenőrizzük, hogy a kimeneti mappa létezik-e
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        logger.info(f"Kimeneti mappa létrehozása: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # API kulcs kiválasztása - alapértelmezetten a sandbox
    api_key = LIVE_API_KEY if args.use_live else SANDBOX_API_KEY
    logger.info(f"Használt API kulcs: {'Live' if args.use_live else 'Sandbox'}")
    
    # Fájlnév előkészítése
    filename = Path(args.image).stem
    
    # Különböző paraméter kombinációk tesztelése
    # A hivatalos API dokumentáció alapján: https://www.photoroom.com/api/docs/reference/b0fb6beb9cd7e-photoroom-api
    param_sets = [
        # 1. Alap háttér eltávolítás - átlátszó háttér
        {
            'name': '01_alap_atlatszo',
            'params': {},
            'description': 'Alap háttér eltávolítás átlátszó háttérrel'
        },
        
        # 2. Különböző formátumok
        {
            'name': '02_png_format',
            'params': {
                'format': 'png'
            },
            'description': 'PNG formátum (átlátszó háttér támogatással)'
        },
        {
            'name': '03_jpg_format',
            'params': {
                'format': 'jpg'
            },
            'description': 'JPG formátum (tömörített, átlátszóság nélkül)'
        },
        {
            'name': '04_webp_format',
            'params': {
                'format': 'webp'
            },
            'description': 'WebP formátum (modern, jó tömörítés, átlátszóság támogatással)'
        },
        
        # 3. Háttérszínek
        {
            'name': '05_feher_hatter',
            'params': {
                'bg_color': '#FFFFFF',
                'format': 'webp'
            },
            'description': 'Fehér háttér (#FFFFFF)'
        },
        {
            'name': '06_eeeee5_hatter',
            'params': {
                'bg_color': '#EEEEE5',
                'format': 'webp'
            },
            'description': 'Világos bézs háttér (#EEEEE5)'
        },
        {
            'name': '07_fekete_hatter',
            'params': {
                'bg_color': '#000000',
                'format': 'webp'
            },
            'description': 'Fekete háttér (#000000)'
        },
        
        # 4. Árnyékok
        {
            'name': '08_soft_shadow',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'format': 'webp'
            },
            'description': 'Lágy AI árnyék'
        },
        {
            'name': '09_natural_shadow',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'natural',
                'format': 'webp'
            },
            'description': 'Természetes árnyék'
        },
        
        # 5. Pozícionálás és méretezés
        {
            'name': '10_center_position',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'format': 'webp'
            },
            'description': 'Középre igazítás'
        },
        {
            'name': '11_scale_13percent',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'format': 'webp'
            },
            'description': '13%-os méretezés'
        },
        
        # 6. Shopify méretek
        {
            'name': '12_shopify_portrait',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'format': 'webp'
            },
            'description': 'Shopify portré méret (4:5 arány)'
        },
        {
            'name': '13_shopify_square',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'square',
                'format': 'webp'
            },
            'description': 'Shopify négyzet méret (1:1 arány)'
        },
        
        # 7. Vágás
        {
            'name': '14_portrait_crop',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp'
            },
            'description': 'Portré méret automatikus vágással'
        },
        {
            'name': '15_square_crop',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'square',
                'crop': 'true',
                'format': 'webp'
            },
            'description': 'Négyzet méret automatikus vágással'
        },
        
        # 8. Minőség beállítások
        {
            'name': '16_high_quality',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp',
                'quality': '100'
            },
            'description': 'Magas minőség (100%)'
        },
        {
            'name': '17_low_quality',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp',
                'quality': '50'
            },
            'description': 'Alacsony minőség (50%)'
        },
        
        # 9. Egyedi méretezés
        {
            'name': '18_custom_size',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'width': '800',
                'height': '600',
                'format': 'webp'
            },
            'description': 'Egyedi méret (800x600 pixel)'
        },
        
        # 10. Egyedi háttérkép
        {
            'name': '19_bg_blur',
            'params': {
                'bg_blur': '10',
                'format': 'webp'
            },
            'description': 'Háttér elmosás (10 pixel)'
        },
        
        # 11. Teljes beállítás - Shopify optimalizált
        {
            'name': '20_shopify_optimalizalt',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp',
                'quality': '90'
            },
            'description': 'Shopify-ra optimalizált beállítások'
        }
    ]
    
    # Ha csak egy adott paraméter-készletet kell futtatni
    if args.param_set is not None:
        if 1 <= args.param_set <= len(param_sets):
            selected_param_set = param_sets[args.param_set - 1]
            logger.info(f"Csak a(z) {args.param_set}. paraméter-készlet futtatása: {selected_param_set['name']} - {selected_param_set['description']}")
            param_sets = [selected_param_set]
        else:
            logger.error(f"Érvénytelen paraméter-készlet szám: {args.param_set}. Érvényes értékek: 1-{len(param_sets)}")
            sys.exit(1)
    
    # Paraméterek tesztelése
    success_count = 0
    error_count = 0
    start_total_time = time.time()
    
    for i, param_set in enumerate(param_sets):
        if args.debug:
            logger.debug(f"Paraméter-készlet {i+1}/{len(param_sets)}: {param_set['name']} - {param_set['description']}")
        else:
            logger.info(f"Paraméter teszt: {param_set['name']} - {param_set['description']}")
        
        output_path = os.path.join(output_dir, f"{filename}_{param_set['name']}")
        
        # Formátum hozzáadása a fájlnévhez, ha nincs megadva
        if 'format' in param_set['params']:
            output_path += f".{param_set['params']['format']}"
        else:
            output_path += ".png"  # Alapértelmezett PNG formátum
        
        # Feldolgozás időmérése
        start_time = time.time()
        result = process_image_with_params(args.image, output_path, api_key, param_set['params'], args.debug)
        process_time = time.time() - start_time
        
        if args.debug:
            logger.debug(f"Feldolgozási idő: {process_time:.2f} másodperc")
        
        if result:
            success_count += 1
        else:
            error_count += 1
    
    total_time = time.time() - start_total_time
    logger.info(f"Minden paraméter teszt befejezve. Sikeres: {success_count}, Hibás: {error_count}")
    logger.info(f"Teljes futási idő: {total_time:.2f} másodperc")
    
    if args.debug:
        logger.debug(f"Átlagos feldolgozási idő: {total_time/len(param_sets):.2f} másodperc/kép")
    
    if error_count > 0 and args.use_live:
        logger.warning("Hibák történtek a feldolgozás során. Próbáld meg a sandbox API-val a --use-live kapcsoló nélkül.")

if __name__ == "__main__":
    main() 