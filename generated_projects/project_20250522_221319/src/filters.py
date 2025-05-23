import numpy as np
import cv2
from typing import Tuple

def butterworth_high_pass_filter(shape: Tuple[int, int], cutoff: float, order: int = 2) -> np.ndarray:
    """
    Generates a Butterworth high-pass filter mask in frequency domain.
    
    Args:
        shape: Tuple of (rows, cols) for the filter dimensions
        cutoff: Normalized cutoff frequency (0-0.5)
        order: Filter order (default: 2)
    
    Returns:
        2D numpy array containing the filter mask
    """
    rows, cols = shape
    x = np.linspace(-0.5, 0.5, cols)
    y = np.linspace(-0.5, 0.5, rows)
    xx, yy = np.meshgrid(x, y)
    d = np.sqrt(xx**2 + yy**2)
    # Prevent division by zero with small epsilon
    mask = 1 / (1 + (cutoff/(d + 1e-6))**(2*order))
    return mask

def apply_frequency_filter(image: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    """
    Applies frequency domain filtering to image using Butterworth high-pass filter.
    Handles multi-channel images by processing each channel separately.
    
    Args:
        image: Input image (2D or 3D numpy array)
        cutoff: Normalized cutoff frequency (0-0.5)
        order: Filter order (default: 2)
    
    Returns:
        Filtered image with same dimensions as input
    """
    if image.ndim not in [2, 3]:
        raise ValueError("Input image must be 2D (grayscale) or 3D (multi-channel)")
    
    def process_channel(channel: np.ndarray) -> np.ndarray:
        dft = cv2.dft(np.float32(channel), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        mask = butterworth_high_pass_filter(channel.shape, cutoff, order)
        filtered_shift = dft_shift * mask[..., np.newaxis]
        idft_shift = np.fft.ifftshift(filtered_shift)
        img_back = cv2.idft(idft_shift)
        return cv2.normalize(cv2.magnitude(img_back[:,:,0], img_back[:,:,1]), None, 0, 255, cv2.NORM_MINMAX)

    if image.ndim == 3:
        return np.stack([process_channel(image[:,:,c]) for c in range(image.shape[2])], axis=2).astype(np.uint8)
    return process_channel(image).astype(np.uint8)