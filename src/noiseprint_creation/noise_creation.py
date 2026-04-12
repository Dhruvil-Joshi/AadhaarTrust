import numpy as np
import glob
import matplotlib.pyplot as plt
from src.noiseprint_creation.Noiseprint import *
import os
import cv2
from config import settings

def generate_noiseprint(job_id):
    examples = []
    noiseprints = []

    image_folder = f"{settings.TEMP_PROCESSING_DIR}\\{job_id}"

    for file_path in glob.glob(f'{image_folder}\\*'):
        print(file_path)
        example, noise_print = getNoiseprint(file_path)
        examples.append(example)
        noiseprints.append([file_path.split('\\')[-1].split('.')[0], noise_print, example, file_path])

    output_dir = settings.NOISEPRINT_IMAGES_DIR
    original_cropped_dir = settings.REFINED_IMAGES_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(original_cropped_dir, exist_ok=True)

    border = 10

    for name, res, original_img, file_path in noiseprints:        
        # Crop border from BOTH noiseprint and original image
        if res.shape[0] > 2 * border and res.shape[1] > 2 * border:
            crop_noiseprint = res[border:-border, border:-border]
            crop_original = original_img[border:-border, border:-border]
        else:
            crop_noiseprint = res
            crop_original = original_img
            border = 0
        
        # === Process Noiseprint ===
        # Normalize the cropped noiseprint
        vmin = np.min(crop_noiseprint)
        vmax = np.max(crop_noiseprint)
        norm_crop = np.clip((crop_noiseprint - vmin) / (vmax - vmin + 1e-8), 0, 1)
        
        # Save cropped noiseprint (without padding back)
        filename_noiseprint = os.path.join(output_dir, f"noiseprint_{name}.png")
        plt.imsave(filename_noiseprint, norm_crop, cmap='gray')
        
        # === Process Original Image ===
        # Read the original image directly from file to preserve color
        original_img_color = cv2.imread(file_path)
        
        if original_img_color is not None:
            # Convert BGR to RGB
            original_img_color = cv2.cvtColor(original_img_color, cv2.COLOR_BGR2RGB)
            
            # Apply same crop
            if original_img_color.shape[0] > 2 * border and original_img_color.shape[1] > 2 * border:
                crop_original_color = original_img_color[border:-border, border:-border]
            else:
                crop_original_color = original_img_color
            
            # Save as RGB
            filename_original = os.path.join(original_cropped_dir, f"{name}.png")
            plt.imsave(filename_original, crop_original_color)
        else:
            # Fallback to using the provided original_img
            filename_original = os.path.join(original_cropped_dir, f"{name}.png")
            if len(crop_original.shape) == 3:
                plt.imsave(filename_original, np.clip(crop_original, 0, 1))
            else:
                plt.imsave(filename_original, crop_original, cmap='gray')
    
    print(f"Noiseprints saved to: {output_dir}")
    print(f"Cropped originals saved to: {original_cropped_dir}")
    
    # return filename_noiseprint, filename_original