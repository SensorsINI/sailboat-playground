import pyglet
import numpy as np
from sailboat_playground.engine.utils import compute_angle
from sailboat_playground.visualization.Sailboat import Sailboat
from sailboat_playground.visualization.utils import map_position
from sailboat_playground.visualization.resources.resources import (
    speed_image,
    buoy_image,
)
import math


class Viewer:

    def __init__(self, map_size: int = 800, buoy_list: list = None):
        self._map_size = map_size
        self._buoy_list = buoy_list if buoy_list is not None else []
        self._window = pyglet.window.Window(800, 800)
        self._window.event(self.on_draw)
        pyglet.gl.glClearColor(0.1, 0.4, 0.8, 0.4)
        self._step = 0
        self._main_batch = pyglet.graphics.Batch()

        self._end_label = pyglet.text.Label(
            text="End of simulation",
            x=400,
            y=-400,
            anchor_x="center",
            batch=self._main_batch,
            font_size=48,
        )

        # Position wind vector in the middle of the display
        WIND_X = 400  # Center horizontally
        WIND_Y = 400  # Center vertically
        self._wind_origin = (WIND_X, WIND_Y)
        self._wind_vector_vertices = None
        self._wind_vector_batch = pyglet.graphics.Batch()
        self._force_vector_batch = pyglet.graphics.Batch()
        self._force_vectors = {}
        self._torque_vertices = None
        self._max_force_magnitude = 1.0

        self._legend_total = pyglet.text.Label(
            text="Total Force",
            x=400,
            y=40,
            anchor_x="center",
            anchor_y="center",
            color=(255, 0, 0, 255),
            font_size=14,
            batch=self._main_batch,
        )
        self._legend_sail = pyglet.text.Label(
            text="Sail Force",
            x=400,
            y=20,
            anchor_x="center",
            anchor_y="center",
            color=(0, 255, 0, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._legend_hull = pyglet.text.Label(
            text="Hull Drag",
            x=400,
            y=0,
            anchor_x="center",
            anchor_y="center",
            color=(0, 128, 255, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._legend_torque = pyglet.text.Label(
            text="Torque (CW+/CCW-)",
            x=400,
            y=-20,
            anchor_x="center",
            anchor_y="center",
            color=(255, 165, 0, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._wind_text = pyglet.text.Label(
            text="N/A m/s",
            x=WIND_X,
            y=10,
            anchor_x="center",
            anchor_y="center",
            batch=self._main_batch,
            font_size=15,
        )

        SPEED_X = 140
        self._speed_icon = pyglet.sprite.Sprite(
            img=speed_image, x=SPEED_X, y=40, batch=self._main_batch
        )
        self._speed_text = pyglet.text.Label(
            text="N/A m/s",
            x=SPEED_X,
            y=10,
            anchor_x="center",
            anchor_y="center",
            batch=self._main_batch,
            font_size=15,
        )

        POSITION_X = 700
        self._position_text = pyglet.text.Label(
            text="(nan, nan)",
            x=POSITION_X,
            y=10,
            anchor_x="center",
            anchor_y="center",
            batch=self._main_batch,
            font_size=15,
        )

        self._sailboat = None
        self._objects = []

    def init(self):
        self._sailboat = Sailboat(
            x=400, y=400, batch=self._main_batch, map_size=self._map_size
        )
        self._objects = [self._sailboat]

        for obj in self._objects:
            for handler in obj.event_handlers:
                self._window.push_handlers(handler)

        for x, y in self._buoy_list:
            pos = map_position(np.array([x, y]), self._map_size)
            x_map = pos[0]
            y_map = pos[1]
            self._objects.append(
                pyglet.sprite.Sprite(
                    img=buoy_image, x=x_map, y=y_map, batch=self._main_batch
                )
            )

    def _draw_wind_vector(self, wind_speed):
        """
        Draw wind vector showing direction and speed.

        Args:
            wind_speed (np.ndarray): Wind velocity vector [x, y] in m/s
        """
        # Clear previous wind vector
        if self._wind_vector_vertices is not None:
            self._wind_vector_vertices.delete()

        # Calculate wind speed magnitude and direction
        wind_magnitude = np.linalg.norm(wind_speed)
        if wind_magnitude < 0.01:  # Very light wind, draw a small circle
            # Draw a small circle for very light wind
            circle_radius = 2
            vertices = []
            colors = []
            for i in range(8):  # 8-sided circle
                angle = i * 2 * np.pi / 8
                x = self._wind_origin[0] + circle_radius * np.cos(angle)
                y = self._wind_origin[1] + circle_radius * np.sin(angle)
                vertices.extend([x, y])
                colors.extend([255, 255, 0, 255])  # Yellow for light wind
            self._wind_vector_vertices = self._wind_vector_batch.add(
                len(vertices) // 2,
                pyglet.gl.GL_POLYGON,
                None,
                ("v2f", vertices),
                ("c4B", colors),
            )
        else:
            # Scale: 1 m/s = 5% of screen height (40 pixels for 800px screen)
            scale_factor = 40.0  # pixels per m/s
            vector_length = wind_magnitude * scale_factor

            # Limit vector length to prevent it from extending beyond screen bounds
            # Leave some margin from screen edges (100px from all edges)
            max_length_x = min(
                self._wind_origin[0] - 100, 800 - self._wind_origin[0] - 100
            )
            max_length_y = min(
                self._wind_origin[1] - 100, 800 - self._wind_origin[1] - 100
            )
            max_length = min(max_length_x, max_length_y)

            # With centered origin, we have plenty of room (300px radius)
            max_length = max(max_length, 300)  # At least 300 pixels from center

            # Check if vector needs to be clipped
            is_clipped = vector_length > max_length
            if is_clipped:
                vector_length = max_length

            # Calculate wind direction (angle from wind velocity vector)
            wind_angle = compute_angle(wind_speed)

            # Calculate vector endpoint
            end_x = self._wind_origin[0] + vector_length * np.cos(wind_angle)
            end_y = self._wind_origin[1] + vector_length * np.sin(wind_angle)

            # Draw arrow shaft
            shaft_vertices = [self._wind_origin[0], self._wind_origin[1], end_x, end_y]
            shaft_colors = [255, 255, 0, 255] * 2  # Yellow shaft

            # Draw arrow head
            head_size = max(12, vector_length * 0.3)  # Larger arrow head size
            head_angle1 = wind_angle + np.pi - np.pi / 3  # 45 degrees to the left, pointing toward origin
            head_angle2 = wind_angle + np.pi + np.pi / 4  # 45 degrees to the right, pointing toward origin

            head_x1 = end_x + head_size * np.cos(head_angle1)
            head_y1 = end_y + head_size * np.sin(head_angle1)
            head_x2 = end_x + head_size * np.cos(head_angle2)
            head_y2 = end_y + head_size * np.sin(head_angle2)

            head_vertices = [
                end_x,
                end_y,
                head_x1,
                head_y1,
                end_x,
                end_y,
                head_x2,
                head_y2,
            ]
            head_colors = [255, 255, 0, 255] * 4  # Yellow head

            # Create vertices for both shaft and head
            all_vertices = shaft_vertices + head_vertices
            all_colors = shaft_colors + head_colors

            # Add clipping indicator if vector was clipped
            if is_clipped:
                # Add a ">" symbol at the end to indicate clipping
                clip_indicator_size = 6
                clip_angle1 = wind_angle + np.pi - np.pi / 4  # 45 degrees
                clip_angle2 = wind_angle + np.pi + np.pi / 4  # 45 degrees

                clip_x1 = end_x + clip_indicator_size * np.cos(clip_angle1)
                clip_y1 = end_y + clip_indicator_size * np.sin(clip_angle1)
                clip_x2 = end_x + clip_indicator_size * np.cos(clip_angle2)
                clip_y2 = end_y + clip_indicator_size * np.sin(clip_angle2)

                clip_vertices = [
                    end_x,
                    end_y,
                    clip_x1,
                    clip_y1,
                    end_x,
                    end_y,
                    clip_x2,
                    clip_y2,
                ]
                clip_colors = [255, 0, 0, 255] * 4  # Red for clipping indicator

                all_vertices.extend(clip_vertices)
                all_colors.extend(clip_colors)

            self._wind_vector_vertices = self._wind_vector_batch.add(
                len(all_vertices) // 2,
                pyglet.gl.GL_LINES,
                None,
                ("v2f", all_vertices),
                ("c4B", all_colors),
            )

    def on_draw(self):
        self._window.clear()
        self._main_batch.draw()
        self._wind_vector_batch.draw()
        self._force_vector_batch.draw()

    def update(self, dt, state_list=None, step_size=1):
        if self._step >= len(state_list):
            self._end_label.y = 400
        else:
            state = state_list[self._step]
            # Draw wind vector showing direction and speed
            self._draw_wind_vector(state["wind_speed"])
            self._sailboat.set_position(
                map_position(state["boat_position"], self._map_size)
            )
            self._sailboat.set_rotation(state["boat_heading"])
            self._sailboat.set_alpha(state["sail_angle"])
            self._sailboat.set_rudder_angle(state["rudder_angle"])
            self._sailboat.update(dt)
            self._wind_text.text = "{:.1f}m/s".format(
                np.linalg.norm(state["wind_speed"])
            )
            self._speed_text.text = "{:.1f}m/s".format(
                np.linalg.norm(state["boat_speed"])
            )
            self._position_text.text = "Pos: ({:.2f}, {:.2f})".format(
                state["boat_position"][0], state["boat_position"][1]
            )
            self._step += step_size

    def run(self, state_list, simulation_speed=100):

        # Init
        self.init()

        # Calculate optimal display settings
        # Target: 60 FPS for smooth display, but skip states to achieve desired speedup
        target_fps = 60
        total_states = len(state_list)
        total_simulation_time = total_states / simulation_speed  # seconds

        # Calculate how many states to skip per frame
        step_size = max(1, int(simulation_speed / target_fps))

        # Use 60 FPS for smooth display
        update_interval = 1.0 / target_fps

        print(f"Visualization settings:")
        print(f"  Total states: {total_states}")
        print(f"  Simulation speed: {simulation_speed} states/sec")
        print(f"  Display FPS: {target_fps}")
        print(f"  Step size: {step_size} states per frame")
        print(f"  Total playback time: {total_simulation_time:.1f} seconds")

        # Set update interval with step size
        pyglet.clock.schedule_interval(
            self.update, update_interval, state_list=state_list, step_size=step_size
        )

        # Run
        pyglet.app.run()

    def draw_force_vectors(self, boat_position, forces):
        if forces is None:
            return

        origin = map_position(np.array(boat_position), self._map_size)
        colors = {
            "total": (255, 0, 0, 255),
            "sail": (0, 255, 0, 255),
            "hull": (0, 128, 255, 255),
        }
        scale = 20.0

        for key, vec in forces.items():
            vec_key = f"force_{key}"
            if self._force_vectors.get(vec_key) is not None:
                self._force_vectors[vec_key].delete()
                self._force_vectors[vec_key] = None

            if vec is None:
                continue

            magnitude = np.linalg.norm(vec)
            if magnitude < 1e-6:
                continue

            self._max_force_magnitude = max(
                self._max_force_magnitude * 0.98, magnitude, 1.0
            )
            scale = 120.0 / self._max_force_magnitude
            vector_length = magnitude * scale
            if vector_length < 18.0:
                scale = max(scale, 18.0 / max(magnitude, 1e-6))

            end_x = origin[0] + vec[0] * scale
            end_y = origin[1] + vec[1] * scale

            shaft_vertices = [origin[0], origin[1], end_x, end_y]
            shaft_colors = list(colors.get(key, (255, 255, 255, 255))) * 2

            head_size = max(10.0, magnitude * scale * 0.3)
            angle = math.atan2(vec[1], vec[0])
            left_angle = angle + math.pi - math.pi / 6
            right_angle = angle + math.pi + math.pi / 6
            head_vertices = [
                end_x,
                end_y,
                end_x + head_size * math.cos(left_angle),
                end_y + head_size * math.sin(left_angle),
                end_x,
                end_y,
                end_x + head_size * math.cos(right_angle),
                end_y + head_size * math.sin(right_angle),
            ]
            head_colors = list(colors.get(key, (255, 255, 255, 255))) * 4

            vertices = shaft_vertices + head_vertices
            color_data = shaft_colors + head_colors

            self._force_vectors[vec_key] = self._force_vector_batch.add(
                len(vertices) // 2,
                pyglet.gl.GL_LINES,
                None,
                ("v2f", vertices),
                ("c4B", color_data),
            )

    def draw_torque_arc(self, boat_position, angular_accel):
        if self._torque_vertices is not None:
            self._torque_vertices.delete()
            self._torque_vertices = None

        if angular_accel is None or abs(angular_accel) < 1e-4:
            return

        origin = map_position(np.array(boat_position), self._map_size)
        radius = 45.0
        segments = 16
        direction = -1 if angular_accel > 0 else 1  # positive accel => clockwise torque
        sweep_angle = max(0.3, min(abs(angular_accel) * 2.0, math.pi * 1.5))

        start_angle = math.pi / 2  # start in front of boat (pointing upward on screen)
        angles = [
            start_angle + direction * sweep_angle * (i / segments)
            for i in range(segments + 1)
        ]

        vertices = []
        colors = []
        color = (255, 165, 0, 255)
        for i in range(segments):
            a0 = angles[i]
            a1 = angles[i + 1]
            x0 = origin[0] + radius * math.cos(a0)
            y0 = origin[1] + radius * math.sin(a0)
            x1 = origin[0] + radius * math.cos(a1)
            y1 = origin[1] + radius * math.sin(a1)
            vertices.extend([x0, y0, x1, y1])
            colors.extend(list(color) * 2)

        arrow_base_angle = angles[-1]
        arrow_length = 12.0
        arrow_width = 6.0
        tip_x = origin[0] + radius * math.cos(arrow_base_angle)
        tip_y = origin[1] + radius * math.sin(arrow_base_angle)
        normal_angle = arrow_base_angle + direction * math.pi / 2
        base_x = tip_x + arrow_length * math.cos(arrow_base_angle)
        base_y = tip_y + arrow_length * math.sin(arrow_base_angle)
        left_x = base_x + arrow_width * math.cos(normal_angle)
        left_y = base_y + arrow_width * math.sin(normal_angle)
        right_x = base_x - arrow_width * math.cos(normal_angle)
        right_y = base_y - arrow_width * math.sin(normal_angle)

        vertices.extend([tip_x, tip_y, left_x, left_y, tip_x, tip_y, right_x, right_y])
        colors.extend(list(color) * 4)

        self._torque_vertices = self._force_vector_batch.add(
            len(vertices) // 2,
            pyglet.gl.GL_LINES,
            None,
            ("v2f", vertices),
            ("c4B", colors),
        )
