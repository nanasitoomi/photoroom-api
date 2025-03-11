#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PhotoRoom és Shopify Integráció

Ez a szkript a PhotoRoom API-t használja képek háttérének eltávolítására és módosítására,
majd a feldolgozott képeket feltölti a Shopify webáruházba a termék vonalkódja alapján.
"""

import os
import sys
import requests
import logging
import re
import base64
import argparse
import json
from datetime import datetime
import glob
import time
import concurrent.futures
from tqdm import tqdm
import requests.exceptions
from functools import wraps
import tempfile
import csv
import shutil

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Újrapróbálkozási dekorátor
def retry(max_tries=3, delay_seconds=1, backoff_factor=2, exceptions=(requests.exceptions.RequestException,)):
    """
    Újrapróbálkozási dekorátor hálózati kérésekhez
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay_seconds
            last_exception = None
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Hiba történt: {str(e)}. Újrapróbálkozás {mdelay} másodperc múlva...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff_factor
            logger.error(f"Sikertelen újrapróbálkozás után feladva: {str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator

def parse_args():
    parser = argparse.ArgumentParser(description='PhotoRoom és Shopify Integráció')
    parser.add_argument('--image-file', help='Feltöltendő kép fájl')
    parser.add_argument('--input-dir', help='Bemeneti könyvtár a feldolgozandó képeknek')
    parser.add_argument('--photoroom-api-key', required=True, help='PhotoRoom API kulcs')
    parser.add_argument('--shopify-api-key', required=True, help='Shopify API kulcs')
    parser.add_argument('--shopify-password', required=True, help='Shopify Admin API hozzáférési token')
    parser.add_argument('--shopify-store', required=True, help='Shopify bolt URL (pl. your-store.myshopify.com)')
    parser.add_argument('--output-dir', default='output', help='Kimeneti könyvtár a feldolgozott képeknek')
    parser.add_argument('--background-color', default='white', help='Háttérszín (pl. white, transparent, #FF5733)')
    parser.add_argument('--batch-size', type=int, default=5, help='Egyszerre feldolgozandó képek száma')
    parser.add_argument('--delay', type=float, default=1.0, help='Késleltetés a kérések között másodpercben')
    parser.add_argument('--debug', action='store_true', help='Debug mód bekapcsolása (részletes információk)')
    return parser.parse_args()

@retry(max_tries=3, delay_seconds=2)
def process_image_with_photoroom(image_path, output_dir, api_key, background_color='white'):
    """
    Feldolgozza a képet a PhotoRoom API-val
    """
    logger.info(f"Kép feldolgozása PhotoRoom API-val: {image_path}")
    
    # Ellenőrizzük, hogy a fájl létezik-e
    if not os.path.isfile(image_path):
        logger.error(f"A megadott képfájl nem létezik: {image_path}")
        return None
    
    # Ellenőrizzük a fájl méretét
    file_size = os.path.getsize(image_path)
    if file_size > 20 * 1024 * 1024:  # 20 MB
        logger.warning(f"A fájl mérete túl nagy ({file_size / (1024*1024):.2f} MB), ez problémákat okozhat")
    
    # Kimeneti könyvtár létrehozása, ha nem létezik
    os.makedirs(output_dir, exist_ok=True)
    
    # Kimeneti fájl neve
    base_name = os.path.basename(image_path)
    file_name, file_ext = os.path.splitext(base_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = os.path.join(output_dir, f"{file_name}_processed_{timestamp}.png")
    
    try:
        # API végpont
        url = "https://image-api.photoroom.com/v2/edit"
        
        # Fejlécek
        headers = {
            "x-api-key": api_key
        }
        
        # Fájl előkészítése
        with open(image_path, 'rb') as f:
            files = {
                'imageFile': (os.path.basename(image_path), f, 'image/jpeg')
            }
            
            # Paraméterek
            data = {
                'background.color': background_color,
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
            
            # Kérés küldése időtúllépés kezeléssel
            logger.info(f"PhotoRoom API kérés küldése: {url}")
            response = requests.post(url, headers=headers, files=files, data=data, timeout=(10, 60))  # 10s connect, 60s read
            
            # Válasz ellenőrzése
            if response.status_code == 200:
                # Ideiglenes fájl használata a biztonságos íráshoz
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                # Átnevezés a végleges fájlnévre
                try:
                    shutil.move(temp_path, output_file)
                    logger.info(f"Feldolgozott kép mentve: {output_file}")
                    return output_file
                except Exception as e:
                    logger.error(f"Hiba a fájl átnevezése során: {str(e)}")
                    os.unlink(temp_path)  # Töröljük az ideiglenes fájlt
                    return None
            else:
                logger.error(f"Hiba a PhotoRoom API kérés során: {response.status_code} - {response.text}")
                return None
    
    except requests.exceptions.Timeout:
        logger.error(f"Időtúllépés a PhotoRoom API kérés során: {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Kapcsolódási hiba a PhotoRoom API kérés során: {url}")
        return None
    except Exception as e:
        logger.error(f"Kivétel a PhotoRoom API kérés során: {str(e)}")
        return None

@retry(max_tries=3, delay_seconds=2)
def get_product_by_barcode(barcode, api_key, password, store):
    """
    Lekérdezi a terméket a vonalkód alapján
    """
    logger.info(f"Termék keresése vonalkód alapján: {barcode}")
    
    # Ellenőrizzük a vonalkód formátumát
    if not barcode or not isinstance(barcode, str) or not barcode.strip():
        logger.error(f"Érvénytelen vonalkód: {barcode}")
        return None
    
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
    """ % barcode.strip()
    
    try:
        # Shopify API végpont - GraphQL
        url = f"https://{store}/admin/api/2025-01/graphql.json"
        
        # Fejlécek
        headers = {
            "X-Shopify-Access-Token": password,
            "Content-Type": "application/json"
        }
        
        # Kérés küldése időtúllépés kezeléssel
        response = requests.post(url, json={"query": query}, headers=headers, timeout=(5, 30))  # 5s connect, 30s read
        
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
        
    except requests.exceptions.Timeout:
        logger.error(f"Időtúllépés a termék lekérdezése során: {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Kapcsolódási hiba a termék lekérdezése során: {url}")
        return None
    except Exception as e:
        logger.error(f"Kivétel a termék lekérdezése során: {str(e)}")
        return None

def get_product_name_by_barcode(barcode, api_key, password, store):
    """
    Lekérdezi a termék nevét a vonalkód alapján
    """
    logger.info(f"Termék nevének keresése vonalkód alapján: {barcode}")
    
    # GraphQL lekérdezés
    query = """
    {
      products(first: 1, query: "barcode:%s") {
        edges {
          node {
            id
            title
          }
        }
      }
    }
    """ % barcode
    
    try:
        # Shopify API végpont - GraphQL
        url = f"https://{store}/admin/api/2025-01/graphql.json"
        
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
                product_name = product['title']
                product_id = product['id']
                logger.info(f"Termék megtalálva: {product_name} (ID: {product_id})")
                return product_name
            else:
                logger.warning(f"Nem található termék a következő vonalkóddal: {barcode}")
                return None
        else:
            logger.error(f"Hiba a termék lekérdezése során: {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"Kivétel a termék lekérdezése során: {str(e)}")
        return None

@retry(max_tries=3, delay_seconds=2)
def upload_image_to_product(image_file, product_id, api_key, password, store):
    """
    Feltölti a képet a termékhez
    """
    logger.info(f"Kép feltöltése a termékhez: {image_file} -> {product_id}")
    
    # Ellenőrizzük, hogy a fájl létezik-e
    if not os.path.isfile(image_file):
        logger.error(f"A megadott képfájl nem létezik: {image_file}")
        return False
    
    try:
        # Kép beolvasása
        with open(image_file, 'rb') as f:
            image_data = f.read()
        
        # Ellenőrizzük a fájl méretét
        file_size = len(image_data)
        if file_size > 20 * 1024 * 1024:  # 20 MB
            logger.warning(f"A fájl mérete túl nagy ({file_size / (1024*1024):.2f} MB), ez problémákat okozhat")
        
        # Shopify product ID kinyerése a GraphQL ID-ból
        # A GraphQL ID formátuma: gid://shopify/Product/1234567890
        # Ebből kell kinyerni a számot a végén
        product_id_match = re.search(r'Product/(\d+)', product_id)
        if not product_id_match:
            logger.error(f"Nem sikerült kinyerni a termék ID-t: {product_id}")
            return False
        
        numeric_product_id = product_id_match.group(1)
        logger.info(f"Numerikus termék ID: {numeric_product_id}")
        
        # REST API végpont a kép feltöltéséhez
        url = f"https://{store}/admin/api/2025-01/products/{numeric_product_id}/images.json"
        
        # Fejlécek
        headers = {
            "X-Shopify-Access-Token": password,
            "Content-Type": "application/json"
        }
        
        # Kép feltöltése multipart/form-data formátumban
        files = {
            'image': (os.path.basename(image_file), image_data, 'image/jpeg')
        }
        
        # Kérés adatok
        data = {
            "image": {
                "attachment": base64.b64encode(image_data).decode('utf-8'),
                "filename": os.path.basename(image_file)
            }
        }
        
        # Kérés küldése időtúllépés kezeléssel
        response = requests.post(url, json=data, headers=headers, timeout=(5, 60))  # 5s connect, 60s read
        
        # Válasz ellenőrzése
        if response.status_code in [200, 201]:
            logger.info(f"Kép sikeresen feltöltve a termékhez: {product_id}")
            return True
        else:
            logger.error(f"Hiba a kép feltöltése során: {response.status_code} - {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        logger.error(f"Időtúllépés a kép feltöltése során: {url}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Kapcsolódási hiba a kép feltöltése során: {url}")
        return False
    except Exception as e:
        logger.error(f"Kivétel a kép feltöltése során: {str(e)}")
        return False

def extract_barcode_from_filename(filename):
    """
    Kivonja a vonalkódot a fájlnévből
    """
    if not filename:
        logger.error("Üres fájlnév")
        return ""
    
    try:
        # Regex minta a számok kinyeréséhez
        numbers = re.findall(r'\d+', os.path.basename(filename))
        if numbers:
            # Az első számsorozatot használjuk
            return numbers[0]
        else:
            # Ha nincs szám a fájlnévben, akkor az eredeti fájlnevet használjuk kiterjesztés nélkül
            return os.path.splitext(os.path.basename(filename))[0]
    except Exception as e:
        logger.error(f"Hiba a vonalkód kinyerése során: {str(e)}")
        return os.path.basename(filename)

def process_and_upload_image(image_file, photoroom_api_key, shopify_api_key, shopify_password, shopify_store, output_dir, background_color='white'):
    """
    Feldolgozza a képet a PhotoRoom API-val, majd feltölti a Shopify-ra
    """
    # Ellenőrizzük, hogy a fájl létezik-e
    if not os.path.isfile(image_file):
        logger.error(f"A megadott képfájl nem létezik: {image_file}")
        return False
    
    try:
        # Vonalkód kinyerése a fájlnévből
        barcode = extract_barcode_from_filename(image_file)
        if not barcode:
            logger.error(f"Nem sikerült vonalkódot kinyerni a fájlnévből: {image_file}")
            return False
            
        logger.info(f"Vonalkód kinyerve a fájlnévből: {barcode}")
        
        # Termék lekérdezése a vonalkód alapján
        product = get_product_by_barcode(barcode, shopify_api_key, shopify_password, shopify_store)
        
        if product:
            # Kép feldolgozása a PhotoRoom API-val
            processed_image = process_image_with_photoroom(image_file, output_dir, photoroom_api_key, background_color)
            
            if processed_image:
                # Feldolgozott kép feltöltése a termékhez
                if upload_image_to_product(processed_image, product['id'], shopify_api_key, shopify_password, shopify_store):
                    logger.info(f"Feldolgozott kép sikeresen feltöltve a termékhez: {product['title']} (ID: {product['id']})")
                    return True
                else:
                    logger.error(f"Hiba a feldolgozott kép feltöltése során: {processed_image} -> {product['title']}")
                    return False
            else:
                logger.error(f"Hiba a kép feldolgozása során: {image_file}")
                return False
        else:
            logger.error(f"Nem található termék a következő vonalkóddal: {barcode}")
            return False
    except Exception as e:
        logger.error(f"Kivétel a kép feldolgozása és feltöltése során: {str(e)}")
        return False

def process_batch(input_dir, output_dir, photoroom_api_key, shopify_api_key, shopify_password, shopify_store, background_color='white', batch_size=5, delay=0.2, max_workers=4):
    """
    Feldolgoz egy egész könyvtárnyi képet és feltölti a Shopify-ra párhuzamos feldolgozással
    """
    logger.info(f"Batch feldolgozás indítása: {input_dir}")
    
    # Ellenőrizzük, hogy a könyvtár létezik-e
    if not os.path.isdir(input_dir):
        logger.error(f"A megadott könyvtár nem létezik: {input_dir}")
        return False
    
    try:
        # Képfájlok keresése a könyvtárban
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            pattern = os.path.join(input_dir, ext)
            image_files.extend(glob.glob(pattern))
        
        # Ellenőrizzük, hogy találtunk-e képeket
        if not image_files:
            logger.error(f"Nem találhatók képfájlok a könyvtárban: {input_dir}")
            return False
        
        # Rendezzük a fájlokat név szerint
        image_files.sort()
        
        logger.info(f"Összesen {len(image_files)} kép található a könyvtárban")
        
        # Statisztika
        total_images = len(image_files)
        successful_images = 0
        failed_images = 0
        
        # Feldolgozási funkció
        def process_image(image_file):
            try:
                # Kép feldolgozása és feltöltése
                result = process_and_upload_image(image_file, photoroom_api_key, shopify_api_key, shopify_password, shopify_store, output_dir, background_color)
                # Késleltetés a kérések között
                if delay > 0:
                    time.sleep(delay)
                return (image_file, result)
            except Exception as e:
                logger.error(f"Kivétel a kép feldolgozása során: {str(e)}")
                return (image_file, False)
        
        # Párhuzamos feldolgozás ThreadPoolExecutor-ral
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Képek feldolgozása batch-ekben
            results = []
            for i in range(0, total_images, batch_size):
                batch = image_files[i:i+batch_size]
                logger.info(f"Batch feldolgozása: {i+1}-{min(i+batch_size, total_images)} / {total_images}")
                
                # Batch párhuzamos feldolgozása
                futures = [executor.submit(process_image, image_file) for image_file in batch]
                
                # Eredmények begyűjtése
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Feldolgozás"):
                    try:
                        image_file, success = future.result()
                        results.append((image_file, success))
                        if success:
                            successful_images += 1
                        else:
                            failed_images += 1
                    except Exception as e:
                        logger.error(f"Hiba a future eredményének feldolgozása során: {str(e)}")
                        failed_images += 1
        
        # Összesítés
        logger.info(f"Batch feldolgozás befejezve")
        logger.info(f"Összesen feldolgozott képek: {total_images}")
        logger.info(f"Sikeres feltöltések: {successful_images}")
        logger.info(f"Sikertelen feltöltések: {failed_images}")
        
        # Eredmények mentése CSV fájlba
        result_file = os.path.join(output_dir, f"batch_results_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        try:
            with open(result_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Fájl', 'Eredmény'])
                for image_file, success in results:
                    writer.writerow([image_file, 'Sikeres' if success else 'Sikertelen'])
            logger.info(f"Eredmények mentve: {result_file}")
        except Exception as e:
            logger.error(f"Hiba az eredmények mentése során: {str(e)}")
        
        return successful_images > 0
    
    except Exception as e:
        logger.error(f"Kivétel a batch feldolgozás során: {str(e)}")
        return False

if __name__ == "__main__":
    # Ha közvetlenül futtatjuk a szkriptet
    if len(sys.argv) > 1 and sys.argv[1] == "get_product_name":
        # Parancssori argumentumok
        if len(sys.argv) < 6:
            print("Használat: python photoroom_shopify_integration.py get_product_name <barcode> <shopify_api_key> <shopify_password> <shopify_store>")
            sys.exit(1)
        
        barcode = sys.argv[2]
        api_key = sys.argv[3]
        password = sys.argv[4]
        store = sys.argv[5]
        
        # Termék nevének lekérdezése
        product_name = get_product_name_by_barcode(barcode, api_key, password, store)
        
        if product_name:
            print(f"Termék neve: {product_name}")
        else:
            print(f"Nem található termék a következő vonalkóddal: {barcode}")
    elif len(sys.argv) > 1 and sys.argv[1] == "upload_image":
        # Parancssori argumentumok
        if len(sys.argv) < 6:
            print("Használat: python photoroom_shopify_integration.py upload_image <image_file> <shopify_api_key> <shopify_password> <shopify_store>")
            sys.exit(1)
        
        image_file = sys.argv[2]
        api_key = sys.argv[3]
        password = sys.argv[4]
        store = sys.argv[5]
        
        # Vonalkód kinyerése a fájlnévből
        barcode = extract_barcode_from_filename(image_file)
        logger.info(f"Vonalkód kinyerve a fájlnévből: {barcode}")
        
        # Termék lekérdezése a vonalkód alapján
        product = get_product_by_barcode(barcode, api_key, password, store)
        
        if product:
            # Kép feltöltése a termékhez
            if upload_image_to_product(image_file, product['id'], api_key, password, store):
                logger.info(f"Kép sikeresen feltöltve a termékhez: {product['title']} (ID: {product['id']})")
                print(f"Kép sikeresen feltöltve a termékhez: {image_file}")
            else:
                logger.error(f"Hiba a kép feltöltése során: {image_file} -> {product['title']}")
                print(f"Hiba a kép feltöltése során: {image_file}")
                sys.exit(1)
        else:
            logger.error(f"Nem található termék a következő vonalkóddal: {barcode}")
            print(f"Hiba a kép feltöltése során: {image_file}")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "process_and_upload":
        # Parancssori argumentumok
        if len(sys.argv) < 8:
            print("Használat: python photoroom_shopify_integration.py process_and_upload <image_file> <photoroom_api_key> <shopify_api_key> <shopify_password> <shopify_store> <output_dir> [background_color]")
            sys.exit(1)
        
        image_file = sys.argv[2]
        photoroom_api_key = sys.argv[3]
        shopify_api_key = sys.argv[4]
        shopify_password = sys.argv[5]
        shopify_store = sys.argv[6]
        output_dir = sys.argv[7]
        background_color = sys.argv[8] if len(sys.argv) > 8 else 'white'
        
        # Kép feldolgozása és feltöltése
        if process_and_upload_image(image_file, photoroom_api_key, shopify_api_key, shopify_password, shopify_store, output_dir, background_color):
            print(f"Kép sikeresen feldolgozva és feltöltve: {image_file}")
        else:
            print(f"Hiba a kép feldolgozása és feltöltése során: {image_file}")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "batch_process":
        # Parancssori argumentumok
        if len(sys.argv) < 8:
            print("Használat: python photoroom_shopify_integration.py batch_process <input_dir> <photoroom_api_key> <shopify_api_key> <shopify_password> <shopify_store> <output_dir> [background_color] [batch_size] [delay] [max_workers]")
            sys.exit(1)
        
        input_dir = sys.argv[2]
        photoroom_api_key = sys.argv[3]
        shopify_api_key = sys.argv[4]
        shopify_password = sys.argv[5]
        shopify_store = sys.argv[6]
        output_dir = sys.argv[7]
        background_color = sys.argv[8] if len(sys.argv) > 8 else 'white'
        batch_size = int(sys.argv[9]) if len(sys.argv) > 9 else 5
        delay = float(sys.argv[10]) if len(sys.argv) > 10 else 0.2
        max_workers = int(sys.argv[11]) if len(sys.argv) > 11 else 4
        
        # Batch feldolgozás
        if process_batch(input_dir, output_dir, photoroom_api_key, shopify_api_key, shopify_password, shopify_store, background_color, batch_size, delay, max_workers):
            print(f"Batch feldolgozás sikeresen befejezve: {input_dir}")
        else:
            print(f"Hiba a batch feldolgozás során: {input_dir}")
            sys.exit(1)
    else:
        # Parancssori argumentumok
        args = parse_args()
        
        # Debug mód beállítása
        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mód bekapcsolva")
            logger.debug(f"Parancssori argumentumok: {args}")
        
        # Ellenőrizzük, hogy megadtak-e bemeneti könyvtárat vagy képfájlt
        if args.input_dir:
            # Batch feldolgozás
            if process_batch(args.input_dir, args.output_dir, args.photoroom_api_key, args.shopify_api_key, args.shopify_password, args.shopify_store, args.background_color, args.batch_size, args.delay, max_workers=4):
                print(f"Batch feldolgozás sikeresen befejezve: {args.input_dir}")
            else:
                print(f"Hiba a batch feldolgozás során: {args.input_dir}")
                sys.exit(1)
        elif args.image_file:
            # Kép feldolgozása és feltöltése
            if process_and_upload_image(args.image_file, args.photoroom_api_key, args.shopify_api_key, args.shopify_password, args.shopify_store, args.output_dir, args.background_color):
                print(f"Kép sikeresen feldolgozva és feltöltve: {args.image_file}")
            else:
                print(f"Hiba a kép feldolgozása és feltöltése során: {args.image_file}")
                sys.exit(1)
        else:
            print("Hiba: Meg kell adni vagy egy képfájlt (--image-file) vagy egy bemeneti könyvtárat (--input-dir)")
            sys.exit(1) 