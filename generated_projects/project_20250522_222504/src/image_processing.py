import cv2
import numpy as np
from pathlib import Path
from .filters import butterworth_highpass_filter

def read_images(image_paths):
    """Read multiple images from given paths with error handling.
    
    Args:
        image_paths (list): List of paths to image files
        
    Returns:
        list: List of loaded images as numpy arrays
        
    Raises:
        ValueError: If any image fails to load
    """
    images = []
    for path in image_paths:
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"Failed to load image at {path}")
        images.append(image)
    return images

def enhance_image(original_image):
    """Enhance image while preserving gray levels using frequency domain filtering.
    
    Args:
        original_image (numpy.ndarray): Input grayscale image (uint8)
        
    Returns:
        numpy.ndarray: Enhanced image with preserved histogram characteristics
    """
    # Validate input type
    if original_image.dtype != np.uint8:
        raise ValueError("Input image must be uint8 type")
        
    # Preserve low frequencies and enhance mid/high frequencies
    high_pass = butterworth_highpass_filter(original_image, d0=30, order=2)
    
    # Combine original with enhanced details using optimized weights
    enhanced = cv2.addWeighted(original_image, 1.0, high_pass, 0.5, 0)
    
    # Edge-preserving noise reduction
    enhanced = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
    
    return np.clip(enhanced, 0, 255).astype(np.uint8)