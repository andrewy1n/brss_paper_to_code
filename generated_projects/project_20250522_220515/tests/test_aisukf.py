import numpy as np
from src.aisukf import AISUKF

def test_initialization():
    aisukf = AISUKF()
    lr_images = [np.random.rand(10,10) for _ in range(5)]
    z, P = aisukf.initialize(lr_images)
    assert z.shape == (1,)
    assert P.shape == (1,1)

def test_sigma_points():
    aisukf = AISUKF()
    z = np.array([1.0])
    P = np.array([[0.1]])
    sigma_points, w_m, w_c = aisukf.compute_sigma_points(z, P)
    assert len(sigma_points) == 3  # 2n+1 where n=1
    assert len(w_m) == 3
    assert len(w_c) == 3

def test_predict_update():
    aisukf = AISUKF()
    z = np.array([1.0])
    P = np.array([[0.1]])
    Q = np.array([[0.01]])
    V = np.array([[0.5]])
    
    # Test predict step
    z_pred, P_pred, _, _, _ = aisukf.predict_step(z, P, Q)
    assert z_pred.shape == (1,)
    assert P_pred.shape == (1,1)
    
    # Test update step
    x_t = np.array([1.1])
    z_upd, P_upd, _, _ = aisukf.update_step(z_pred, P_pred, x_t, V)
    assert z_upd.shape == (1,)
    assert P_upd.shape == (1,1)