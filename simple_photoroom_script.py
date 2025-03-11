#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple PhotoRoom API Script

Ez a szkript a PhotoRoom API v2 végpontját használja képek feldolgozásához
a felhasználó által megadott paraméterekkel.
"""

import os
import requests
import argparse
import logging
import subprocess
import re
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Simple PhotoRoom API Script')
    parser.add_argument('--input-file', required=True, help='Bemeneti kép elérési útja')
    parser.add_argument('--output-file', help='Kimeneti kép elérési útja (opcionális, alapértelmezetten a számsor.webp)')
    parser.add_argument('--output-dir', help='Kimeneti mappa elérési útja (opcionális, alapértelmezetten output/real_webp)')
    return parser.parse_args()

def extract_number_from_filename(filename):
    """
    Kivonja a számokat a fájlnévből
    """
    # Regex minta a számok kinyeréséhez
    numbers = re.findall(r'\d+', os.path.basename(filename))
    if numbers:
        # Az első számsorozatot használjuk
        return numbers[0]
    else:
        # Ha nincs szám a fájlnévben, akkor az eredeti fájlnevet használjuk kiterjesztés nélkül
        return os.path.splitext(os.path.basename(filename))[0]

def convert_to_webp(input_file, output_file):
    """
    Konvertálja a képet WebP formátumba
    """
    try:
        # Ellenőrizzük, hogy a cwebp parancs elérhető-e
        result = subprocess.run(['which', 'cwebp'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("A cwebp parancs nem található. Telepítsd a libwebp csomagot.")
            logger.warning("Például: brew install webp")
            return False
        
        # Konvertálás WebP formátumba
        logger.info(f"Konvertálás WebP formátumba: {input_file} -> {output_file}")
        result = subprocess.run(['cwebp', '-q', '90', input_file, '-o', output_file], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Konvertálás sikeres")
            return True
        else:
            logger.error(f"Konvertálási hiba: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a konvertálás során: {str(e)}")
        return False

def process_image(input_file, output_file=None):
    """
    Feldolgozza a képet a PhotoRoom API v2 végpontjával
    """
    logger.info(f"Kép feldolgozása: {input_file}")
    
    # Ha nincs megadva kimeneti fájl, akkor a számsor.webp nevet használjuk
    if output_file is None:
        number = extract_number_from_filename(input_file)
        output_dir = "output/real_webp"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{number}.webp")
    
    logger.info(f"Kimeneti fájl: {output_file}")
    
    # Ideiglenes fájl a PNG kimenethez
    temp_output = output_file + ".temp.png"
    
    # Kép URL-lé konvertálása (ha helyi fájl)
    if os.path.isfile(input_file):
        # Helyi fájl esetén feltöltjük
        with open(input_file, 'rb') as image_file:
            files = {
                'imageFile': (os.path.basename(input_file), image_file, 'image/jpeg')
            }
            
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
                'paddingTop': '10%',
                'paddingBottom': '10%',
                'paddingLeft': '10%',
                'paddingRight': '10%',
                'format': 'png',
                'quality': '90'
            }
            
            # Fejlécek beállítása - sandbox API kulcs használata
            headers = {
                'x-api-key': 'sandbox_f5a0cd1aeff027ca3084a3dad7b40462c3862a7a'
            }
            
            # API kérés küldése
            url = "https://image-api.photoroom.com/v2/edit"
            logger.info(f"API kérés küldése: {url}")
            
            response = requests.post(url, files=files, data=params, headers=headers)
    else:
        # URL esetén közvetlenül használjuk
        image_url = input_file
        
        # API paraméterek
        edit_params = 'background.color=EBECF0&ignorePaddingAndSnapOnCroppedSides=false&outputSize=1600x2000&segmentation.mode=keepSalientObject&segmentation.prompt=product&segmentation.negativePrompt=hand%2C%20finger&shadow.mode=ai.soft&lighting.mode=ai.auto&marginTop=0%25&marginBottom=0%25&marginLeft=0%25&marginRight=0%25&paddingTop=10%25&paddingBottom=10%25&paddingLeft=10%25&paddingRight=10%25&format=png&quality=90'
        
        # Fejlécek beállítása - sandbox API kulcs használata
        headers = {
            'x-api-key': 'sandbox_f5a0cd1aeff027ca3084a3dad7b40462c3862a7a'
        }
        
        # API végpont
        url = f"https://image-api.photoroom.com/v2/edit?{edit_params}&imageUrl={image_url}"
        logger.info(f"API kérés küldése URL-lel")
        
        # Kérés küldése
        response = requests.get(url, headers=headers)
    
    # Válasz ellenőrzése
    if response.status_code == 200:
        # Sikeres válasz esetén mentjük a képet
        with open(temp_output, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Kép sikeresen feldolgozva és mentve: {temp_output}")
        
        # Konvertálás WebP formátumba
        if convert_to_webp(temp_output, output_file):
            # Ideiglenes fájl törlése
            os.remove(temp_output)
            logger.info(f"Ideiglenes fájl törölve: {temp_output}")
            return True
        else:
            logger.error("WebP konvertálás sikertelen")
            # Ha a konvertálás sikertelen, átnevezzük a temp fájlt
            os.rename(temp_output, output_file)
            logger.warning(f"Az eredeti PNG fájl átnevezve: {output_file}")
            return True
    else:
        logger.error(f"API hiba ({response.status_code}): {response.text}")
        return False

def main():
    args = parse_args()
    
    # Kimeneti fájl meghatározása
    output_file = args.output_file
    
    # Ha van megadva kimeneti mappa, de nincs kimeneti fájl
    if args.output_dir and not args.output_file:
        # Ellenőrizzük, hogy a kimeneti mappa létezik-e
        if not os.path.exists(args.output_dir):
            logger.info(f"Kimeneti mappa létrehozása: {args.output_dir}")
            os.makedirs(args.output_dir, exist_ok=True)
        
        # Számsor kinyerése a fájlnévből
        number = extract_number_from_filename(args.input_file)
        output_file = os.path.join(args.output_dir, f"{number}.webp")
    
    # Ha van megadva kimeneti fájl
    if output_file:
        # Ellenőrizzük, hogy a kimeneti mappa létezik-e
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            logger.info(f"Kimeneti mappa létrehozása: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
    
    # Kép feldolgozása
    success = process_image(args.input_file, output_file)
    
    if success:
        logger.info("Feldolgozás sikeresen befejezve")
    else:
        logger.error("Feldolgozás sikertelen")

if __name__ == "__main__":
    main() 