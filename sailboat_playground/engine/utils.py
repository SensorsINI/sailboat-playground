import math
import numpy as np
from sailboat_playground.constants import constants


def compute_angle(vec: np.ndarray):
    """
    Compute the angle of a 2D vector in radians.
    
    Calculates the angle of a 2D vector using atan2 and normalizes the result
    to the range [0, 2π) to handle the 2π cut problem.
    
    Args:
        vec (np.ndarray): 2D vector [x, y] to compute angle for
        
    Returns:
        float: Angle in radians, normalized to [0, 2π)
        
    Raises:
        AssertionError: If input vector is not 2D
        
    Note:
        Uses standard trigonometric convention where:
        - 0 radians = positive X-axis (East)
        - π/2 radians = positive Y-axis (North)
        - π radians = negative X-axis (West)
        - 3π/2 radians = negative Y-axis (South)
    """
    try:
        assert vec.shape == (2,)
    except AssertionError:
        raise AssertionError(
            f"Failed to compute angle on vector with shape different from (2,): Shape is {vec.shape}")
    ang = math.atan2(vec[1], vec[0])
    while ang < 0:
        ang += 2 * np.pi
    while ang > 2 * np.pi:
        ang -= 2 * np.pi
    return ang


def norm_to_vector(norm: float, angle_rad: float):
    """
    Convert magnitude and angle to a 2D vector.
    
    Creates a 2D vector from a magnitude (norm) and angle in radians.
    This is the inverse operation of compute_angle().
    
    Args:
        norm (float): Magnitude of the vector
        angle_rad (float): Angle in radians
        
    Returns:
        np.ndarray: 2D vector [x, y] with specified magnitude and direction
        
    Note:
        Uses standard trigonometric convention where:
        - 0 radians = positive X-axis (East)
        - π/2 radians = positive Y-axis (North)
        - π radians = negative X-axis (West)
        - 3π/2 radians = negative Y-axis (South)
        
    Example:
        >>> norm_to_vector(5.0, 0)
        array([5., 0.])  # Vector pointing East
        
        >>> norm_to_vector(3.0, np.pi/2)
        array([0., 3.])  # Vector pointing North
    """
    return np.array([np.cos(angle_rad), np.sin(angle_rad)]) * norm
