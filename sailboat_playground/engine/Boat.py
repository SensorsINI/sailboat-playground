"""
Sailboat Physics Model and State Management

This module implements the core physics model for a sailboat in the sailing simulation.
The Boat class manages the boat's physical state, aerodynamic properties, and dynamics.

## Model Structure

The Boat class represents a sailboat with the following components:
- **Sail**: Primary propulsion foil with configurable aerodynamic properties
- **Rudder**: Control surface for steering with separate aerodynamic characteristics
- **Hull**: Main body with mass and physical properties

## Physical State Variables

The boat maintains the following state variables:

### Position and Orientation
- `_position`: 2D position vector [x, y] in meters (Cartesian coordinates)
- `_heading`: Boat orientation in degrees (0° = East, 90° = North, 180° = West, 270° = South)
- `_alpha`: Angle of attack for the sail in degrees

### Kinematics
- `_speed`: 2D velocity vector [vx, vy] in m/s
- `_angular_speed`: Rotational velocity in degrees/second
- `_currentTime`: Current simulation time in seconds

### Control Surfaces
- `_rudder_angle`: Rudder deflection angle in degrees

## Aerodynamic Model

The boat uses lookup tables (CSV files) for foil coefficients:
- **Sail Foil**: Contains lift (cl), drag (cd) coefficients vs. angle of attack
- **Rudder Foil**: Separate coefficients for rudder control surfaces

The model calculates:
- `cr`: Radial force coefficient (forward/backward force)
- `clat`: Lateral force coefficient (side force)

## Physics Integration

The class implements:
- Force application via `apply_force()` (translational dynamics)
- Angular acceleration via `apply_angular_acceleration()` (rotational dynamics)
- State integration via `execute()` (position and heading updates)

## Configuration

Boat properties are loaded from JSON configuration files containing:
- Physical parameters (mass, dimensions)
- Foil specifications (sail_foil, rudder_foil filenames)
- Performance characteristics

## Coordinate System

Uses standard trigonometric circle convention:
- X-axis: East (0°)
- Y-axis: North (90°)
- Positive rotation: Counter-clockwise
- All angles in degrees, positions in meters

## Angle Normalization (2π Cut Problem)

The boat handles the 2π cut problem (angle wrapping) through several mechanisms:

### Heading Normalization
- **Problem**: Heading angles can exceed 360° or go negative during simulation
- **Solution**: The `execute()` method normalizes heading to [0°, 360°) range using while loops:
  ```python
  while self._heading >= 360: self._heading -= 360
  while self._heading < 0: self._heading += 360
  ```
- **Purpose**: Ensures heading always represents a valid compass bearing

### Angular Speed Limits
- **Problem**: Uncontrolled angular acceleration could cause unrealistic spinning
- **Solution**: `apply_angular_acceleration()` clamps angular speed to ±360°/time_delta
- **Purpose**: Prevents the boat from spinning faster than one full rotation per timestep

### Angle Range Consistency
- All angle inputs (sail angle, rudder angle) are expected to be in degrees
- The simulation maintains angle consistency by normalizing only the heading
- Other angles (alpha, rudder_angle) are typically controlled within reasonable ranges by the sailing algorithms
"""

__all__ = ["Boat"]

import json
import numpy as np
from os import path
import pandas as pd
from sailboat_playground.constants import constants, get_time_delta


