#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photoroom API Teszt

Ez a szkript bemutatja a Photoroom API alapvető használatát.
Egy képet küld az API-nak, eltávolítja a hátteret, és különböző beállításokat alkalmaz.
"""

import os
import sys
import requests
import argparse
import logging

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Photoroom API Teszt')
    parser.add_argument('--image', required=True, help='A feldolgozandó kép elérési útja')
    parser.add_argument('--output', required=True, help='A kimeneti kép elérési útja')
    parser.add_argument('--api-key', required=True, help='Photoroom API kulcs')
    return parser.parse_args()

def process_image(image_path, output_path, api_key):
    """
    Feldolgozza a képet a Photoroom API-val
    """
    logger.info(f"Kép feldolgozása: {image_path}")
    
    # API végpont
    url = "https://sdk.photoroom.com/v1/segment"
    
    # Fájl előkészítése
    files = {
        'image_file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')
    }
    
    # Paraméterek beállítása
    data = {
        'bg_color': '#EEEEE5',  # Egyszínű háttér színkódja
        'format': 'webp',       # Kimeneti formátum
        'size': 'portrait',     # Shopify portrait méret
        'crop': 'true',         # Automatikus vágás
        'position': 'center',   # Középre igazítás
        'scale': '13',          # 13% beállítás
        'shadow': 'soft'        # Soft AI árnyék
    }
    
    # Fejlécek beállítása
    headers = {
        'x-api-key': api_key
    }
    
    try:
        # API kérés küldése
        logger.info("API kérés küldése...")
        response = requests.post(url, files=files, data=data, headers=headers)
        
        # Ellenőrizzük a válasz státuszkódját
        if response.status_code == 200:
            # Sikeres válasz esetén mentjük a képet
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Kép sikeresen feldolgozva és mentve: {output_path}")
            return True
        else:
            logger.error(f"Hiba a feldolgozás során: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False
    finally:
        # Bezárjuk a fájlt
        files['image_file'][1].close()

def main():
    args = parse_args()
    
    # Ellenőrizzük, hogy a bemeneti fájl létezik-e
    if not os.path.isfile(args.image):
        logger.error(f"A bemeneti fájl nem létezik: {args.image}")
        sys.exit(1)
    
    # Ellenőrizzük, hogy a kimeneti mappa létezik-e
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Feldolgozzuk a képet
    success = process_image(args.image, args.output, args.api_key)
    
    if success:
        logger.info("A feldolgozás sikeres volt.")
    else:
        logger.error("A feldolgozás sikertelen volt.")
        sys.exit(1)

if __name__ == "__main__":
    main() 