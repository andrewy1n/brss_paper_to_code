import numpy as np
from typing import List, Tuple, Optional

class AISUKF:
    """Adaptive Importance Sampling Unscented Kalman Filter for SAR image super-resolution.
    
    Implements the AISUKF algorithm with adaptive noise covariance estimation for
    super-resolution of SAR images.
    
    Attributes:
        alpha: Spread parameter for sigma points (default: 1e-3)
        beta: Incorporation parameter for prior knowledge (default: 2)
        kappa: Secondary scaling parameter (default: 0)
        V0: Initial measurement noise covariance (default: 0.5)
        Q0: Initial process noise covariance (default: 0.01)
        L: Window size for covariance matching (default: 15)
    """
    
    def __init__(self, alpha: float = 1e-3, beta: float = 2, kappa: float = 0):
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        self.V0 = np.array([[0.5]])  # Initial measurement noise covariance
        self.Q0 = np.array([[0.01]])  # Initial process noise covariance
        self.L = 15  # Window size for covariance matching

    def initialize(self, lr_images: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """Initialize intensity estimate and covariance matrix.
        
        Args:
            lr_images: List of low-resolution input images
            
        Returns:
            Tuple containing:
                - initial_estimate: Initial intensity estimate
                - P: Initial covariance matrix
        """
        if not lr_images:
            raise ValueError("Input image list cannot be empty")
            
        base_image = lr_images[0]
        if base_image.size < 5:
            raise ValueError("Base image too small for initialization")
            
        initial_estimate = np.mean(base_image[:5])
        P = np.eye(1) * 0.1  # Small initial covariance
        
        return np.array([initial_estimate]), P

    def compute_sigma_points(self, z: np.ndarray, P: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute sigma points and weights using unscented transform.
        
        Args:
            z: Current state estimate
            P: Current covariance matrix
            
        Returns:
            Tuple containing:
                - sigma_points: Computed sigma points
                - w_m: Mean weights
                - w_c: Covariance weights
        """
        n = len(z)
        lambda_ = self.alpha**2 * (n + self.kappa) - n
        
        # Compute sigma points using vectorized operations
        sigma_points = np.zeros((2*n+1, n))
        sigma_points[0] = z
        sqrt_matrix = np.linalg.cholesky((n + lambda_) * P)
        
        sigma_points[1:n+1] = z + sqrt_matrix.T
        sigma_points[n+1:] = z - sqrt_matrix.T
        
        # Compute weights
        w_m = np.full(2*n+1, 1/(2*(n + lambda_)))
        w_c = w_m.copy()
        w_m[0] = lambda_ / (n + lambda_)
        w_c[0] = w_m[0] + (1 - self.alpha**2 + self.beta)
            
        return sigma_points, w_m, w_c

    def predict_step(self, z_t_minus_1: np.ndarray, P_t_minus_1: np.ndarray, 
                    Q_t_minus_1: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Perform prediction step of AISUKF.
        
        Args:
            z_t_minus_1: Previous state estimate
            P_t_minus_1: Previous covariance matrix
            Q_t_minus_1: Previous process noise covariance
            
        Returns:
            Tuple containing predicted state, covariance, sigma points and weights
        """
        sigma_points, w_m, w_c = self.compute_sigma_points(z_t_minus_1, P_t_minus_1)
        
        # Vectorized prediction calculations
        z1_t_t_minus_1 = np.sum(w_m[:, None] * sigma_points, axis=0)
        diff = sigma_points - z1_t_t_minus_1
        P1_t_t_minus_1 = np.einsum('i,ij,ik->jk', w_c, diff, diff) + Q_t_minus_1
        
        return z1_t_t_minus_1, P1_t_t_minus_1, sigma_points, w_m, w_c

    def update_step(self, z1_t_t_minus_1: np.ndarray, P1_t_t_minus_1: np.ndarray, 
                  x_t: np.ndarray, V_t_minus_1: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Perform update step of AISUKF.
        
        Args:
            z1_t_t_minus_1: Predicted state
            P1_t_t_minus_1: Predicted covariance
            x_t: Current measurement
            V_t_minus_1: Previous measurement noise covariance
            
        Returns:
            Tuple containing updated state, covariance, sigma points and predicted measurement
        """
        sigma_points, w_m, w_c = self.compute_sigma_points(z1_t_t_minus_1, P1_t_t_minus_1)
        
        # Vectorized update calculations
        z2_t_t_minus_1 = np.sum(w_m[:, None] * sigma_points, axis=0)
        diff = sigma_points - z2_t_t_minus_1
        P_IC_t = np.einsum('i,ij,ik->jk', w_c, diff, diff) + V_t_minus_1
        
        diff_prior = sigma_points - z1_t_t_minus_1
        P_CC_t = np.einsum('i,ij,ik->jk', w_c, diff_prior, diff)
        
        # Use pseudo-inverse for numerical stability
        K = P_CC_t @ np.linalg.pinv(P_IC_t)
        
        z_t = z1_t_t_minus_1 + K @ (x_t - z2_t_t_minus_1)
        P_t = P1_t_t_minus_1 - K @ P_IC_t @ K.T
        
        return z_t, P_t, sigma_points, z2_t_t_minus_1

    def process_pixel(self, measurements: List[float], v: float) -> float:
        """Process a single pixel through T iterations.
        
        Args:
            measurements: List of pixel values from LR images
            v: Estimated noise variance
            
        Returns:
            Final estimated pixel intensity
        """
        if not measurements:
            raise ValueError("Measurements list cannot be empty")
            
        # Initialize
        z_t_minus_1, P_t_minus_1 = self.initialize([np.array(measurements)])
        V_t_minus_1 = self.V0
        Q_t_minus_1 = self.Q0
        E_t_hist = []
        
        for x_t in measurements:
            x_t = np.array([x_t])
            
            # Prediction step
            z1_t_t_minus_1, P1_t_t_minus_1, sigma_points_pred, _, _ = self.predict_step(
                z_t_minus_1, P_t_minus_1, Q_t_minus_1)
            
            # Update step
            z_t, P_t, sigma_points_upd, z2_t_t_minus_1 = self.update_step(
                z1_t_t_minus_1, P1_t_t_minus_1, x_t, V_t_minus_1)
            
            # Calculate noise covariances
            E_t = x_t - (z_t * v)
            E_t_hist.append(E_t)
            
            if len(E_t_hist) >= self.L:
                F_t = np.mean(np.square(E_t_hist[-self.L:]))
            else:
                F_t = np.mean(np.square(E_t_hist))
                
            diff = sigma_points_upd - x_t + E_t
            V_t = F_t + np.einsum('i,ij,ik->jk', w_c, diff, diff)
            Q_t = K @ F_t @ K.T
            
            # Update for next iteration
            z_t_minus_1 = z_t
            P_t_minus_1 = P_t
            V_t_minus_1 = V_t
            Q_t_minus_1 = Q_t
        
        return float(z_t[0])