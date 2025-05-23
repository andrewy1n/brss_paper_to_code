import numpy as np
import cv2
from src.aisukf import AISUKF
from src.image_processing import prepare_lr_images
from src.metrics import calculate_psnr, calculate_ssim

def main():
    # Load LR images (example with synthetic data)
    lr_images = [cv2.imread(f'data/low_res_images/lr_{i}.png', 0) for i in range(5)]
    
    # Prepare images (register and estimate noise)
    registered_images, noise_variances = prepare_lr_images(lr_images)
    
    # Initialize AISUKF
    aisukf = AISUKF()
    
    # Process each pixel (simplified example)
    hr_height, hr_width = lr_images[0].shape[0]*2, lr_images[0].shape[1]*2
    super_res = np.zeros((hr_height, hr_width))
    
    # For each pixel in HR image (simplified - in practice would need proper mapping)
    for i in range(hr_height):
        for j in range(hr_width):
            # Get corresponding LR pixels (simplified)
            lr_i, lr_j = i//2, j//2
            measurements = [img[lr_i, lr_j] for img in registered_images]
            v = np.mean(noise_variances)
            
            # Process pixel
            super_res[i,j] = aisukf.process_pixel(measurements, v)
    
    # Save result
    cv2.imwrite('data/high_res_images/super_res.png', super_res)
    
    # Calculate metrics if ground truth available
    try:
        original = cv2.imread('data/high_res_images/original.png', 0)
        psnr = calculate_psnr(original, super_res)
        ssim = calculate_ssim(original, super_res)
        print(f"PSNR: {psnr:.2f}, SSIM: {ssim:.4f}")
    except:
        print("No ground truth available for metrics calculation")

if __name__ == "__main__":
    main()