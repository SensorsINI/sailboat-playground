"""
Simulation Manager - Core Physics Integration and Coordination

This module implements the central simulation manager that coordinates all physical
interactions in the sailing simulation. The Manager class integrates boat dynamics,
environmental forces, and agent control into a unified simulation step.

## Architecture Overview

The Manager acts as the main simulation controller that:
- Coordinates between Boat physics and Environment dynamics
- Computes and applies all physical forces (wind, water, rudder)
- Manages simulation state and provides agent interface
- Handles debug logging and state monitoring

## Force Integration System

The Manager integrates multiple force sources in each simulation step:

### 1. Wind Forces on Sail
- **Apparent Wind Calculation**: Computes wind relative to boat motion
- **Sail Aerodynamics**: Uses foil lookup tables for lift/drag coefficients
- **Driving Force**: Projects total sail force onto boat heading direction
- **Angle Normalization**: Handles wind angle wrapping and sail angle calculations

### 2. Water Forces on Hull
- **Apparent Water Current**: Computes water flow relative to boat motion
- **Hull Resistance**: Applies friction forces based on hull area and coefficients
- **Drag Forces**: Opposes boat motion through water

### 3. Water Forces on Rudder
- **Rudder Aerodynamics**: Computes lift/drag forces on rudder surface
- **Torque Generation**: Creates rotational forces for steering control
- **Angular Dynamics**: Applies torque to boat's moment of inertia

## State Management

### Complete State (`state` property)
Provides full simulation state including:
- Environmental conditions (wind/water speeds)
- Boat kinematics (position, speed, heading)
- Control surfaces (sail angle, rudder angle)

### Agent State (`agent_state` property)
Provides simplified state for sailing algorithms:
- Boat heading and position
- Apparent wind speed and direction
- Essential navigation information

## Physics Constants and Scaling

- **Force Scaling**: Uses 10x multiplier for numerical stability
- **Time Integration**: Uses fixed timestep from constants
- **Angle Resolution**: Requires integer angles for foil lookup tables
- **Coordinate System**: Maintains trigonometric circle convention

## Simulation Loop

The `step()` method implements the complete physics integration:
1. Apply agent controls (sail/rudder angles)
2. Compute apparent wind and water velocities
3. Calculate all force components
4. Apply forces and torques to boat
5. Integrate boat and environment states
6. Update simulation time

## Error Handling

- Validates agent input format (requires [alpha, rudder_angle] list)
- Handles angle normalization throughout force calculations
- Provides debug logging for physics troubleshooting
"""

__all__ = ["Manager"]

import json
import os
import time

import numpy as np
from numpy.linalg.linalg import norm
from sailboat_playground.engine.utils import *
from sailboat_playground.engine.Boat import Boat
from sailboat_playground.constants import constants
from sailboat_playground.engine.Environment import Environment


