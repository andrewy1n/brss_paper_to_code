import cv2
import numpy as np
from typing import Optional, Tuple

def load_image(path: str) -> np.ndarray:
    """
    Loads an image with preserved data format.
    
    Args:
        path: Path to image file
    
    Returns:
        Loaded image as numpy array
    
    Raises:
        FileNotFoundError: If specified path doesn't exist
    """
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Could not load image from {path}")
    return image

def compute_histogram(image: np.ndarray) -> np.ndarray:
    """
    Computes normalized histogram for single or multi-channel image.
    
    Args:
        image: Input image (2D or 3D numpy array)
    
    Returns:
        Array of histograms (shape: [channels, 256])
    """
    if image.ndim == 3:
        return np.stack([cv2.calcHist([image], [c], None, [256], [0, 256]).flatten() 
                        for c in range(image.shape[2])]) / image.size
    hist = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()
    return (hist / hist.sum()).reshape(1, -1)

def preserve_grayscale_range(original: np.ndarray, enhanced: np.ndarray) -> np.ndarray:
    """
    Preserves original grayscale range in enhanced image.
    
    Args:
        original: Original input image
        enhanced: Enhanced output image
    
    Returns:
        Normalized image maintaining original intensity range
    """
    orig_min = original.min()
    orig_max = original.max()
    clipped = np.clip(enhanced, orig_min, orig_max)
    return cv2.normalize(clipped, None, orig_min, orig_max, cv2.NORM_MINMAX)