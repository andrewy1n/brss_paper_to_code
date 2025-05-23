import numpy as np
import cv2

def butterworth_highpass_filter(image, d0=30, order=2):
    """Butterworth Highpass Filter for frequency domain processing
    
    Args:
        image (numpy.ndarray): Input grayscale image
        d0 (int): Cutoff frequency (default: 30)
        order (int): Filter order (default: 2)
        
    Returns:
        numpy.ndarray: Filtered image in spatial domain
    """
    # Convert to float32 for FFT processing
    img_float = np.float32(image)
    
    # Fast Fourier Transform and shift
    f = np.fft.fft2(img_float)
    fshift = np.fft.fftshift(f)
    
    # Create filter matrix
    rows, cols = image.shape
    center_row, center_col = rows//2, cols//2
    y, x = np.ogrid[-center_row:rows-center_row, -center_col:cols-center_col]
    distance = np.sqrt(x**2 + y**2)
    
    # Butterworth highpass filter formula
    filter_matrix = 1 / (1 + (d0 / (distance + 1e-6))**(2*order)
    
    # Apply filter and inverse FFT
    filtered_shift = fshift * filter_matrix
    f_ishift = np.fft.ifftshift(filtered_shift)
    img_back = np.fft.ifft2(f_ishift)
    
    # Convert to spatial domain and normalize
    result = np.abs(img_back)
    return cv2.normalize(result, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)