class Manager:
    def __init__(
        self,
        boat_config: str,
        env_config: str,
        foils_dir: str = "foils/",
        debug: bool = False,
        boat_heading: float = 90,
        boat_position: np.ndarray = np.array([0, 0]),
        state_log_path: str | None = None,
    ):
        self._boat = Boat(boat_config, foils_dir)
        self._boat.set_heading(boat_heading)
        self._boat.set_position(boat_position)
        self._env = Environment(env_config)
        self._apparent_wind_speed = 0
        self._apparent_wind_direction = 0
        self._debug = debug
        self._last_force_components = {
            "sail": np.array([0.0, 0.0]),
            "keel": np.array([0.0, 0.0]),
            "hull": np.array([0.0, 0.0]),
            "total": np.array([0.0, 0.0]),
        }
        self._last_angular_acceleration = 0.0
        self._step_index = 0
        self._state_log_path = state_log_path
        if self._state_log_path:
            log_dir = os.path.dirname(self._state_log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            with open(self._state_log_path, "w", encoding="utf-8") as _state_log:
                _state_log.write("")
        self._log_state("init")
        self._last_angular_acceleration = 0.0
        # Tracks the previous "side" (+1/-1) the sail was on for smooth gybe transitions.
        # By convention:
        #   +1 = sail is out on the starboard ("right") side – i.e., wind is from port/left.
        #   -1 = sail is out on the port ("left") side – i.e., wind is from starboard/right.
        self._last_sail_sign = 1.0
        # Deadband (in degrees) for sail side changes, helps prevent rapid switching near dead downwind.
        self._sail_side_deadband = 5.0

    def log(self, *args, **kwargs):
        if self._debug:
            print(*args, **kwargs)

    @property
    def boat(self):
        return self._boat

    @property
    def environment(self):
        return self._env

    @property
    def state(self):
        return {
            "wind_speed": self._env.wind_speed,
            "water_speed": self._env.water_speed,
            "boat_heading": self._boat.heading,
            "boat_speed": self._boat.speed,
            "boat_speed_direction": compute_angle(self._boat.speed),
            "boat_position": self._boat.position,
            "sail_angle": self._boat.alpha,
            "rudder_angle": self._boat.rudder_angle,
        }

    @property
    def agent_state(self):
        return {
            "heading": self._boat.heading,
            "wind_speed": self._apparent_wind_speed,
            "wind_direction": self._apparent_wind_direction,
            "position": self._boat.position,
        }

    @classmethod
    def compute_force(cls, rho, velocity, area, coeff):
        # Scale factor to make forces appropriate for simulation
        # Original formula gives correct physics but too small for numerical stability.
        # Hydrodynamic forces are naturally larger due to water density; keep them closer to
        # physical magnitudes by using a smaller scale factor in water.
        force_scale = 10 if rho <= 10 else 1
        return force_scale * 1 / 2 * rho * (velocity**2) * area * coeff

    def print_current_state(self):
        self.log("*" * 15)
        self.log("*** Current Manager state:")
        self.log("True wind speed: {}".format(self._env.wind_speed))
        self.log("True water speed: {}".format(self._env.water_speed))
        self.log("Boat heading: {}".format(self._boat.heading))
        self.log("Boat speed: {}".format(self._boat.speed))
        self.log(
            "Boat speed direction: {}".format(
                compute_angle(self._boat.speed) * 180 / np.pi
            )
        )
        self.log("Boat position: {}".format(self._boat.position))
        self.log("Sail angle of attack: {}".format(self._boat.alpha))
        self.log("Rudder angle of attack: {}".format(self._boat.rudder_angle))
        self.log("*" * 15)

    def step(self, ans: list):
        if type(ans) != list or len(ans) != 2:
            raise Exception(
                'Argument "ans" for Manager.step() must be a list with two values: [alpha, rudder_angle]'
            )
        self._log_state("pre-step")
        self.apply_agent(ans[0], ans[1])
        self.print_current_state()
        total_force = np.array([0.0, 0.0])
        # 1 - Wind forces on sail
        # 1.1 - Compute apparent wind
        self.log("----------- Wind forces on sail")
        Va_raw = self._env.wind_speed - self._boat.speed
        self.log(f"Va_raw={Va_raw}")
        Va = self._sanitize_relative_velocity(Va_raw)
        if not np.allclose(Va, Va_raw):
            self.log(f"Va_clamped={Va}")
        Va_angle = compute_angle(Va) * 180 / np.pi
        # Compute the apparent wind direction relative to the boat's heading.
        # Sign convention: Positive values indicate apparent wind coming from the starboard (right) side
        # of the boat (relative to heading), negative from port (left) side.
        apparent_wind_direction = Va_angle - self._boat.heading
        while apparent_wind_direction < -180:
            apparent_wind_direction += 360
        while apparent_wind_direction > 180:
            apparent_wind_direction -= 360
        self._apparent_wind_direction = apparent_wind_direction
        global_sail_angle = self._boat.heading + self._boat.alpha
        while global_sail_angle < 0:
            global_sail_angle += 360
        while global_sail_angle > 360:
            global_sail_angle -= 360
        self.log(f"global_sail_angle={global_sail_angle}")
        # Explanation:
        # "alpha" here represents the angle of attack of the sail, i.e., the angle between the apparent wind direction (the wind as perceived by the moving boat)
        # and the orientation of the sail itself (in global coordinates). The sail's effectiveness depends critically on this angle.
        #
        # Logic:
        # 1. Retrieve the commanded sail angle (relative to the boat), and determine its magnitude and sign.
        # 2. If the commanded sail sign is zero (i.e., no trim), persist the previous sail sign to maintain sail side.
        # 3. Determine which side of the boat the sail should be on:
        #    - If the apparent wind is almost aligned with the boat's axis (inside a deadband), keep the current/commanded sign.
        #    - Otherwise, set sail to opposite side: negative sign if apparent wind comes from starboard, positive if from port.
        #    This ensures the sail always falls on the appropriate downwind side for correct physics when tacking/jibing.
        # 4. Persist this sail "side" for the next step.
        # 5. Reapply the sign to the magnitude to form the adjusted (possibly flipped) sail alpha.
        # 6. If an adjustment was made, update the boat's alpha.
        # 7. Recompute the global sail angle with the possibly-updated alpha.
        # 8. Finally, compute the angle of attack (alpha): difference between apparent wind angle and global sail angle.
        alpha_cmd = self._boat.alpha  # The sail trim angle as set by agent [-max, +max], in degrees, relative to boat heading
        alpha_magnitude = abs(alpha_cmd)
        commanded_sign = np.sign(alpha_cmd) if alpha_magnitude > 0 else 0.0
        if commanded_sign == 0:
            commanded_sign = self._last_sail_sign
        # Determine which side to put the sail on:
        # - If apparent wind direction is within a deadband, stick with current sign.
        # - Otherwise, flip to correct side based on the sign of the apparent wind direction:
        #   negative apparent wind means wind is coming from *port* (left) side: set sail on starboard (right): +1.0
        #   positive apparent wind means wind is coming from *starboard* (right): set sail on port (left): -1.0
        if abs(self._apparent_wind_direction) < self._sail_side_deadband:
            desired_sign = commanded_sign
        else:
            desired_sign = -1.0 if self._apparent_wind_direction >= 0 else 1.0
        self._last_sail_sign = desired_sign
        adjusted_alpha = desired_sign * alpha_magnitude
        if adjusted_alpha != self._boat.alpha:
            self.log(f"Adjusted sail alpha from {self._boat.alpha} to {adjusted_alpha}")
            self._boat.set_alpha(int(adjusted_alpha))
            global_sail_angle = self._boat.heading + self._boat.alpha
            while global_sail_angle < 0:
                global_sail_angle += 360
            while global_sail_angle > 360:
                global_sail_angle -= 360
            self.log(f"global_sail_angle (adjusted)={global_sail_angle}")
        # Final sail *angle of attack* (alpha, in degrees) is the difference between apparent wind angle and sail orientation in global frame
        alpha = Va_angle - global_sail_angle
        while alpha < -180:
            alpha += 360
        while alpha > 180:
            alpha -= 360
        self.log(f"Va_angle={Va_angle}")
        self.log(f"alpha={alpha}")
        Va_norm = np.linalg.norm(Va)
        self._apparent_wind_speed = Va_norm
        self.log(f"Va_norm={Va_norm}")
        # 1.2 - Compute total force (in order to check driving force direction)
        D_norm = abs(
            self.compute_force(
                constants.wind_rho,
                Va_norm,
                self._boat.config["sail_area"],
                self._boat.sail_df[self._boat.sail_df["alpha"] == round(alpha)][
                    "cd"
                ].values[0],
            )
        )
        self.log(f"D_norm={D_norm}")
        D_angle = Va_angle
        self.log(f"D_angle={D_angle}")
        D = norm_to_vector(D_norm, D_angle * np.pi / 180)
        self.log(f"D={D}")
        L_norm = abs(
            self.compute_force(
                constants.wind_rho,
                Va_norm,
                self._boat.config["sail_area"],
                self._boat.sail_df[self._boat.sail_df["alpha"] == round(alpha)][
                    "cl"
                ].values[0],
            )
        )
        self.log(f"L_norm={L_norm}")
        if self._boat.alpha > 0:
            L_angle = D_angle + 90
        else:
            L_angle = D_angle - 90
        while L_angle > 360:
            L_angle -= 360
        while L_angle < 0:
            L_angle += 360
        self.log(f"L_angle={L_angle}")
        L = norm_to_vector(L_norm, L_angle * np.pi / 180)
        self.log(f"L={L}")
        F_T = L + D
        self.log(f"F_T={F_T}")
        # 1.3 - Split total force into along-hull drive + lateral slip component
        heading_rad = self._boat.heading * np.pi / 180
        forward_axis = norm_to_vector(1, heading_rad)

        F_drive = np.dot(F_T, forward_axis) * forward_axis
        self.log(f"F_drive={F_drive}")

        # Any residual force represents side-force from the sail and generates leeway ("slip").
        F_lateral_raw = F_T - F_drive

        # Empirical slip coefficient: hull prevents most of the lateral impulse, but a portion
        # still pushes the boat sideways. Tweakable constant chosen conservatively (< 1.0).
        SLIP_FORCE_COEFF = 0.25
        F_slip = SLIP_FORCE_COEFF * F_lateral_raw
        self.log(f"F_slip_raw={F_lateral_raw}")
        self.log(f"F_slip_applied={F_slip}")

        sail_force = F_drive + F_slip
        self.log(f"* Adding sail_force={sail_force}")
        total_force += sail_force

        # # 2 - Water forces on hull
        # # 2.1 - Compute apparent water current
        self.log("----------- Water forces on hull")
        Wa_raw = self._env.water_speed - self._boat.speed
        self.log(f"Wa_raw={Wa_raw}")
        Wa = self._sanitize_relative_velocity(Wa_raw)
        if not np.allclose(Wa, Wa_raw):
            self.log(f"Wa_clamped={Wa}")
        Wa_angle = compute_angle(Wa) * 180 / np.pi
        while Wa_angle < 0:
            Wa_angle += 360
        while Wa_angle > 360:
            Wa_angle -= 360
        self.log(f"Wa_angle={Wa_angle}")
        Wa_norm = np.linalg.norm(Wa)
        self.log(f"Wa_norm={Wa_norm}")
        # 2.2 - Compute water resistance on hull
        F_WR_norm = abs(
            self.compute_force(
                constants.sea_water_rho,
                Wa_norm,
                self._boat.config["hull_area"],
                self._boat.config["hull_friction_coefficient"],
            )
        )
        self.log(f"F_WR_norm={F_WR_norm}")
        F_WR = norm_to_vector(F_WR_norm, Wa_angle * np.pi / 180)
        self.log(f"F_WR={F_WR}")
        self.log(f"* Adding {F_WR}")
        hull_force = F_WR
        # 2.3 - Apply forces
        total_force += hull_force

        # 2.4 - Water forces on keel (lateral damping + yaw torque)
        keel_force = np.array([0.0, 0.0])
        keel_torque = 0.0
        keel_area = self._boat.config.get("keel_area", 0.0)
        if keel_area > 0 and self._boat.keel_df is not None and Wa_norm > 0:
            self.log("----------- Water forces on keel")
            keel_heading = self._boat.heading
            keel_angle = (Wa_angle - keel_heading + 180) % 360 - 180
            keel_alpha = int(np.clip(np.round(keel_angle), -180, 180))
            keel_cd_row = self._boat.keel_df[self._boat.keel_df["alpha"] == keel_alpha]
            if not keel_cd_row.empty:
                keel_cd = keel_cd_row["cd"].values[0]
                keel_cl = keel_cd_row["cl"].values[0]
                if not (np.isfinite(keel_cd) and np.isfinite(keel_cl)):
                    self.log(
                        f"Non-finite keel coefficients (cd={keel_cd}, cl={keel_cl}); skipping keel force."
                    )
                else:
                    D_norm_keel = abs(
                        self.compute_force(
                            constants.sea_water_rho,
                            Wa_norm,
                            keel_area,
                            keel_cd,
                        )
                    )
                    D_keel = norm_to_vector(D_norm_keel, Wa_angle * np.pi / 180)

                    if keel_angle > 0:
                        L_angle_keel = Wa_angle - 90
                    else:
                        L_angle_keel = Wa_angle + 90
                    while L_angle_keel > 360:
                        L_angle_keel -= 360
                    while L_angle_keel < 0:
                        L_angle_keel += 360

                    L_norm_keel = abs(
                        self.compute_force(
                            constants.sea_water_rho,
                            Wa_norm,
                            keel_area,
                            keel_cl,
                        )
                    )
                    L_keel = norm_to_vector(L_norm_keel, L_angle_keel * np.pi / 180)

                    keel_force_candidate = L_keel + D_keel
                    if not np.all(np.isfinite(keel_force_candidate)):
                        self.log(
                            f"Non-finite keel force encountered ({keel_force_candidate}); skipping keel contribution."
                        )
                    else:
                        keel_force = keel_force_candidate
                        total_force += keel_force

                        heading_rad = np.radians(self._boat.heading)
                        forward = np.array([np.cos(heading_rad), np.sin(heading_rad)])
                        keel_offset = self._boat.config.get(
                            "keel_distance_from_com", 0.0
                        )
                        lever_vector_keel = keel_offset * forward
                        keel_torque = (
                            lever_vector_keel[0] * keel_force[1]
                            - lever_vector_keel[1] * keel_force[0]
                        )
                        self.log(f"keel_force={keel_force}")
                        self.log(f"keel_torque={keel_torque}")
            else:
                self.log(
                    f"No keel foil data for alpha={keel_alpha}, skipping keel force."
                )

        # 3 - Water forces on rudder
        # 3.1 - Compute water force on rudder
        self.log("----------- Water forces on rudder")
        global_rudder_angle = self._boat.heading + self._boat.rudder_angle
        while global_rudder_angle < 0:
            global_rudder_angle += 360
        while global_rudder_angle > 360:
            global_rudder_angle -= 360
        # Compute the angle of attack ("alpha") of the rudder relative to the apparent water flow ("Wa").
        # Wa_angle: direction of apparent water flow (relative to East, degrees, 0-360), i.e., where the water is moving FROM, in the global frame.
        # global_rudder_angle: rudder's direction in global frame (boat heading + rudder angle), degrees, 0-360.
        # The 'rudder_angle' here is the angle between the incoming water and the rudder:
        #   - Positive: water hits the starboard (right) side of the rudder (rudder to port).
        #   - Negative: water hits the port (left) side of the rudder (rudder to starboard).
        # This value is wrapped to [-180, 180] for consistent foil lookup.
        rudder_angle = (Wa_angle - global_rudder_angle + 180) % 360 - 180
        D_norm = abs(
            self.compute_force(
                constants.sea_water_rho,
                Wa_norm,
                self._boat.config["rudder_area"],
                self._boat.rudder_df[
                    self._boat.rudder_df["alpha"] == round(rudder_angle)
                ]["cd"].values[0],
            )
        )
        self.log(f"D_norm={D_norm}")
        # Compute the direction of the rudder drag ("D") force.
        # Explanation:
        #   - The drag force on the rudder always acts in the same direction as the 
        #     oncoming water flow relative to the rudder (i.e., directly opposes the water's movement 
        #     over the rudder surface).
        #   - Here, D_angle is set to Wa_angle, which is the global angle (degrees, 0-360, trigonometric convention)
        #     from which the apparent water is flowing. This means the drag vector points
        #     exactly opposite to the water's incoming direction as experienced by the rudder.
        #   - This is necessary because drag always resists the relative fluid motion: the rudder's drag
        #     does not depend on the rudder's orientation, only on the velocity (Wa) *direction* and magnitude.
        D_angle = Wa_angle
        self.log(f"D_angle={D_angle}")
        # Convert D_angle from degrees to radians for vector construction,
        # then create the force vector of magnitude D_norm in direction D_angle.
        D = norm_to_vector(D_norm, D_angle * np.pi / 180)
        self.log(f"D={D}")
        L_norm = abs(
            self.compute_force(
                constants.sea_water_rho,
                Wa_norm,
                self._boat.config["rudder_area"],
                self._boat.rudder_df[
                    self._boat.rudder_df["alpha"] == round(rudder_angle)
                ]["cl"].values[0],
            )
        )
        self.log(f"L_norm={L_norm}")
        if self._boat.rudder_angle > 0:
            L_angle = D_angle - 90
        else:
            L_angle = D_angle + 90
        while L_angle > 360:
            L_angle -= 360
        while L_angle < 0:
            L_angle += 360
        self.log(f"L_angle={L_angle}")
        L = norm_to_vector(L_norm, L_angle * np.pi / 180)
        self.log(f"L={L}")
        F_T = L + D
        self.log(f"F_T={F_T}")
        # 3.2 - Compute torque via lever arm cross product (rudder behind COM)
        heading_rad = np.radians(self._boat.heading)
        lever_arm = self._boat.config["length"] - self._boat.config["com_length"]
        forward = np.array([np.cos(heading_rad), np.sin(heading_rad)])
        lever_vector = -lever_arm * forward
        torque = lever_vector[0] * F_T[1] - lever_vector[1] * F_T[0]
        self.log(f"torque={torque}")

        # 3.3 - Apply rotational damping based on angular-induced water flow
        angular_speed_rad = np.radians(self._boat.angular_speed)
        if abs(angular_speed_rad) > 0:
            tangential_speed = abs(angular_speed_rad) * lever_arm
            damping_force = self.compute_force(
                constants.sea_water_rho,
                tangential_speed,
                self._boat.config["hull_area"],
                self._boat.config["hull_rotation_resistance"],
            )
            damping_torque = -np.sign(angular_speed_rad) * damping_force * lever_arm
        else:
            damping_torque = 0.0
        self.log(f"damping_torque={damping_torque}")

        if not np.isfinite(keel_torque):
            self.log("Keel torque was non-finite; resetting to 0.")
            keel_torque = 0.0
        net_torque = torque + keel_torque + damping_torque
        self.log(f"net_torque={net_torque}")

        if not np.isfinite(net_torque):
            self.log("Non-finite net torque encountered; resetting to 0.")
            net_torque = 0.0
        angular_acceleration_rad = net_torque / self._boat.config["moment_of_inertia"]
        angular_acceleration_deg = np.degrees(angular_acceleration_rad)
        self.log(f"angular_acceleration_deg_raw={angular_acceleration_deg}")

        MAX_ANGULAR_ACCEL = 720.0  # deg/s^2 physical safety limit
        if angular_acceleration_deg > MAX_ANGULAR_ACCEL:
            angular_acceleration_deg = MAX_ANGULAR_ACCEL
        elif angular_acceleration_deg < -MAX_ANGULAR_ACCEL:
            angular_acceleration_deg = -MAX_ANGULAR_ACCEL
        self.log(f"angular_acceleration_deg_clamped={angular_acceleration_deg}")

        self._boat.apply_angular_acceleration(angular_acceleration_deg)
        self._last_angular_acceleration = angular_acceleration_deg

        # 4 - Apply all forces
        if not np.all(np.isfinite(total_force)):
            self.log(
                f"Non-finite total force encountered ({total_force}); zeroing for stability."
            )
            total_force = np.nan_to_num(
                total_force, nan=0.0, posinf=0.0, neginf=0.0
            )
        self.log(f"--> Applying total_force={total_force}")
        self._boat.apply_force(total_force)
        self._last_force_components = {
            "sail": sail_force,
            "hull": hull_force,
            "keel": keel_force,
            "total": total_force,
        }

        # 4 - Execute boat and environment
        self._boat.execute()
        self._env.execute()
        self._log_state("post-step")
        self._step_index += 1

    def apply_agent(self, alpha, rudder_angle):
        # Convert to integers for foil lookup (foil data has integer angle resolution)
        self._boat.set_alpha(int(alpha))
        self._boat.set_rudder_angle(int(rudder_angle))

    def _sanitize_relative_velocity(self, vec: np.ndarray) -> np.ndarray:
        """
        Clamp apparent fluid velocities to prevent runaway force calculations.
        """
        MAX_RELATIVE_SPEED = 50.0  # m/s cap for apparent wind/current
        if vec is None:
            return np.zeros(2)
        norm_val = np.linalg.norm(vec)
        if not np.isfinite(norm_val) or norm_val == 0:
            return np.zeros(2)
        if norm_val > MAX_RELATIVE_SPEED:
            scale = MAX_RELATIVE_SPEED / norm_val
            return vec * scale
        return vec

    def _log_state(self, phase: str):
        """
        Append a JSON record of the current simulation state to the debug log file.
        """
        if not self._state_log_path:
            return
        try:
            snapshot = {
                "timestamp": time.time(),
                "step": self._step_index,
                "phase": phase,
                "state": self.state,
                "force_components": self._last_force_components,
                "angular_acceleration_deg": self._last_angular_acceleration,
            }
            with open(self._state_log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(snapshot, default=self._json_default) + "\n")
        except Exception as exc:
            self.log(f"Failed to write state log: {exc}")

    @staticmethod
    def _json_default(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (np.floating, float)):
            return float(value)
        if isinstance(value, (np.integer, int)):
            return int(value)
        return value
