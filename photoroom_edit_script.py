#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PhotoRoom API v2 Image Editor

Ez a szkript a PhotoRoom API v2 végpontját használja képek feldolgozásához
a következő paraméterekkel:
- Háttérszín: EBECF0 (világos szürke)
- Kimeneti méret: 1600x2000
- Szegmentálás mód: keepSalientObject
- Szegmentálás prompt: product
- Szegmentálás negatív prompt: hand, finger
- Árnyék: ai.soft
- Világítás: ai.auto
- Padding: 12% minden oldalon
- Formátum: WebP
- ignorePaddingAndSnapOnCroppedSides: false

Használat:
    python photoroom_edit_script.py --input-file input/image.jpg --output-file output/result.webp --api-key YOUR_API_KEY
"""

import os
import sys
import requests
import argparse
import logging
import time
import json
from urllib.parse import quote
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("photoroom_edit_script.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='PhotoRoom API v2 Image Editor')
    parser.add_argument('--input-file', required=True, help='Bemeneti kép elérési útja')
    parser.add_argument('--output-file', required=True, help='Kimeneti kép elérési útja (.webp kiterjesztéssel)')
    parser.add_argument('--api-key', required=True, help='PhotoRoom API kulcs')
    parser.add_argument('--image-url', help='Kép URL-je (opcionális, ha nem a helyi fájlt szeretnénk használni)')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása')
    return parser.parse_args()

def process_image_with_url(image_url, output_path, api_key, debug=False):
    """
    Feldolgozza a képet URL alapján a PhotoRoom API v2 végpontjával
    """
    if debug:
        logger.debug(f"Kép feldolgozása URL-ből: {image_url}")
    else:
        logger.info(f"Kép feldolgozása URL-ből: {image_url}")
    
    # API paraméterek
    edit_params = 'background.color=EBECF0&ignorePaddingAndSnapOnCroppedSides=false&outputSize=1600x2000&segmentation.mode=keepSalientObject&segmentation.prompt=product&segmentation.negativePrompt=hand%2C%20finger&shadow.mode=ai.soft&lighting.mode=ai.auto&marginTop=0%25&marginBottom=0%25&marginLeft=0%25&marginRight=0%25&paddingTop=12%25&paddingBottom=12%25&paddingLeft=12%25&paddingRight=12%25&format=webp'
    
    # URL kódolás ellenőrzése
    if '%25' not in edit_params:
        edit_params = edit_params.replace('%', '%25')
    
    # Fejlécek beállítása
    headers = {
        'x-api-key': api_key
    }
    
    try:
        # API végpont
        url = f"https://image-api.photoroom.com/v2/edit?{edit_params}&imageUrl={quote(image_url)}"
        
        if debug:
            logger.debug(f"API kérés küldése: {url}")
        
        # Kérés küldése
        start_time = time.time()
        response = requests.get(url, headers=headers)
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

def process_image_with_file(image_path, output_path, api_key, debug=False):
    """
    Feldolgozza a helyi képfájlt a PhotoRoom API v2 végpontjával
    """
    if debug:
        logger.debug(f"Kép feldolgozása: {image_path}")
    else:
        logger.info(f"Kép feldolgozása: {image_path}")
    
    # API paraméterek
    params = {
        'background.color': 'EBECF0',
        'ignorePaddingAndSnapOnCroppedSides': 'false',
        'outputSize': '1600x2000',
        'segmentation.mode': 'keepSalientObject',
        'segmentation.prompt': 'product',
        'segmentation.negativePrompt': 'hand, finger',
        'shadow.mode': 'ai.soft',
        'lighting.mode': 'ai.auto',
        'marginTop': '0%',
        'marginBottom': '0%',
        'marginLeft': '0%',
        'marginRight': '0%',
        'paddingTop': '12%',
        'paddingBottom': '12%',
        'paddingLeft': '12%',
        'paddingRight': '12%',
        'format': 'webp'
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
    
    # Ellenőrizzük, hogy a kimeneti fájl .webp kiterjesztésű-e
    output_ext = Path(args.output_file).suffix.lower()
    if output_ext != '.webp':
        logger.warning(f"A kimeneti fájl nem .webp kiterjesztésű: {args.output_file}")
        new_output_file = str(Path(args.output_file).with_suffix('.webp'))
        logger.info(f"Kimeneti fájl átnevezése: {new_output_file}")
        args.output_file = new_output_file
    
    # Ellenőrizzük, hogy van-e URL vagy helyi fájl
    if args.image_url:
        # URL alapú feldolgozás
        logger.info(f"URL alapú feldolgozás: {args.image_url}")
        
        # Ellenőrizzük, hogy a kimeneti mappa létezik-e
        output_dir = os.path.dirname(args.output_file)
        if not os.path.exists(output_dir):
            logger.info(f"Kimeneti mappa létrehozása: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
        
        # Kép feldolgozása
        success = process_image_with_url(args.image_url, args.output_file, args.api_key, args.debug)
    else:
        # Helyi fájl alapú feldolgozás
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
        success = process_image_with_file(args.input_file, args.output_file, args.api_key, args.debug)
    
    if success:
        logger.info("Feldolgozás sikeresen befejezve")
        logger.info(f"Kimeneti fájl: {args.output_file} (WebP formátum)")
        sys.exit(0)
    else:
        logger.error("Feldolgozás sikertelen")
        sys.exit(1)

if __name__ == "__main__":
    main() 