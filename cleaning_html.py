from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import sys

class Scrapper:
    def __init__(self, html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            print(f'Opening html file at {html_file}')
            content = f.read()

        self.source = BeautifulSoup(content, 'html.parser')
        self.image_sources = None
        
    def __extract_ixid(self, url):
        # Utiliza una expresión regular para buscar el valor de "ixid"
        match = re.search(r'ixid=([^&]+)', url)
        
        # Verifica si se encontró el valor "ixid" en la URL
        if match:
            ixid = match.group(1)
            return ixid
        else:
            return None  # Retorna None si "ixid" no se encuentra en la URL
        
    def __is_premium(self, url):
        tipo = url.split('-')[0].split('/')[-1]
        return tipo == 'premium_photo'

    def find_images(self):
        images = self.source.select('img[alt]')
        images = [image for image in images if 'role' not in image.attrs]
        images = [image for image in images if image['style'].replace(' ', '') not in ['display:none;', 'display:none']]
        return images
    
    def get_sources_df(self, images):
        # Creamos los arreglos necesarios para poder tener todas las imágenes en un csv
        descriptions, source = [], []
        for image in images:
            descriptions.append(image['alt'].lower())
            source.append(image['src'])

        # Creamos el dataframe
        extracted_src = (pd
         .DataFrame({'description':descriptions, 'source':source})
         .assign(ixid=lambda df: df.apply(lambda x: self.__extract_ixid(x.source), axis=1))
         .assign(is_premium=lambda df: df.apply(lambda x: self.__is_premium(x.source), axis=1))
         .query('not is_premium')
         )
        self.image_sources = extracted_src
    
    def save_df(self, direcotry, filename):
        if self.image_sources is None:
            print('Not able to update image sources, since the dataframe is None')
            return False
        
        # Abrimos los existentes en caso de que ya estén ahí
        if filename in os.listdir(direcotry):
            existing_sources = pd.read_parquet(f'{direcotry}/{filename}', engine='pyarrow')
        else:
            existing_sources = pd.DataFrame()

        # Guardamos los nuevos
        updated_sources = pd.concat((existing_sources, self.image_sources), ignore_index=True).drop_duplicates(subset=['ixid']).drop_duplicates(subset=['description'])
        updated_sources.to_parquet(f'{direcotry}/{filename}', index=False)
        return True


if __name__ == '__main__':
    # Abrimos el archivo html
    #html_location = './data/unsplash_source.html'
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
    else:
        category = 'people'

    html_location = f'./data/html/unsplash_source_{category}.html'
    scrapper = Scrapper(html_file=html_location)

    # Buscamos las imágenes y guardamos el df en el atributo del objeto
    images = scrapper.find_images()
    scrapper.get_sources_df(images)
    
    # Actualizamos/Creamos el parquet
    #scrapper.save_df('data', 'image_sources.parquet')
    scrapper.save_df('data/sources', f'image_sources_{category}.parquet')
    




