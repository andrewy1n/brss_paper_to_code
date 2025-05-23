import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

def calculate_psnr(original, super_res):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR)
    """
    return peak_signal_noise_ratio(original, super_res, data_range=255)

def calculate_ssim(original, super_res):
    """
    Calculate Structural Similarity Index Measure (SSIM)
    """
    return structural_similarity(original, super_res, data_range=255, multichannel=True)

def calculate_fsim(original, super_res):
    """
    Calculate Feature Similarity Index Measure (FSIM)
    """
    # Placeholder - actual implementation would require phase congruency calculation
    # This is a simplified version
    from skimage.feature import hog
    fd1 = hog(original, visualize=False)
    fd2 = hog(super_res, visualize=False)
    return np.dot(fd1, fd2) / (np.linalg.norm(fd1) * np.linalg.norm(fd2))

def calculate_epf(original, super_res):
    """
    Calculate Edge Preservation Factor (EPF)
    """
    # Apply Sobel edge detection
    from skimage.filters import sobel
    edges_orig = sobel(original)
    edges_sr = sobel(super_res)
    
    # Calculate correlation coefficient
    cov = np.cov(edges_orig.flatten(), edges_sr.flatten())
    return cov[0,1] / np.sqrt(cov[0,0] * cov[1,1])

def calculate_enl(image, region):
    """
    Calculate Equivalent Number of Looks (ENL) for a homogeneous region
    """
    patch = image[region[0]:region[1], region[2]:region[3]]
    mu = np.mean(patch)
    sigma = np.std(patch)
    return (mu / sigma)**2