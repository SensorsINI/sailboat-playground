"""
Manual Keyboard Control Example
===============================

Interactive sailboat-playground demo that mirrors the Argo keyboard controls.

Controls
--------
- Left / Right arrow: adjust rudder (-1 to +1)
- Up / Down arrow   : ease / sheet the sail (-1 to +1)
- Space             : pause / resume physics stepping
- R                 : reset simulation to starting pose
- C                 : center both controls
- Q / Escape        : quit

Notes
-----
- Sail command matches Argo conventions: -1 = sheeted in, +1 = fully eased.
- The example determines the downwind side from apparent wind each step so the
  sail always swings to the correct side automatically.
- Requires pyglet 1.5.x (1.5.17 recommended).
"""

import math
import os
from pathlib import Path
import sys

import numpy as np
import pyglet

EXAMPLES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EXAMPLES_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BOAT_CONFIG = PROJECT_ROOT / "boats" / "sample_boat.json"
ENVIRONMENT_CONFIG = PROJECT_ROOT / "environments" / "playground.json"
FOILS_DIR = PROJECT_ROOT / "foils"

from sailboat_playground.engine import Manager
from sailboat_playground.visualization import Viewer
from sailboat_playground.visualization.utils import map_position


ARENA_SIZE_METERS = 200
INITIAL_POSITION = np.array([0.0, 0.0])
INITIAL_HEADING_DEG = 90.0  # 0° = East, 90° = North

RUDDER_STEP = 0.125  # matches Argo keyboard control granularity
SAIL_STEP = 0.125

