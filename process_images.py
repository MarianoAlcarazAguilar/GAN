import cv2
import os
import sys
import pandas as pd

class ImageProcessor:
    def __init__(self):
        self.face_classifier = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.image = None
        
    def load_image(self, image_location:str):
        self.image = cv2.imread(image_location)
        
    def get_image(self):
        return self.image
    
    def identify_face_location(self):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        face = self.face_classifier.detectMultiScale(
            gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        return face
    
    def is_horizontal(self):
        height, width, _ = self.image.shape
        return width > height
    
    def find_location_of_interest(self):
        assert self.image is not None
        
        face = self.identify_face_location()
        is_horizontal = self.is_horizontal()
        height, width, _ = self.image.shape
        
        if isinstance(face, tuple):
            if is_horizontal:
                x_start = (width - height)/2
                x_end = x_start + height
                y_start = 0
                y_end = height
            else:
                x_start = 0
                x_end = width
                y_start = (height - width)/2
                y_end = y_start + width
                
        else:
            # Si no es tupla, hay que ver las ubicaciones medias
            # CUIDADO CON ESTE, A LO MEJOR HAY QUE CAMBIAR ORDEN
            x_mean, y_mean = face.mean(axis=0)[:2]
            if is_horizontal: # Si es horizontal
                if x_mean < width/2: # Y lo importante está del lado izquierdo
                    x_start = 0
                    x_end = x_start + height
                    y_start = 0
                    y_end = height
                else: # Y lo importante está del lado derecho
                    x_start = width - height
                    x_end = width
                    y_start = 0
                    y_end = height
            else: # Si es vertical
                if y_mean < height/2: # Y lo importante está arriba
                    x_start = 0
                    x_end = width
                    y_start = 0
                    y_end = y_start + width
                else: # Y lo importante está abajo
                    x_start = 0
                    x_end = width
                    y_start = height - width
                    y_end = height
                    
        return int(x_start), int(x_end), int(y_start), int(y_end)
    
    def cut_image(self, all_middle=False):
        if all_middle:
            is_horizontal = self.is_horizontal()
            height, width, _ = self.image.shape
            
            if is_horizontal:
                x_start = (width - height)/2
                x_end = x_start + height
                y_start = 0
                y_end = height
            else:
                x_start = 0
                x_end = width
                y_start = (height - width)/2
                y_end = y_start + width
        else:
            x_start, x_end, y_start, y_end = self.find_location_of_interest()
        return self.image[int(y_start):int(y_end), int(x_start):int(x_end)]
    
    def resize_image(self, new_height, new_width):
        return cv2.resize(self.image, (new_width, new_height))
    
def find_new_images(raw_images_location, cut_images_location):
    existing_descriptions = [filename.split('.')[0] for filename in os.listdir(raw_images_location)]
    raw_images = pd.DataFrame({'description':existing_descriptions})
    
    existing_descriptions = [filename.split('.')[0] for filename in os.listdir(cut_images_location)]
    cut_images = pd.DataFrame({'description':existing_descriptions}).assign(raw=False)
    
    merged = raw_images.merge(cut_images, on="description", how="outer", indicator=True)
    not_in_both = merged[merged["_merge"] != "both"]
    return not_in_both.description.apply(lambda x: x+'.png').values

if __name__ == "__main__":
    if len(sys.argv) > 1:
        category = '_'.join(sys.argv[1:]).lower()
    else:
        category = 'people'

    if category == 'people':
        all_middle=False
    else:
        all_middle=True

    images_dir = f'./data/images/{category}'
    training_data_dir = f'./data/training/{category}'
    if not os.path.exists(training_data_dir):
        os.mkdir(training_data_dir)

    #images = os.listdir(f'{images_dir}') # En este tenemos todas las imágenes originales sin cortar
    images = find_new_images(images_dir, training_data_dir)
    print(type(images))
    print(f'Cropping {images.shape[0]} images')
    # Aquí tenemos que identificar cuáles ya existían y cuales aún no para solo procesar esos



    crop_image = ImageProcessor()
    image_size = 300
    for image in images:
        try:
            image_location = f'{images_dir}/{image}'
            crop_image.load_image(image_location)
            
            # Identificamos dónde está lo importante de la imagen
            cut_image = crop_image.cut_image(all_middle=all_middle)
            cut_image = crop_image.resize_image(image_size, image_size)
            
            # Define the compression parameters
            compression_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]  # Adjust compression level (0-9)

            # Save the image with compression
            cv2.imwrite(f'{training_data_dir}/{image}', cut_image)
        except:
            print(f'Unable to crop {image}')
