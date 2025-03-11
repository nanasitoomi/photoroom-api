#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photoroom API Paraméterek Tesztelése

Ez a szkript bemutatja a Photoroom API különböző paramétereit és azok hatását.
Egy képet küld az API-nak különböző beállításokkal, és elmenti az eredményeket.

A hivatalos API dokumentáció alapján: https://docs.photoroom.com/image-editing-api-plus-plan
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
    parser.add_argument('--param-set', type=int, help='Csak egy adott paraméter-készlet futtatása (1-35)')
    parser.add_argument('--use-plus', action='store_true', help='Plus API használata (v2 API)')
    parser.add_argument('--bg-image', help='Háttérkép elérési útja a bg_image paraméterhez')
    return parser.parse_args()

def process_image_with_params(image_path, output_path, api_key, params, debug=False, use_plus=False, bg_image_path=None):
    """
    Feldolgozza a képet a Photoroom API-val a megadott paraméterekkel
    """
    logger.info(f"Kép feldolgozása: {image_path} - Paraméterek: {params}")
    
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
        # Bezárjuk a fájlokat, ha sikerült megnyitni
        if 'files' in locals():
            for key in files:
                if hasattr(files[key][1], 'close'):
                    files[key][1].close()

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
    
    # API verzió kiválasztása
    if args.use_plus:
        logger.info("Plus API (v2) használata")
    else:
        logger.info("Alap API (v1) használata")
    
    # Fájlnév előkészítése
    filename = Path(args.image).stem
    
    # Különböző paraméter kombinációk tesztelése
    # A hivatalos API dokumentáció alapján: https://docs.photoroom.com/image-editing-api-plus-plan
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
        },
        
        # 12. Különböző minőségi szintek
        {
            'name': '21_medium_quality',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '13',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp',
                'quality': '75'
            },
            'description': 'Közepes minőség (75%)'
        },
        
        # 13. Különböző méretezési értékek
        {
            'name': '22_scale_50percent',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '50',
                'format': 'webp'
            },
            'description': '50%-os méretezés'
        },
        
        # 14. Háttér elmosás különböző értékekkel
        {
            'name': '23_bg_blur_20',
            'params': {
                'bg_blur': '20',
                'format': 'webp'
            },
            'description': 'Háttér elmosás (20 pixel)'
        },
        
        # 15. Kombinált beállítások
        {
            'name': '24_combined_params',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'scale': '25',
                'size': 'portrait',
                'crop': 'true',
                'format': 'webp',
                'quality': '85'
            },
            'description': 'Kombinált paraméterek (25% méret, 85% minőség)'
        },
        
        # 16. Egyedi méretezés más arányokkal
        {
            'name': '25_custom_size_wide',
            'params': {
                'bg_color': '#EEEEE5',
                'shadow': 'soft',
                'position': 'center',
                'width': '1200',
                'height': '600',
                'format': 'webp'
            },
            'description': 'Egyedi széles méret (1200x600 pixel)'
        },
        
        # Plus API (v2) specifikus paraméterek
        # 17. HD háttér eltávolítás
        {
            'name': '26_hd_removal',
            'params': {
                'hd': 'true',
                'format': 'webp'
            },
            'description': 'HD háttér eltávolítás',
            'plus_only': True
        },
        
        # 18. Egyedi DPI beállítás
        {
            'name': '27_custom_dpi',
            'params': {
                'bg_color': '#EEEEE5',
                'dpi': '300',
                'format': 'webp'
            },
            'description': 'Egyedi DPI beállítás (300)',
            'plus_only': True
        },
        
        # 19. AI generált háttér
        {
            'name': '28_ai_background_photo',
            'params': {
                'bg_prompt': 'A beautiful beach at sunset',
                'bg_style': 'photographic',
                'format': 'webp'
            },
            'description': 'AI generált fotorealisztikus háttér',
            'plus_only': True
        },
        
        # 20. AI generált háttér - flat color
        {
            'name': '29_ai_background_flat',
            'params': {
                'bg_prompt': 'A simple blue background',
                'bg_style': 'flat_color',
                'format': 'webp'
            },
            'description': 'AI generált egyszínű háttér',
            'plus_only': True
        },
        
        # 21. AI generált háttér - gradient
        {
            'name': '30_ai_background_gradient',
            'params': {
                'bg_prompt': 'A blue to purple gradient',
                'bg_style': 'gradient',
                'format': 'webp'
            },
            'description': 'AI generált színátmenetes háttér',
            'plus_only': True
        },
        
        # 22. AI generált háttér - pattern
        {
            'name': '31_ai_background_pattern',
            'params': {
                'bg_prompt': 'A geometric pattern with blue and yellow',
                'bg_style': 'pattern',
                'format': 'webp'
            },
            'description': 'AI generált mintás háttér',
            'plus_only': True
        },
        
        # 23. AI újravilágítás
        {
            'name': '32_relight',
            'params': {
                'relight': 'true',
                'relight_direction': 'left',
                'relight_strength': 'medium',
                'format': 'webp'
            },
            'description': 'AI újravilágítás (balról, közepes erősség)',
            'plus_only': True
        },
        
        # 24. Szöveg eltávolítás
        {
            'name': '33_remove_text',
            'params': {
                'remove_text': 'true',
                'format': 'webp'
            },
            'description': 'Szöveg eltávolítás a képről',
            'plus_only': True
        },
        
        # 25. Kép kiterjesztés
        {
            'name': '34_expand',
            'params': {
                'expand': 'true',
                'expand_factor': '1.5',
                'format': 'webp'
            },
            'description': 'Kép kiterjesztés (1.5x)',
            'plus_only': True
        },
        
        # 26. AI felskálázás
        {
            'name': '35_upscale',
            'params': {
                'upscale': 'true',
                'upscale_factor': '2',
                'format': 'webp'
            },
            'description': 'AI felskálázás (2x)',
            'plus_only': True
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
    skipped_count = 0
    start_total_time = time.time()
    
    for i, param_set in enumerate(param_sets):
        # Ellenőrizzük, hogy a paraméter-készlet csak a Plus API-val használható-e
        if param_set.get('plus_only', False) and not args.use_plus:
            logger.warning(f"Paraméter-készlet kihagyva (csak Plus API): {param_set['name']} - {param_set['description']}")
            skipped_count += 1
            continue
        
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
        result = process_image_with_params(
            args.image, 
            output_path, 
            api_key, 
            param_set['params'], 
            args.debug, 
            args.use_plus and param_set.get('plus_only', False),
            args.bg_image if 'bg_image' in param_set['params'] else None
        )
        process_time = time.time() - start_time
        
        if args.debug:
            logger.debug(f"Feldolgozási idő: {process_time:.2f} másodperc")
        
        if result:
            success_count += 1
        else:
            error_count += 1
    
    total_time = time.time() - start_total_time
    logger.info(f"Minden paraméter teszt befejezve. Sikeres: {success_count}, Hibás: {error_count}, Kihagyott: {skipped_count}")
    logger.info(f"Teljes futási idő: {total_time:.2f} másodperc")
    
    if args.debug:
        processed_count = success_count + error_count
        if processed_count > 0:
            logger.debug(f"Átlagos feldolgozási idő: {total_time/processed_count:.2f} másodperc/kép")
    
    if error_count > 0 and args.use_live:
        logger.warning("Hibák történtek a feldolgozás során. Próbáld meg a sandbox API-val a --use-live kapcsoló nélkül.")
    
    if skipped_count > 0 and not args.use_plus:
        logger.warning(f"{skipped_count} paraméter-készlet kihagyva, mert csak a Plus API-val használható. Használd a --use-plus kapcsolót a tesztelésükhöz.")

if __name__ == "__main__":
    main() 