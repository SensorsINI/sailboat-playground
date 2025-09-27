import numpy as np
import pyglet
from sailboat_playground.engine import Manager
from sailboat_playground.visualization import Viewer
from sailboat_playground.engine.utils import compute_angle
from sailboat_playground.visualization.utils import map_position

STEPS = 6000  # Number of timesteps to simulate; timestep is specified in constants.py, by default 0.1 seconds
ARENA_SIZE_METERS = 200  # Arena size in meters
# (length of one side of the square rendering area, origin is in the center)
# Define initial position and heading angle as constants
INITIAL_POSITION = np.array([50, -90])  # meters, starting position (x, y)
INITIAL_HEADING_ANGLE = 130  # degrees, 0 = East, 90 = North, 180 = West, 270 = South (trigonometric convention)

# Debugging parameters
DEBUG_THRESHOLD_PERCENT = (
    10.0  # Alert if any state variable changes by more than this percentage
)


def wrap(angle):
    while angle < 0:
        angle += 360
    while angle > 360:
        angle -= 360
    return angle


def get_rudder_angle(current_heading, target_heading):
    diff = current_heading - target_heading
    return diff * 0.25


def get_sail_angle(wind_direction, is_tacking):
    if wind_direction > 170 and wind_direction < 190:
        return 2 * (wind_direction - 180)
    elif wind_direction >= 190:
        return 30
    else:
        return -30


def get_target_angle(boat_position, target_position):
    return compute_angle(target_position - boat_position) * 180 / np.pi


def check_state_changes(current_state, previous_state, step, threshold_percent):
    """Check for sudden changes in state variables and print debug info"""
    if previous_state is None:
        return

    alerts = []

    # Check position changes
    pos_change = np.linalg.norm(
        current_state["boat_position"] - previous_state["boat_position"]
    )
    if pos_change > 0:
        pos_change_percent = (
            pos_change / np.linalg.norm(previous_state["boat_position"])
        ) * 100
        if pos_change_percent > threshold_percent:
            alerts.append(f"Position: {pos_change:.3f}m ({pos_change_percent:.1f}%)")

    # Check heading changes
    heading_change = abs(current_state["boat_heading"] - previous_state["boat_heading"])
    if heading_change > 180:
        heading_change = 360 - heading_change
    if heading_change > threshold_percent:
        alerts.append(f"Heading: {heading_change:.1f}° ({heading_change:.1f}%)")

    # Check speed changes
    current_speed = np.linalg.norm(current_state["boat_speed"])
    previous_speed = np.linalg.norm(previous_state["boat_speed"])
    if previous_speed > 0.25:
        speed_change_percent = (
            abs(current_speed - previous_speed) / previous_speed * 100
        )
        if speed_change_percent > threshold_percent:
            alerts.append(
                f"Speed: {current_speed:.3f}→{previous_speed:.3f} m/s ({speed_change_percent:.1f}%)"
            )

    # # Check wind speed changes
    # current_wind = np.linalg.norm(current_state["wind_speed"])
    # previous_wind = np.linalg.norm(previous_state["wind_speed"])
    # if previous_wind > 0:
    #     wind_change_percent = abs(current_wind - previous_wind) / previous_wind * 100
    #     if wind_change_percent > threshold_percent:
    #         alerts.append(
    #             f"Wind: {current_wind:.3f}→{previous_wind:.3f} m/s ({wind_change_percent:.1f}%)"
    #         )

    # Print alerts if any
    if alerts:
        print(f"\n🚨 STEP {step}: SUDDEN CHANGES DETECTED!")
        for alert in alerts:
            print(f"   {alert}")
        print(
            f"   Position: ({current_state['boat_position'][0]:.2f}, {current_state['boat_position'][1]:.2f})"
        )
        print(f"   Heading: {current_state['boat_heading']:.1f}°")
        print(f"   Sail angle: {current_state['sail_angle']:.1f}°")
        print(f"   Rudder angle: {current_state['rudder_angle']:.1f}°")
        print()


# --- Control Algorithm Overview ---
# The main control algorithm in this example is a simple upwind sailing strategy that
# steers the boat toward a target position by alternating ("tacking") between two
# heading angles (typically 40° and 140° relative to East/North, depending on wind).
#
# The algorithm works as follows:
# - At each simulation step, it computes the angle from the boat's current position to the target.
# - If the boat is on one tack (e.g., heading 140°) and the target angle crosses the threshold for the other tack (e.g., drops below 40°), it switches tacking state.
# - The `is_tacking` flag is set to True when a tack is required, and the `target_heading` is updated accordingly.
# - When the boat is close enough to the target (within 20 meters), tacking is disabled and the boat steers directly toward the target.
#
# Tacking state is managed by:
# - Tracking the previous target heading (`prev_target_heading`).
# - Detecting when the target angle crosses the tack threshold, which triggers a tack.
# - Updating `target_heading` to the new tack angle and toggling `is_tacking`.
# - When not tacking, the boat simply steers toward the computed target angle.
#
# This approach ensures the boat zig-zags upwind efficiently, switching tacks as needed to make progress toward the upwind target.

