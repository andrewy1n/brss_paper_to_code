import cv2
import os
from pathlib import Path
from .image_processing import read_images, enhance_image
from .histogram import plot_histogram

def main():
    """Main processing pipeline for image enhancement"""
    try:
        # Create output directories if missing
        Path("data/output_images").mkdir(parents=True, exist_ok=True)
        Path("data/histograms").mkdir(parents=True, exist_ok=True)
        
        image_paths = [
            'data/input_images/image_430nm.tif',
            'data/input_images/image_460nm.tif',
            'data/input_images/image_530nm.tif',
            'data/input_images/image_560nm.tif',
            'data/input_images/image_680nm.tif',
            'data/input_images/image_710nm.tif'
        ]
        
        images = read_images(image_paths)
        
        for idx, img in enumerate(images):
            # Generate original histogram
            plot_histogram(img, f'data/histograms/original_hist_{idx}.png')
            
            # Process image
            enhanced = enhance_image(img)
            
            # Generate enhanced histogram
            plot_histogram(enhanced, f'data/histograms/enhanced_hist_{idx}.png')
            
            # Save result
            cv2.imwrite(f'data/output_images/enhanced_{idx}.tif', enhanced)
            
    except Exception as e:
        print(f"Error processing images: {str(e)}")
        raise

if __name__ == '__main__':
    main()