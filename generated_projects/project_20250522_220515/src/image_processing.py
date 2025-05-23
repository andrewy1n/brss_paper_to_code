import cv2
import numpy as np
from typing import List, Tuple
from skimage import registration

def register_images(lr_images: List[np.ndarray], reference_idx: int = 0) -> List[np.ndarray]:
    """Register LR images to a reference image using subpixel registration.
    
    Args:
        lr_images: List of low-resolution input images
        reference_idx: Index of reference image
        
    Returns:
        List of registered images
        
    Raises:
        ValueError: If input images have different shapes or invalid reference index
    """
    if not lr_images:
        raise ValueError("Input image list cannot be empty")
    if reference_idx < 0 or reference_idx >= len(lr_images):
        raise ValueError("Invalid reference index")
        
    reference = lr_images[reference_idx]
    registered_images = []
    
    for img in lr_images:
        if img.shape != reference.shape:
            raise ValueError("All images must have the same dimensions")
            
        # Estimate shift with subpixel accuracy
        shift, error, _ = registration.phase_cross_correlation(
            reference, img, upsample_factor=10)
        
        # Apply shift using Fourier transform for better accuracy
        registered = np.fft.ifftn(np.fft.fftn(img) * 
                    np.exp(1j * 2 * np.pi * 
                          (shift[0] * np.fft.fftfreq(img.shape[0])[:, None] +
                          shift[1] * np.fft.fftfreq(img.shape[1])))
        registered = np.real(registered)
        
        registered_images.append(registered)
    
    return registered_images

def estimate_noise(image: np.ndarray) -> float:
    """Estimate noise variance from a single image using robust statistics.
    
    Args:
        image: Input image
        
    Returns:
        Estimated noise variance
        
    Raises:
        ValueError: If input image is empty
    """
    if image.size == 0:
        raise ValueError("Input image cannot be empty")
        
    # Use median absolute deviation with correction for SAR speckle noise
    m = np.median(image)
    abs_dev = np.abs(image - m)
    mad = np.median(abs_dev)
    
    # Correction factor for multiplicative noise
    sigma = 1.4826 * mad / (0.6745 * np.sqrt(0.5))
    
    return float(sigma**2)

def prepare_lr_images(lr_images: List[np.ndarray]) -> Tuple[List[np.ndarray], List[float]]:
    """Prepare LR images by registering and estimating noise.
    
    Args:
        lr_images: List of low-resolution input images
        
    Returns:
        Tuple containing:
            - registered_images: List of registered images
            - noise_variances: List of estimated noise variances
            
    Raises:
        ValueError: If input image list is empty
    """
    if not lr_images:
        raise ValueError("Input image list cannot be empty")
        
    registered = register_images(lr_images)
    noise_variances = [estimate_noise(img) for img in registered]
    
    return registered, noise_variances