#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PhotoRoom API v2 Batch Processor - Sample Version

Ez a szkript a PhotoRoom API v2 végpontját használja a képek feldolgozásához
a következő paraméterekkel:
- Háttérszín: F2F2F2FF (világosszürke)
- Kimeneti méret: 1600x2000 (fix méret)
- Padding: 0.1
- Árnyék: ai.soft

Ez a verzió csak néhány kiválasztott képet dolgoz fel a Batch_8 mappából.

Használat:
    python playground_style_sample.py --input-dir input/Batch_8 --output-dir output/playground_style_sample --api-key YOUR_API_KEY
"""

import os
import sys
import requests
import argparse
import logging
import time
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("playground_style_sample.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='PhotoRoom API v2 Batch Processor - Sample Version')
    parser.add_argument('--input-dir', required=True, help='Bemeneti képek mappája')
    parser.add_argument('--output-dir', required=True, help='Kimeneti képek mappája')
    parser.add_argument('--api-key', required=True, help='PhotoRoom API kulcs')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása')
    parser.add_argument('--limit', type=int, default=5, help='Feldolgozandó képek maximális száma')
    return parser.parse_args()

def process_image(image_path, output_path, api_key, debug=False):
    """
    Feldolgozza a képet a PhotoRoom API v2 végpontjával
    """
    if debug:
        logger.debug(f"Kép feldolgozása: {image_path}")
    else:
        logger.info(f"Kép feldolgozása: {image_path}")
    
    # API paraméterek
    params = {
        'background.color': 'F2F2F2FF',
        'width': '1600',
        'height': '2000',
        'padding': '0.1',
        'shadow.mode': 'ai.soft'
    }
    
    # Fejlécek beállítása
    headers = {
        'x-api-key': api_key
    }
    
    try:
        # Fájl megnyitása
        with open(image_path, 'rb') as image_file:
            files = {
                'imageFile': (os.path.basename(image_path), image_file, 'image/jpeg')
            }
            
            # API kérés küldése
            url = "https://image-api.photoroom.com/v2/edit"
            if debug:
                logger.debug(f"API kérés küldése: {url}")
                logger.debug(f"Paraméterek: {params}")
            
            start_time = time.time()
            response = requests.post(url, files=files, data=params, headers=headers)
            end_time = time.time()
            
            # Válasz ellenőrzése
            if response.status_code == 200:
                # Sikeres válasz esetén mentjük a képet
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Kép sikeresen feldolgozva és mentve: {output_path}")
                logger.info(f"Feldolgozási idő: {end_time - start_time:.2f} másodperc")
                return True
            else:
                logger.error(f"API hiba ({response.status_code}): {response.text}")
                return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False

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
    
    # Kiválasztunk néhány reprezentatív képet
    # Különböző típusú termékek képeit választjuk ki
    selected_images = []
    product_types = set()
    
    for image_path in image_paths:
        filename = os.path.basename(image_path)
        # Termék típus kinyerése a fájlnévből (pl. "Sierra Tequila", "Jim Beam", stb.)
        parts = filename.split('-')
        if len(parts) > 1:
            product_type = parts[1].strip()
            if product_type not in product_types and len(selected_images) < args.limit:
                product_types.add(product_type)
                selected_images.append(image_path)
                logger.info(f"Kiválasztott kép: {filename}")
    
    # Ha nem sikerült elég képet kiválasztani, akkor veszünk még néhányat
    if len(selected_images) < args.limit:
        remaining = args.limit - len(selected_images)
        for image_path in image_paths:
            if image_path not in selected_images and remaining > 0:
                selected_images.append(image_path)
                remaining -= 1
                logger.info(f"További kiválasztott kép: {os.path.basename(image_path)}")
    
    logger.info(f"Összesen {len(selected_images)} kép került kiválasztásra feldolgozásra")
    
    # Képek feldolgozása
    total_success = 0
    total_error = 0
    
    for image_path in selected_images:
        try:
            # Kimeneti fájlnév előkészítése
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(args.output_dir, f"{name}.png")
            
            # Kép feldolgozása
            success = process_image(image_path, output_path, args.api_key, args.debug)
            
            if success:
                total_success += 1
            else:
                total_error += 1
        except Exception as e:
            logger.error(f"Kivétel a kép feldolgozása során: {image_path} - {str(e)}")
            total_error += 1
    
    # Összesítés
    logger.info("Feldolgozás befejezve")
    logger.info(f"Összesen {len(selected_images)} kép feldolgozva")
    logger.info(f"Sikeres feldolgozás: {total_success}")
    logger.info(f"Sikertelen feldolgozás: {total_error}")

if __name__ == "__main__":
    main() 