#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple PhotoRoom API Request

Ez a szkript pontosan a felhasználó által megadott kódot használja a PhotoRoom API-val.
"""

import requests

headers = {
    'x-api-key': 'sandbox_f5a0cd1aeff027ca3084a3dad7b40462c3862a7a'
}

response = requests.get('https://image-api.photoroom.com/v2/edit?background.color=EBECF0&ignorePaddingAndSnapOnCroppedSides=false&outputSize=1600x2000&segmentation.mode=keepSalientObject&segmentation.prompt=product&segmentation.negativePrompt=hand%2C%20finger&shadow.mode=ai.soft&lighting.mode=ai.auto&marginTop=0%25&marginBottom=0%25&marginLeft=0%25&marginRight=0%25&paddingTop=12%25&paddingBottom=12%25&paddingLeft=12%25&paddingRight=12%25&format=webp&imageUrl=IMAGE_URL_GOES_HERE', headers=headers)

with open('output.webp', 'wb') as f:
    f.write(response.content)

print("Kép feldolgozva és mentve: output.webp") 