#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shopify Image Uploader

Ez a szkript a feldolgozott képeket feltölti a Shopify-ra a termék vonalkódja (barcode) alapján.
A képek nevében lévő számsor alapján azonosítja a megfelelő terméket.
"""

import os
import sys
import requests
import argparse
import logging
import json
import re
import time
from pathlib import Path

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shopify_uploader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Shopify Image Uploader')
    parser.add_argument('--input-dir', required=True, help='Feldolgozott képek mappája')
    parser.add_argument('--shopify-api-key', required=True, help='Shopify API kulcs')
    parser.add_argument('--shopify-password', required=True, help='Shopify Admin API hozzáférési token')
    parser.add_argument('--shopify-store', required=True, help='Shopify bolt URL (pl. your-store.myshopify.com)')
    parser.add_argument('--batch-size', type=int, default=5, help='Egyszerre feldolgozandó képek száma (alapértelmezett: 5)')
    parser.add_argument('--delay', type=float, default=1.0, help='Késleltetés a kérések között másodpercben (alapértelmezett: 1.0)')
    parser.add_argument('--dry-run', action='store_true', help='Teszt mód - nem tölt fel képeket')
    return parser.parse_args()

def get_product_by_barcode(barcode, api_key, password, store):
    """
    Lekérdezi a terméket a vonalkód alapján
    """
    logger.info(f"Termék keresése vonalkód alapján: {barcode}")
    
    try:
        # Shopify API végpont - GraphQL
        url = f"https://{store}/admin/api/2023-07/graphql.json"
        
        # GraphQL lekérdezés
        query = """
        {
          products(first: 1, query: "barcode:%s") {
            edges {
              node {
                id
                title
                images(first: 10) {
                  edges {
                    node {
                      id
                      src
                    }
                  }
                }
              }
            }
          }
        }
        """ % barcode
        
        # Fejlécek
        headers = {
            "X-Shopify-Access-Token": password,
            "Content-Type": "application/json"
        }
        
        # Kérés küldése
        response = requests.post(url, json={"query": query}, headers=headers)
        
        # Válasz ellenőrzése
        if response.status_code == 200:
            data = response.json()
            products = data.get('data', {}).get('products', {}).get('edges', [])
            
            if products:
                product = products[0]['node']
                logger.info(f"Termék megtalálva: {product['title']} (ID: {product['id']})")
                return product
            else:
                logger.warning(f"Nem található termék a következő vonalkóddal: {barcode}")
                return None
        else:
            logger.error(f"Hiba a termék lekérdezése során: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Kivétel a termék lekérdezése során: {str(e)}")
        return None

def upload_image_to_product(image_path, product_id, api_key, password, store):
    """
    Feltölti a képet a termékhez
    """
    logger.info(f"Kép feltöltése a termékhez: {image_path} -> {product_id}")
    
    try:
        # Shopify API végpont - REST
        product_gid = product_id.split('/')[-1]
        url = f"https://{store}/admin/api/2023-07/products/{product_gid}/images.json"
        
        # Fájl előkészítése
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Base64 kódolás
        import base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        # Fájlnév kinyerése
        filename = os.path.basename(image_path)
        
        # Kérés adatok
        data = {
            "image": {
                "attachment": encoded_image,
                "filename": filename,
                "position": 1  # Fő kép
            }
        }
        
        # Fejlécek
        headers = {
            "X-Shopify-Access-Token": password,
            "Content-Type": "application/json"
        }
        
        # Kérés küldése
        response = requests.post(url, json=data, headers=headers)
        
        # Válasz ellenőrzése
        if response.status_code in [200, 201]:
            image_data = response.json().get('image', {})
            logger.info(f"Kép sikeresen feltöltve: {filename} (ID: {image_data.get('id')})")
            return True
        else:
            logger.error(f"Hiba a kép feltöltése során: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a kép feltöltése során: {str(e)}")
        return False

def extract_barcode_from_filename(filename):
    """
    Kivonja a vonalkódot a fájlnévből
    """
    # Számok kinyerése a fájlnévből
    numbers = re.findall(r'\d+', os.path.basename(filename))
    if numbers:
        # Az első számsorozatot használjuk vonalkódként
        return numbers[0]
    else:
        return None

def process_images(input_dir, api_key, password, store, batch_size=5, delay=1.0, dry_run=False):
    """
    Feldolgozza a képeket és feltölti a Shopify-ra
    """
    # Képek listázása
    image_files = []
    for ext in ['*.webp', '*.png', '*.jpg', '*.jpeg']:
        image_files.extend(list(Path(input_dir).glob(ext)))
    
    logger.info(f"Összesen {len(image_files)} kép található a mappában")
    
    # Eredmények számlálása
    total_success = 0
    total_error = 0
    total_not_found = 0
    
    # Képek feldolgozása kötegekben
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i+batch_size]
        logger.info(f"Köteg feldolgozása: {i+1}-{min(i+batch_size, len(image_files))} / {len(image_files)}")
        
        for image_path in batch:
            # Vonalkód kinyerése a fájlnévből
            barcode = extract_barcode_from_filename(image_path)
            
            if not barcode:
                logger.warning(f"Nem sikerült vonalkódot kinyerni a fájlnévből: {image_path}")
                total_error += 1
                continue
            
            # Termék lekérdezése a vonalkód alapján
            product = get_product_by_barcode(barcode, api_key, password, store)
            
            if not product:
                logger.warning(f"Nem található termék a következő vonalkóddal: {barcode}")
                total_not_found += 1
                continue
            
            # Kép feltöltése a termékhez
            if not dry_run:
                success = upload_image_to_product(str(image_path), product['id'], api_key, password, store)
                
                if success:
                    total_success += 1
                else:
                    total_error += 1
            else:
                logger.info(f"[TESZT MÓD] Kép feltöltése: {image_path} -> {product['title']} (ID: {product['id']})")
                total_success += 1
            
            # Késleltetés a kérések között
            time.sleep(delay)
        
        logger.info(f"Köteg feldolgozva. Következő köteg...")
    
    # Összesítés
    logger.info("Feldolgozás befejezve")
    logger.info(f"Összesen {len(image_files)} kép")
    logger.info(f"Sikeresen feltöltve: {total_success}")
    logger.info(f"Hiba: {total_error}")
    logger.info(f"Nem található termék: {total_not_found}")
    
    return total_success, total_error, total_not_found

def main():
    args = parse_args()
    
    # Ellenőrizzük, hogy a bemeneti mappa létezik-e
    if not os.path.isdir(args.input_dir):
        logger.error(f"A bemeneti mappa nem létezik: {args.input_dir}")
        sys.exit(1)
    
    # Képek feldolgozása
    logger.info("Shopify Image Uploader indítása")
    logger.info(f"Bemeneti mappa: {args.input_dir}")
    logger.info(f"Shopify bolt: {args.shopify_store}")
    logger.info(f"Köteg méret: {args.batch_size}")
    logger.info(f"Késleltetés: {args.delay} másodperc")
    
    if args.dry_run:
        logger.info("TESZT MÓD: Nem töltünk fel képeket")
    
    # Képek feldolgozása
    total_success, total_error, total_not_found = process_images(
        args.input_dir,
        args.shopify_api_key,
        args.shopify_password,
        args.shopify_store,
        args.batch_size,
        args.delay,
        args.dry_run
    )
    
    # Kilépési kód beállítása
    if total_error > 0 or total_not_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 