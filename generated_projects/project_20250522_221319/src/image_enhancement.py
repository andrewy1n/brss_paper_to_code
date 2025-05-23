import cv2
import numpy as np
from typing import Optional
from .filters import apply_frequency_filter
from .utilities import preserve_grayscale_range

class ImageEnhancer:
    """
    Main image enhancement class implementing the proposed algorithm.
    
    Attributes:
        cutoff: Normalized cutoff frequency (0-0.5)
        order: Filter order for Butterworth filter
        noise_reduction: Enable/disable bilateral filtering
    """
    
    def __init__(self, cutoff: float = 0.1, order: int = 2, noise_reduction: bool = True):
        self.cutoff = cutoff
        self.order = order
        self.noise_reduction = noise_reduction

    def enhance(self, image: np.ndarray) -> np.ndarray:
        """
        Applies complete enhancement pipeline to input image.
        
        Args:
            image: Input image to enhance
        
        Returns:
            Enhanced output image
        """
        enhanced = apply_frequency_filter(image, self.cutoff, self.order)
        enhanced = preserve_grayscale_range(image, enhanced)
        
        if self.noise_reduction:
            enhanced = self._apply_noise_reduction(enhanced)
        
        return enhanced.astype(image.dtype)

    def _apply_noise_reduction(self, image: np.ndarray) -> np.ndarray:
        """Applies bilateral filtering for noise reduction."""
        if image.ndim == 3:
            return cv2.bilateralFilter(image, 9, 75, 75)
        return cv2.bilateralFilter(image, 9, 75, 75)