class UpwindSimulation:
    def __init__(self):
        print("**** Sailboat Playground example: sailing_upwind.py")
        print(f"- Debugging threshold: {DEBUG_THRESHOLD_PERCENT}% change detection")
        print("- Starting real-time simulation...")
        
        # Initialize the simulation manager
        self.m = Manager(
            "boats/sample_boat.json",
            "environments/sample_environment.json",
            boat_heading=INITIAL_HEADING_ANGLE,
            boat_position=INITIAL_POSITION,
            debug=False,
        )
        
        # Simulation parameters
        self.target_position = np.array([0, 90])
        self.target_heading = 140
        self.prev_target_heading = 140
        self.half_arena = ARENA_SIZE_METERS / 2
        self.stop = False
        self.steps = 0
        self.previous_state = None  # Track previous state for debugging
        self.is_tacking = False  # Initialize tacking state
        
        # Initialize the viewer for real-time visualization
        buoys = [
            (-75, 90),
            (75, 90),
        ]
        self.v = Viewer(buoy_list=buoys, map_size=ARENA_SIZE_METERS)
        self.v.init()  # Initialize the viewer components
    
    def update_simulation(self, dt):
        
        if self.stop or self.steps >= STEPS:
            pyglet.app.exit()
            return
            
        state = self.m.agent_state
        # Stop simulation if boat crosses any boundary of the sailing area
        x, y = state["position"]
        if x <= -self.half_arena or x >= self.half_arena or y <= -self.half_arena or y >= self.half_arena:
            self.stop = True
            print("Boat crossed boundary of the sailing area")
            pyglet.app.exit()
            return

        # Check if must tack
        target_angle = get_target_angle(state["position"], self.target_position)
        was_tacking = self.is_tacking  # Track previous tacking state

        # Determine if a tack is needed based on target angle crossing thresholds
        tack_due_to_angle = (target_angle >= 140 and self.prev_target_heading == 40) or (
            target_angle <= 40 and self.prev_target_heading == 140
        )
        self.is_tacking = tack_due_to_angle

        # Set target heading according to tacking
        target_distance = np.linalg.norm(state["position"] - self.target_position)
        tack_due_to_proximity = target_distance < 20
        if tack_due_to_proximity:
            self.is_tacking = False
            self.target_heading = target_angle

        # Print tacking transitions and reasons
        if not was_tacking and self.is_tacking:
            print(
                f"Tacking started at step {self.steps}: "
                f"Target angle {target_angle:.1f}°, "
                f"Previous tack {self.prev_target_heading}°. "
                f"Reason: crossed tack threshold."
            )
        elif was_tacking and not self.is_tacking:
            if tack_due_to_proximity:
                print(
                    f"Tacking ended at step {self.steps}: "
                    f"Boat is within {target_distance:.1f}m of target. "
                    f"Reason: close to target."
                )
            else:
                print(
                    f"Tacking ended at step {self.steps}: "
                    f"Target angle {target_angle:.1f}°, "
                    f"Previous tack {self.prev_target_heading}°. "
                    f"Reason: tack threshold not crossed."
                )

        if not self.is_tacking:
            self.prev_target_heading = self.target_heading

        if self.is_tacking:
            if self.prev_target_heading == 40:
                self.target_heading = 140
            else:
                self.target_heading = 40
        rudder_angle = get_rudder_angle(state["heading"], self.target_heading)

        # Set sail angle
        sail_angle = get_sail_angle(state["wind_direction"], self.is_tacking)
        self.m.step([int(sail_angle), int(rudder_angle)])

        # Check stop condition
        if state["position"][1] > 100:
            self.stop = True
            pyglet.app.exit()
            return

        # Get full state for visualization and debugging
        full_state = self.m.state
        
        # Update the viewer with current state
        self.v._draw_wind_vector(full_state["wind_speed"])
        self.v._sailboat.set_position(
            map_position(full_state["boat_position"], ARENA_SIZE_METERS)
        )
        self.v._sailboat.set_rotation(full_state["boat_heading"])
        self.v._sailboat.set_alpha(full_state["sail_angle"])
        self.v._sailboat.set_rudder_angle(full_state["rudder_angle"])
        self.v._sailboat.update(dt)
        
        # Update text displays
        self.v._wind_text.text = "{:.1f}m/s".format(
            np.linalg.norm(full_state["wind_speed"])
        )
        self.v._speed_text.text = "{:.1f}m/s".format(
            np.linalg.norm(full_state["boat_speed"])
        )
        self.v._position_text.text = "Pos: ({:.2f}, {:.2f})".format(
            full_state["boat_position"][0], full_state["boat_position"][1]
        )

        # Check for sudden state changes
        check_state_changes(full_state, self.previous_state, self.steps, DEBUG_THRESHOLD_PERCENT)
        self.previous_state = full_state

        self.steps += 1

    def run(self):
        # Schedule the simulation update function
        pyglet.clock.schedule_interval(self.update_simulation, 0.1)  # Update every 0.1 seconds
        
        # Run the pyglet event loop
        try:
            pyglet.app.run()
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        finally:
            print(" done.")
            print(f"Simulation completed after {self.steps} steps")


if __name__ == "__main__":
    simulation = UpwindSimulation()
    simulation.run()
