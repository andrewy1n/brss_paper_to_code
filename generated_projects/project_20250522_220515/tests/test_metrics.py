import numpy as np
from src.metrics import calculate_psnr, calculate_ssim

def test_psnr():
    original = np.ones((10,10)) * 255
    noisy = original + np.random.normal(0, 10, (10,10))
    psnr = calculate_psnr(original, noisy)
    assert psnr > 0  # Basic sanity check

def test_ssim():
    original = np.ones((10,10)) * 255
    noisy = original + np.random.normal(0, 10, (10,10))
    ssim = calculate_ssim(original, noisy)
    assert 0 <= ssim <= 1  # SSIM should be in [0,1]