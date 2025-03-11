#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Termék nevének lekérdezése a vonalkód alapján
"""

import sys
import logging

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_product_name_by_barcode_simulated(barcode):
    """
    Szimulálja a termék nevének lekérdezését a vonalkód alapján
    """
    logger.info(f"Termék nevének keresése vonalkód alapján (szimulált): {barcode}")
    
    # Szimulált termékadatbázis
    products = {
        "10008154177882": "Nike Air Max 270 - Fehér/Fekete",
        "5901234123457": "Adidas Ultraboost 21 - Szürke",
        "12345": "Puma RS-X - Kék/Piros",
        "9780201379624": "Design Patterns: Elements of Reusable Object-Oriented Software",
        "9781449355739": "Learning Python, 5th Edition"
    }
    
    # Termék keresése
    if barcode in products:
        product_name = products[barcode]
        logger.info(f"Termék megtalálva (szimulált): {product_name}")
        return product_name
    else:
        logger.warning(f"Nem található termék a következő vonalkóddal (szimulált): {barcode}")
        return None

def main():
    # Parancssori argumentumok
    if len(sys.argv) < 2:
        print("Használat: python get_product_name.py <barcode>")
        sys.exit(1)
    
    barcode = sys.argv[1]
    
    # Termék nevének lekérdezése
    product_name = get_product_name_by_barcode_simulated(barcode)
    
    if product_name:
        print(f"Termék neve: {product_name}")
    else:
        print(f"Nem található termék a következő vonalkóddal: {barcode}")

if __name__ == "__main__":
    main() 