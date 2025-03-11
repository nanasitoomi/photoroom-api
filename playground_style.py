#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PhotoRoom API v2 Batch Processor

Ez a szkript a PhotoRoom API v2 végpontját használja a képek feldolgozásához
a következő paraméterekkel:
- Háttérszín: F2F2F2FF (világosszürke)
- Kimeneti méret: 1600x2000 (utólagos átméretezéssel)
- Padding: 0.1
- Árnyék: ai.soft

Használat:
    python playground_style.py --input-dir input --output-dir output/playground_style --api-key YOUR_API_KEY
"""

import os
import sys
import requests
import argparse
import logging
import concurrent.futures
from pathlib import Path
from PIL import Image
import io

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("playground_style.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='PhotoRoom API v2 Batch Processor')
    parser.add_argument('--input-dir', required=True, help='Bemeneti képek mappája')
    parser.add_argument('--output-dir', required=True, help='Kimeneti képek mappája')
    parser.add_argument('--api-key', required=True, help='PhotoRoom API kulcs')
    parser.add_argument('--batch-size', type=int, default=5, help='Köteg mérete (alapértelmezett: 5)')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása')
    return parser.parse_args()

def resize_image(image_data, target_width=1600, target_height=2000):
    """
    Átméretezi a képet a megadott méretre
    """
    # Kép betöltése a memóriából
    img = Image.open(io.BytesIO(image_data))
    
    # Átméretezés a célméretre, megtartva a képarányt és kitöltve a hátteret
    img_ratio = img.width / img.height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        # A kép szélesebb, mint a célméret aránya
        new_width = target_width
        new_height = int(new_width / img_ratio)
    else:
        # A kép magasabb, mint a célméret aránya
        new_height = target_height
        new_width = int(new_height * img_ratio)
    
    # Átméretezés
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Új kép létrehozása a célmérettel
    new_img = Image.new('RGBA', (target_width, target_height), (242, 242, 242, 255))
    
    # A méretezett kép elhelyezése középen
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    new_img.paste(resized_img, (paste_x, paste_y))
    
    # Kép visszaadása bájt formátumban
    output = io.BytesIO()
    new_img.save(output, format='PNG')
    return output.getvalue()

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
        'size': 'original',
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
            
            response = requests.post(url, files=files, data=params, headers=headers)
            
            # Válasz ellenőrzése
            if response.status_code == 200:
                # Kép átméretezése
                if debug:
                    logger.debug(f"Kép átméretezése 1600x2000 pixelre")
                
                resized_image_data = resize_image(response.content)
                
                # Sikeres válasz esetén mentjük a képet
                with open(output_path, 'wb') as f:
                    f.write(resized_image_data)
                
                logger.info(f"Kép sikeresen feldolgozva, átméretezve és mentve: {output_path}")
                return True
            else:
                logger.error(f"API hiba ({response.status_code}): {response.text}")
                return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False

def process_batch(image_paths, output_dir, api_key, debug=False):
    """
    Feldolgoz egy köteg képet
    """
    results = []
    
    for image_path in image_paths:
        try:
            # Kimeneti fájlnév előkészítése
            filename = os.path.basename(image_path)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}.png")
            
            # Kép feldolgozása
            success = process_image(image_path, output_path, api_key, debug)
            results.append((image_path, success))
        except Exception as e:
            logger.error(f"Kivétel a kép feldolgozása során: {image_path} - {str(e)}")
            results.append((image_path, False))
    
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
    
    # Képek feldolgozása kötegekben
    batch_size = args.batch_size
    batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
    
    logger.info(f"Képek feldolgozása {len(batches)} kötegben, kötegenként {batch_size} kép")
    
    total_success = 0
    total_error = 0
    
    # Párhuzamos feldolgozás ThreadPoolExecutor-ral
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        
        for i, batch in enumerate(batches):
            logger.info(f"Köteg feldolgozása: {i+1}/{len(batches)}")
            
            future = executor.submit(
                process_batch, 
                batch, 
                args.output_dir, 
                args.api_key,
                args.debug
            )
            
            futures.append(future)
        
        # Eredmények összegyűjtése
        for future in concurrent.futures.as_completed(futures):
            batch_results = future.result()
            
            for image_path, success in batch_results:
                if success:
                    total_success += 1
                else:
                    total_error += 1
    
    # Összesítés
    logger.info("Feldolgozás befejezve")
    logger.info(f"Összesen {len(image_paths)} kép feldolgozva")
    logger.info(f"Sikeres feldolgozás: {total_success}")
    logger.info(f"Sikertelen feldolgozás: {total_error}")

if __name__ == "__main__":
    main() 