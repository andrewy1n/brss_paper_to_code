import matplotlib.pyplot as plt
import numpy as np
from typing import Sequence, Tuple

def plot_images(original: np.ndarray, enhanced: np.ndarray, 
                titles: Tuple[str, str] = ('Original', 'Enhanced')) -> None:
    """
    Displays original and enhanced images side by side.
    
    Args:
        original: Original input image
        enhanced: Enhanced output image
        titles: Tuple of titles for subplots
    """
    plt.figure(figsize=(10, 5))
    for i, (img, title) in enumerate(zip([original, enhanced], titles), 1):
        plt.subplot(1, 2, i)
        plt.imshow(img if img.ndim == 2 else img[..., :3])  # Show first 3 channels for color
        plt.title(title), plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_histograms(original_hist: np.ndarray, enhanced_hist: np.ndarray) -> None:
    """
    Plots comparative histograms for original and enhanced images.
    
    Args:
        original_hist: Histogram data from original image
        enhanced_hist: Histogram data from enhanced image
    """
    plt.figure(figsize=(10, 5))
    colors = ['r', 'g', 'b'] if original_hist.shape[0] > 1 else ['k']
    
    for c in range(original_hist.shape[0]):
        plt.plot(original_hist[c], color=colors[c % 3], linestyle='--', label=f'Original Ch{c+1}')
        plt.plot(enhanced_hist[c], color=colors[c % 3], label=f'Enhanced Ch{c+1}')
    
    plt.title('Histogram Comparison (Per Channel)')
    plt.xlabel('Pixel Value'), plt.ylabel('Normalized Frequency')
    plt.legend(), plt.grid(alpha=0.3)
    plt.show()