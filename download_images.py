import pandas as pd
import requests
import os
import sys

# Leemos los sources de las imágenes
if len(sys.argv) > 1:
    category = sys.argv[1].lower()
else:
    category = 'people'

sources_location = f'./data/sources/image_sources_{category}.parquet'
images_location = f'./data/images/{category}'
if not os.path.exists(images_location):
    os.mkdir(images_location)

existing_descriptions = [filename.split('.')[0] for filename in os.listdir(images_location)]
existing_images = pd.DataFrame({'description':existing_descriptions}).assign(previous=True)

sources = pd.read_parquet(sources_location)

new_images = sources.merge(existing_images, on='description', how='left').pipe(lambda df: df.loc[df.previous.isna()])
new_images_found = new_images.shape[0]
print(f'New images found: {new_images_found}')
iteration = 0

for description, source in new_images[['description', 'source']].values:
    if description not in existing_images:
        if iteration % 10 == 0:
            print(f'{iteration}/{new_images_found}')
        response = requests.get(f'{source}')
        with open(f'{images_location}/{description}.png', 'wb') as f:
            f.write(response.content)
        iteration += 1