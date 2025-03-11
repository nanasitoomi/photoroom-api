#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photoroom API Batch Processor és Shopify Feltöltő

Ez a szkript a következőket végzi:
1. Feldolgozza a képeket egy megadott mappából
2. Elküldi őket a Photoroom API-nak a következő beállításokkal:
   - Háttér eltávolítása
   - #EEEEE színkódú egyszínű háttér hozzáadása
   - Soft AI árnyék hozzáadása
   - Középre igazítás (centered)
   - 13% beállítás
   - Shopify portrait méret
3. A feldolgozott képeket WebP formátumban menti
4. Feltölti a képeket a Shopify API-n keresztül, megtartva az eredeti fájlneveket

Használat:
    python batch_process.py --input-dir /path/to/images --output-dir /path/to/output --batch-size 10

Paraméterek:
    --input-dir: A bemeneti képek mappája
    --output-dir: A kimeneti képek mappája
    --batch-size: Egyszerre feldolgozandó képek száma (alapértelmezett: 10)
    --photoroom-api-key: Photoroom API kulcs
    --shopify-api-key: Shopify API kulcs
    --shopify-password: Shopify API jelszó
    --shopify-store: Shopify bolt neve (pl. your-store.myshopify.com)
"""

import os
import sys
import argparse
import time
import json
import requests
import base64
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_process.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Argumentumok feldolgozása
def parse_args():
    parser = argparse.ArgumentParser(description='Photoroom API Batch Processor és Shopify Feltöltő')
    parser.add_argument('--input-dir', required=True, help='A bemeneti képek mappája')
    parser.add_argument('--output-dir', required=True, help='A kimeneti képek mappája')
    parser.add_argument('--batch-size', type=int, default=10, help='Egyszerre feldolgozandó képek száma')
    parser.add_argument('--photoroom-api-key', required=True, help='Photoroom API kulcs')
    parser.add_argument('--shopify-api-key', required=True, help='Shopify API kulcs')
    parser.add_argument('--shopify-password', required=True, help='Shopify API jelszó')
    parser.add_argument('--shopify-store', required=True, help='Shopify bolt neve (pl. your-store.myshopify.com)')
    return parser.parse_args()

# Kép feldolgozása a Photoroom API-val
def process_image_with_photoroom(image_path, output_path, api_key):
    """
    Feldolgozza a képet a Photoroom API-val a megadott beállításokkal
    """
    logger.info(f"Feldolgozás: {image_path}")
    
    # API végpont
    url = "https://sdk.photoroom.com/v1/segment"
    
    # Fájl előkészítése
    files = {
        'image_file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/jpeg')
    }
    
    # Paraméterek beállítása
    data = {
        'bg_color': '#EEEEE5',  # Egyszínű háttér színkódja (javítva 6 karakterre)
        'format': 'webp',      # Kimeneti formátum
        'size': 'portrait',    # Shopify portrait méret
        'crop': 'true',        # Automatikus vágás
        'position': 'center',  # Középre igazítás
        'scale': '13',         # 13% beállítás
        'shadow': 'soft'       # Soft AI árnyék
    }
    
    # Fejlécek beállítása
    headers = {
        'x-api-key': api_key
    }
    
    try:
        # API kérés küldése
        response = requests.post(url, files=files, data=data, headers=headers)
        
        # Ellenőrizzük a válasz státuszkódját
        if response.status_code == 200:
            # Sikeres válasz esetén mentjük a képet
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Sikeres feldolgozás: {output_path}")
            return True, output_path
        else:
            logger.error(f"Hiba a feldolgozás során: {response.status_code} - {response.text}")
            return False, None
    except Exception as e:
        logger.error(f"Kivétel a feldolgozás során: {str(e)}")
        return False, None
    finally:
        # Bezárjuk a fájlt
        files['image_file'][1].close()

# Kép feltöltése a Shopify API-ra
def upload_to_shopify(image_path, api_key, password, store):
    """
    Feltölti a képet a Shopify API-ra
    """
    logger.info(f"Feltöltés Shopify-ra: {image_path}")
    
    # API végpont
    url = f"https://{api_key}:{password}@{store}/admin/api/2023-07/products/images.json"
    
    # Fájl előkészítése
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Base64 kódolás
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    
    # Kérés adatai
    data = {
        "image": {
            "attachment": encoded_image,
            "filename": os.path.basename(image_path)
        }
    }
    
    try:
        # API kérés küldése
        response = requests.post(url, json=data)
        
        # Ellenőrizzük a válasz státuszkódját
        if response.status_code in [200, 201]:
            logger.info(f"Sikeres feltöltés Shopify-ra: {image_path}")
            return True
        else:
            logger.error(f"Hiba a Shopify feltöltés során: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a Shopify feltöltés során: {str(e)}")
        return False

# Batch feldolgozás
def process_batch(image_paths, output_dir, photoroom_api_key, shopify_api_key, shopify_password, shopify_store):
    """
    Feldolgoz egy batch-et képekből
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for image_path in image_paths:
            # Kimeneti fájlnév generálása
            filename = os.path.basename(image_path)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}.webp")
            
            # Kép feldolgozása
            future = executor.submit(
                process_image_with_photoroom, 
                image_path, 
                output_path, 
                photoroom_api_key
            )
            futures.append((future, output_path))
        
        # Eredmények összegyűjtése
        for future, output_path in futures:
            success, processed_path = future.result()
            if success:
                results.append(processed_path)
    
    # Shopify feltöltés
    if shopify_api_key and shopify_password and shopify_store:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for processed_path in results:
                future = executor.submit(
                    upload_to_shopify,
                    processed_path,
                    shopify_api_key,
                    shopify_password,
                    shopify_store
                )
                futures.append(future)
            
            # Eredmények összegyűjtése
            for future in futures:
                future.result()
    
    return results

# Fő függvény
def main():
    args = parse_args()
    
    # Ellenőrizzük a bemeneti mappát
    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        logger.error(f"A bemeneti mappa nem létezik: {input_dir}")
        sys.exit(1)
    
    # Ellenőrizzük/létrehozzuk a kimeneti mappát
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Képek összegyűjtése
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    image_paths = []
    
    for root, _, files in os.walk(input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_paths.append(os.path.join(root, file))
    
    logger.info(f"Összesen {len(image_paths)} kép található a bemeneti mappában")
    
    # Batch-ekre osztás
    batch_size = args.batch_size
    batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
    
    # Feldolgozás batch-enként
    all_results = []
    
    for i, batch in enumerate(batches):
        logger.info(f"Batch feldolgozása: {i+1}/{len(batches)}")
        results = process_batch(
            batch, 
            output_dir, 
            args.photoroom_api_key,
            args.shopify_api_key,
            args.shopify_password,
            args.shopify_store
        )
        all_results.extend(results)
        
        # Kis szünet a batch-ek között, hogy ne terheljük túl az API-t
        if i < len(batches) - 1:
            time.sleep(1)
    
    logger.info(f"Feldolgozás befejezve. {len(all_results)} kép sikeresen feldolgozva.")

if __name__ == "__main__":
    main() 