MAX_RUDDER_DEG = 30.0
MAX_SAIL_DEG = 45.0
SAIL_SIDE_DEADBAND_DEG = 5.0


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class ManualKeyboardSimulation:
    def __init__(self):
        print("**** Sailboat Playground example: manual_keyboard_control.py")
        print("- Arrow keys: rudder (left/right), sail (up/down)")
        print("- Space toggles pause, R resets, C centers controls")
        print("- W rotates wind CCW, E rotates wind CW (10° steps)")
        print("- Q / ESC quits\n")

        self.viewer = Viewer(map_size=ARENA_SIZE_METERS)
        self.viewer.init()
        self.window = self.viewer._window
        self.window.push_handlers(self.on_key_press)
        self.window.push_handlers(self.on_key_release)

        self.manual_rudder = 0.0  # -1 (left) .. +1 (right)
        self.manual_sail = -1.0    # -1 (sheeted in) .. +1 (fully eased)
        self.paused = False

        self._last_sail_side = 1.0
        self._last_relative_wind = 0.0

        self._state_history = []

        self.wind_direction_deg = 35.0

        self._create_simulator()

        pyglet.clock.schedule_interval(self.update_simulation, 0.1)
        pyglet.clock.schedule_interval(self.print_status, 2.0)

    def _create_simulator(self):
        self.simulation_steps = 0
        self.manager = Manager(
            str(BOAT_CONFIG),
            str(ENVIRONMENT_CONFIG),
            boat_heading=INITIAL_HEADING_DEG,
            boat_position=INITIAL_POSITION,
            foils_dir=str(FOILS_DIR),
        )
        self._state_history.clear()
        self._previous_state = None
        self._apply_wind_direction()

    # ------------------------------------------------------------------
    # Keyboard handling
    # ------------------------------------------------------------------
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.LEFT:
            self.manual_rudder = clamp(self.manual_rudder - RUDDER_STEP, -1.0, 1.0)
        elif symbol == pyglet.window.key.RIGHT:
            self.manual_rudder = clamp(self.manual_rudder + RUDDER_STEP, -1.0, 1.0)
        elif symbol == pyglet.window.key.UP:
            self.manual_sail = clamp(self.manual_sail + SAIL_STEP, -1.0, 1.0)
        elif symbol == pyglet.window.key.DOWN:
            self.manual_sail = clamp(self.manual_sail - SAIL_STEP, -1.0, 1.0)
        elif symbol == pyglet.window.key.C:
            self.manual_rudder = 0.0
            self.manual_sail = -1.0
        elif symbol == pyglet.window.key.SPACE:
            self.paused = not self.paused
        elif symbol == pyglet.window.key.R:
            self._create_simulator()
        elif symbol == pyglet.window.key.W:
            self._rotate_wind(-10.0)
        elif symbol == pyglet.window.key.E:
            self._rotate_wind(10.0)
        elif symbol in (pyglet.window.key.Q, pyglet.window.key.ESCAPE):
            pyglet.app.exit()

    def on_key_release(self, symbol, modifiers):
        # No special handling needed
        return

    def _rotate_wind(self, delta_deg: float):
        self.wind_direction_deg = (self.wind_direction_deg + delta_deg) % 360.0
        self._apply_wind_direction()

    def _apply_wind_direction(self):
        env = self.manager.environment
        if env and hasattr(env, "_config"):
            env._config["wind_direction"] = self.wind_direction_deg

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------
    def update_simulation(self, dt):
        if self.paused:
            return

        agent_state = self.manager.agent_state
        relative_wind = float(agent_state.get("wind_direction", 0.0))

        if math.isnan(relative_wind):
            relative_wind = 0.0

        if abs(relative_wind) < SAIL_SIDE_DEADBAND_DEG:
            sail_side = self._last_sail_side
        else:
            sail_side = 1.0 if relative_wind >= 0.0 else -1.0
        if sail_side == 0.0:
            sail_side = 1.0

        self._last_sail_side = sail_side
        self._last_relative_wind = relative_wind

        sheet_fraction = clamp(0.5 * (self.manual_sail + 1.0), 0.0, 1.0)
        sail_angle_deg = sail_side * sheet_fraction * MAX_SAIL_DEG
        rudder_angle_deg = clamp(self.manual_rudder, -1.0, 1.0) * MAX_RUDDER_DEG

        self.manager.step([int(sail_angle_deg), int(rudder_angle_deg)])
        full_state = self.manager.state

        self._update_viewer(full_state)

        self._state_history.append(full_state)
        self.simulation_steps += 1

    def _update_viewer(self, state):
        boat_position = state["boat_position"]
        mapped_pos = map_position(boat_position, ARENA_SIZE_METERS)
        self.viewer._sailboat.set_position(mapped_pos)
        self.viewer._sailboat.set_rotation(state["boat_heading"])
        self.viewer._sailboat.set_alpha(state["sail_angle"])
        self.viewer._sailboat.set_rudder_angle(state["rudder_angle"])
        self.viewer._sailboat.update(0.0)

        forces = getattr(self.manager, "_last_force_components", None)
        self.viewer.draw_force_vectors(boat_position, forces)
        angular_accel = getattr(self.manager, "_last_angular_acceleration", 0.0)
        self.viewer.draw_torque_arc(boat_position, angular_accel)

        wind_speed = state["wind_speed"]
        self.viewer._draw_wind_vector(wind_speed)
        self.viewer._wind_text.text = f"Wind: {np.linalg.norm(wind_speed):.1f} m/s"
        speed = np.linalg.norm(state["boat_speed"])
        self.viewer._speed_text.text = f"Speed: {speed:.2f} m/s"
        self.viewer._position_text.text = (
            f"Pos: ({boat_position[0]:.1f}, {boat_position[1]:.1f})"
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def print_status(self, dt):
        if not self._state_history:
            return

        latest = self._state_history[-1]
        speed = np.linalg.norm(latest["boat_speed"])
        forces = getattr(self.manager, "_last_force_components", None)
        total_force = np.linalg.norm(forces["total"]) if forces else 0.0
        angular_accel = getattr(self.manager, "_last_angular_acceleration", 0.0)
        print(
            f"Step {self.simulation_steps:4d} | "
            f"Heading {latest['boat_heading']:.1f}° | "
            f"Speed {speed:.2f} m/s | "
            f"Wind rel {self._last_relative_wind:.1f}° | "
            f"Sail cmd {self.manual_sail:+.2f} | Rudder cmd {self.manual_rudder:+.2f} | "
            f"|F| {total_force:.2f} N | α_ddot {angular_accel:.3f}"
        )

    def run(self):
        pyglet.app.run()


if __name__ == "__main__":
    try:
        ManualKeyboardSimulation().run()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        pyglet.app.exit()
