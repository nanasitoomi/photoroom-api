#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PhotoRoom API v2 Single Image Processor

Ez a szkript a PhotoRoom API v2 végpontját használja egy kép feldolgozásához
a következő paraméterekkel:
- Háttérszín: F2F2F2FF (világosszürke)
- Kimeneti méret: 1600x2000 (fix méret)
- Padding: 0.1
- Árnyék: ai.soft

Használat:
    python playground_style_single.py --input-file input/Batch_8/FILENAME.jpg --output-file output/result.png --api-key YOUR_API_KEY
"""

import os
import sys
import requests
import argparse
import logging
import time

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("playground_style_single.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='PhotoRoom API v2 Single Image Processor')
    parser.add_argument('--input-file', required=True, help='Bemeneti kép elérési útja')
    parser.add_argument('--output-file', required=True, help='Kimeneti kép elérési útja')
    parser.add_argument('--api-key', required=True, help='PhotoRoom API kulcs')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása')
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
    
    # Ellenőrizzük, hogy a bemeneti fájl létezik-e
    if not os.path.isfile(args.input_file):
        logger.error(f"A bemeneti fájl nem létezik: {args.input_file}")
        sys.exit(1)
    
    # Ellenőrizzük, hogy a kimeneti mappa létezik-e
    output_dir = os.path.dirname(args.output_file)
    if not os.path.exists(output_dir):
        logger.info(f"Kimeneti mappa létrehozása: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # Kép feldolgozása
    success = process_image(args.input_file, args.output_file, args.api_key, args.debug)
    
    if success:
        logger.info("Feldolgozás sikeresen befejezve")
        sys.exit(0)
    else:
        logger.error("Feldolgozás sikertelen")
        sys.exit(1)

if __name__ == "__main__":
    main() 