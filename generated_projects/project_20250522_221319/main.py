import argparse
import cv2
import numpy as np
from src.utilities import load_image, compute_histogram
from src.image_enhancement import ImageEnhancer
from src.visualizations import plot_images, plot_histograms

def main(input_path: str, output_path: str, cutoff: float = 0.1) -> None:
    """
    Main execution pipeline for image enhancement.
    
    Args:
        input_path: Path to input image
        output_path: Path to save enhanced image
        cutoff: Filter cutoff parameter (0-0.5)
    """
    try:
        image = load_image(input_path)
        enhancer = ImageEnhancer(cutoff=cutoff)
        enhanced = enhancer.enhance(image)
        cv2.imwrite(output_path, enhanced)
        
        plot_images(image, enhanced)
        plot_histograms(compute_histogram(image), compute_histogram(enhanced))
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Multi-spectral Image Enhancement')
    parser.add_argument('-i', '--input', required=True, help='Input image path')
    parser.add_argument('-o', '--output', required=True, help='Output image path')
    parser.add_argument('-c', '--cutoff', type=float, default=0.1, 
                       help='Filter cutoff frequency (0-0.5, default: 0.1)')
    args = parser.parse_args()
    
    main(args.input, args.output, args.cutoff)