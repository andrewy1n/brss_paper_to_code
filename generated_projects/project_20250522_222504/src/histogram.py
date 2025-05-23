import matplotlib.pyplot as plt
import numpy as np
import os

def plot_histogram(image, filename):
    """Generate and save histogram plot for image
    
    Args:
        image (numpy.ndarray): Input grayscale image
        filename (str): Output path for histogram plot
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    plt.figure(figsize=(10, 5))
    plt.hist(image.ravel(), bins=256, range=[0, 256], color='blue', alpha=0.7)
    plt.title('Gray Level Distribution')
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()