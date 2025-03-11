#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive PhotoRoom API Script

Ez a szkript interaktívan kéri be a kép URL-jét vagy elérési útját,
majd feldolgozza a PhotoRoom API-val a megadott paraméterekkel.
"""

import os
import sys
import requests
import logging
from urllib.parse import quote
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

# API kulcs - sandbox API kulcs használata
API_KEY = 'sandbox_f5a0cd1aeff027ca3084a3dad7b40462c3862a7a'

def process_image_with_url(image_url, output_path):
    """
    Feldolgozza a képet URL alapján a PhotoRoom API v2 végpontjával
    """
    logger.info(f"Kép feldolgozása URL-ből: {image_url}")
    
    # API paraméterek
    edit_params = 'background.color=EBECF0&ignorePaddingAndSnapOnCroppedSides=false&outputSize=1600x2000&segmentation.mode=keepSalientObject&segmentation.prompt=product&segmentation.negativePrompt=hand%2C%20finger&shadow.mode=ai.soft&lighting.mode=ai.auto&marginTop=0%25&marginBottom=0%25&marginLeft=0%25&marginRight=0%25&paddingTop=12%25&paddingBottom=12%25&paddingLeft=12%25&paddingRight=12%25&format=webp'
    
    # Fejlécek beállítása
    headers = {
        'x-api-key': API_KEY
    }
    
    try:
        # API végpont
        url = f"https://image-api.photoroom.com/v2/edit?{edit_params}&imageUrl={quote(image_url)}"
        
        # Kérés küldése
        logger.info("API kérés küldése...")
        response = requests.get(url, headers=headers)
        
        # Válasz ellenőrzése
        if response.status_code == 200:
            # Sikeres válasz esetén mentjük a képet
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Kép sikeresen feldolgozva és mentve: {output_path}")
            return True
        else:
            logger.error(f"API hiba ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False

def process_image_with_file(image_path, output_path):
    """
    Feldolgozza a helyi képfájlt a PhotoRoom API v2 végpontjával
    """
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
        'x-api-key': API_KEY
    }
    
    try:
        # Fájl megnyitása
        with open(image_path, 'rb') as image_file:
            files = {
                'imageFile': (os.path.basename(image_path), image_file, 'image/jpeg')
            }
            
            # API kérés küldése
            url = "https://image-api.photoroom.com/v2/edit"
            logger.info("API kérés küldése...")
            
            response = requests.post(url, files=files, data=params, headers=headers)
            
            # Válasz ellenőrzése
            if response.status_code == 200:
                # Sikeres válasz esetén mentjük a képet
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Kép sikeresen feldolgozva és mentve: {output_path}")
                return True
            else:
                logger.error(f"API hiba ({response.status_code}): {response.text}")
                return False
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False

def main():
    print("PhotoRoom API Interaktív Szkript")
    print("--------------------------------")
    print("Ez a szkript a PhotoRoom API-t használja képek feldolgozásához.")
    print("API kulcs: " + API_KEY[:13] + "..." + API_KEY[-5:])
    print()
    
    # Kép forrás bekérése
    while True:
        source_type = input("Kép forrása (1: URL, 2: Helyi fájl): ")
        if source_type in ['1', '2']:
            break
        print("Érvénytelen választás. Kérlek, válassz 1-et vagy 2-t.")
    
    # Kép URL vagy elérési út bekérése
    if source_type == '1':
        image_source = input("Kép URL-je: ")
        is_url = True
    else:
        image_source = input("Kép elérési útja: ")
        is_url = False
        
        # Ellenőrizzük, hogy a fájl létezik-e
        if not os.path.isfile(image_source):
            logger.error(f"A fájl nem létezik: {image_source}")
            sys.exit(1)
    
    # Kimeneti fájl bekérése
    output_file = input("Kimeneti fájl elérési útja (alapértelmezett: output.webp): ")
    if not output_file:
        output_file = "output.webp"
    
    # Ellenőrizzük, hogy a kimeneti fájl .webp kiterjesztésű-e
    output_ext = Path(output_file).suffix.lower()
    if output_ext != '.webp':
        logger.warning(f"A kimeneti fájl nem .webp kiterjesztésű: {output_file}")
        new_output_file = str(Path(output_file).with_suffix('.webp'))
        logger.info(f"Kimeneti fájl átnevezése: {new_output_file}")
        output_file = new_output_file
    
    # Ellenőrizzük, hogy a kimeneti mappa létezik-e
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        logger.info(f"Kimeneti mappa létrehozása: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    # Kép feldolgozása
    if is_url:
        success = process_image_with_url(image_source, output_file)
    else:
        success = process_image_with_file(image_source, output_file)
    
    if success:
        logger.info("Feldolgozás sikeresen befejezve")
        print(f"\nA kép sikeresen feldolgozva és mentve: {output_file}")
    else:
        logger.error("Feldolgozás sikertelen")
        print("\nA kép feldolgozása sikertelen. Ellenőrizd a naplófájlt a részletekért.")

if __name__ == "__main__":
    main() 