class Boat:
    def __init__(self, config_file: str, foils_dir: str = "foils/"):
        try:
            with open(config_file, "r") as f:
                self._config = json.loads(f.read())
                f.close()
        except Exception as e:
            raise Exception(f"Failed to load configuration file: {e}")
        self._sail_foil_df = pd.read_csv(
            path.join(foils_dir, f"{self._config['sail_foil']}.csv")
        )
        self._rudder_foil_df = pd.read_csv(
            path.join(foils_dir, f"{self._config['rudder_foil']}.csv")
        )

        # Compute the sail foil angle in radians for trigonometric computations
        self._sail_foil_df["alpha_rad"] = self._sail_foil_df["alpha"] * np.pi / 180

        # Calculate the crosswise force coefficient (cr) for the sail.
        # This combines the lift (cl) and drag (cd) resolved into the crosswise direction
        # relative to the apparent flow, using the angle of attack (alpha_rad).
        # cr = sin(alpha)*cl - cos(alpha)*cd
        self._sail_foil_df["cr"] = (
            np.sin(self._sail_foil_df["alpha_rad"]) * self._sail_foil_df["cl"]
            - np.cos(self._sail_foil_df["alpha_rad"]) * self._sail_foil_df["cd"]
        )

        # Calculate the alongwise force coefficient (clat) for the sail.
        # This is the total force component aligned with the foil chord,
        # essentially the forward or "longitudinal" component in foil coordinates.
        # clat = cos(alpha)*cl + cos(alpha)*cd
        self._sail_foil_df["clat"] = (
            np.cos(self._sail_foil_df["alpha_rad"]) * self._sail_foil_df["cl"]
            + np.cos(self._sail_foil_df["alpha_rad"]) * self._sail_foil_df["cd"]
        )

        # Repeat the same process for the rudder foil: calculate the angle in radians
        self._rudder_foil_df["alpha_rad"] = self._rudder_foil_df["alpha"] * np.pi / 180

        # Calculate the crosswise force coefficient (cr) for the rudder,
        # using lift and drag coefficients and the current angle of attack.
        self._rudder_foil_df["cr"] = (
            np.sin(self._rudder_foil_df["alpha_rad"]) * self._rudder_foil_df["cl"]
            - np.cos(self._rudder_foil_df["alpha_rad"]) * self._rudder_foil_df["cd"]
        )

        # Calculate the alongwise force coefficient (clat) for the rudder,
        # again combining lift and drag along the rudder chord line.
        self._rudder_foil_df["clat"] = (
            np.cos(self._rudder_foil_df["alpha_rad"]) * self._rudder_foil_df["cl"]
            + np.cos(self._rudder_foil_df["alpha_rad"]) * self._rudder_foil_df["cd"]
        )

        self._speed = np.array([0, 0])
        self._angular_speed = 0
        self._position = np.array([0, 0])
        self._currentTime = 0
        self._alpha = 0
        self._rudder_angle = 0
        self._heading = 270

    @property
    def alpha(self):
        return self._alpha

    @property
    def rudder_angle(self):
        return self._rudder_angle

    @property
    def heading(self):
        return self._heading

    @property
    def sail_df(self):
        return self._sail_foil_df

    @property
    def rudder_df(self):
        return self._rudder_foil_df

    @property
    def config(self):
        return self._config

    @property
    def mass(self):
        return self._config["mass"]

    @property
    def speed(self):
        return self._speed

    @property
    def angular_speed(self):
        return self._angular_speed

    @property
    def position(self):
        return self._position

    def apply_force(self, force: np.ndarray):
        """
        Apply a force vector to the boat, updating its velocity.

        Args:
            force (np.ndarray): The force vector [Fx, Fy] applied in the world frame (units: N).

        Explanation:
            This method directly updates the boat's velocity vector (_speed) based on the applied force.
            The input 'force' can have components in any direction in the world (map) coordinate system:
            - If 'force' points exactly along the hull's longitudinal axis (aft to fore), it will accelerate the boat forward or backward.
            - If 'force' has a lateral (sideways) component—across the hull—it can give the boat sideways velocity ("slip" or leeway).
            - There is no restriction to only apply forces along the hull axis: any arbitrary 2D force may be supplied and will be reflected in the resulting velocity vector.

            In typical sailboat simulation, most propulsion is applied along the hull axis (from sail force projected via heading/angle of attack),
            but hydrodynamic modeling—such as leeway, current, and wind forces—can and do result in lateral or oblique force vectors.

            The time integration here is simple explicit Euler:
                v_new = v_old + (F / m) * dt
        """
        self._speed = self._speed + (force / self.mass * get_time_delta())

    def apply_angular_acceleration(self, accel: float):
        self._angular_speed += accel * get_time_delta()
        max_rate = self._config.get("max_angular_speed_deg_s", 90.0)
        if self._angular_speed > max_rate:
            self._angular_speed = max_rate
        if self._angular_speed < -max_rate:
            self._angular_speed = -max_rate

    def execute(self):
        self._currentTime += get_time_delta()
        self._position = self._position + (self._speed * get_time_delta())
        self._heading += self._angular_speed * get_time_delta()
        # Normalize heading to 0-360 range
        while self._heading >= 360:
            self._heading -= 360
        while self._heading < 0:
            self._heading += 360

    def set_alpha(self, alpha):
        self._alpha = alpha

    def set_rudder_angle(self, rudder_angle):
        self._rudder_angle = rudder_angle

    def set_heading(self, heading):
        self._heading = heading

    def set_position(self, position):
        self._position = position
