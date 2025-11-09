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
        pyglet.gl.glClearColor(0.05, 0.15, 0.3, 1.0)
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
        self._wind_vector_vertices = {}
        self._wind_vector_batch = pyglet.graphics.Batch()
        self._force_vector_batch = pyglet.graphics.Batch()
        self._force_vectors = {}
        self._torque_vertices = None
        self._max_force_magnitude = 1.0
        self._scale_vertices = None
        self._scale_batch = pyglet.graphics.Batch()
        self._scale_label = pyglet.text.Label(
            text="",
            x=40,
            y=120,
            anchor_x="center",
            anchor_y="center",
            batch=self._scale_batch,
            font_size=13,
            color=(220, 230, 255, 255),
        )

        self._legend_total = pyglet.text.Label(
            text="Total Force",
            x=400,
            y=760,
            anchor_x="center",
            anchor_y="center",
            color=(255, 120, 120, 255),
            font_size=14,
            batch=self._main_batch,
        )
        self._legend_sail = pyglet.text.Label(
            text="Sail Force",
            x=400,
            y=740,
            anchor_x="center",
            anchor_y="center",
            color=(110, 205, 110, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._legend_hull = pyglet.text.Label(
            text="Hull Drag",
            x=400,
            y=720,
            anchor_x="center",
            anchor_y="center",
            color=(120, 190, 255, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._legend_torque = pyglet.text.Label(
            text="Torque (CW+/CCW-)",
            x=400,
            y=700,
            anchor_x="center",
            anchor_y="center",
            color=(255, 165, 0, 255),
            font_size=12,
            batch=self._main_batch,
        )
        self._wind_text = pyglet.text.Label(
            text="N/A m/s",
            x=WIND_X,
            y=1,
            anchor_x="center",
            anchor_y="bottom",
            batch=self._main_batch,
            font_size=15,
        )

        SPEED_X = 120
        self._speed_icon = pyglet.sprite.Sprite(
            img=speed_image, x=SPEED_X, y=40, batch=self._main_batch
        )
        self._speed_text = pyglet.text.Label(
            text="N/A m/s",
            x=SPEED_X + 30,
            y=50,
            anchor_x="left",
            anchor_y="baseline",
            multiline=True,
            width=200,
            batch=self._main_batch,
            font_size=14,
        )

        POSITION_X = 700
        self._position_text = pyglet.text.Label(
            text="(nan, nan)",
            x=POSITION_X,
            y=10,
            anchor_x="center",
            anchor_y="baseline",
            batch=self._main_batch,
            font_size=15,
        )

        STATUS_X = 40
        self._status_text = pyglet.text.Label(
            text="Step 0 | t=0.0 s",
            x=STATUS_X,
            y=680,
            anchor_x="left",
            anchor_y="center",
            batch=self._main_batch,
            font_size=12,
            color=(240, 245, 255, 255),
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

    def _add_wind_arrow(
        self,
        origin_x: float,
        origin_y: float,
        ux: float,
        uy: float,
        length: float,
        head_size: float,
        clip_positive: bool,
        clip_negative: bool,
        clip_indicator_size: float,
    ):
        arrow_color = (180, 210, 255, 255)
        clip_color = (255, 120, 120, 255)

        half_len = length * 0.5
        start_x = origin_x - half_len * ux
        start_y = origin_y - half_len * uy
        end_x = origin_x + half_len * ux
        end_y = origin_y + half_len * uy

        shaft_vertices = [start_x, start_y, end_x, end_y]
        shaft_colors = list(arrow_color) * 2

        arrow_angle = math.atan2(uy, ux)
        head_angle_offset = math.pi / 5
        left_angle = arrow_angle + math.pi - head_angle_offset
        right_angle = arrow_angle + math.pi + head_angle_offset

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
        head_colors = list(arrow_color) * 4

        all_vertices = shaft_vertices + head_vertices
        all_colors = shaft_colors + head_colors

        clip_angle_offset = math.pi / 4

        def extend_clip_indicator(point_x, point_y, direction_angle):
            clip_vertices = [
                point_x,
                point_y,
                point_x
                + clip_indicator_size
                * math.cos(direction_angle + math.pi - clip_angle_offset),
                point_y
                + clip_indicator_size
                * math.sin(direction_angle + math.pi - clip_angle_offset),
                point_x,
                point_y,
                point_x
                + clip_indicator_size
                * math.cos(direction_angle + math.pi + clip_angle_offset),
                point_y
                + clip_indicator_size
                * math.sin(direction_angle + math.pi + clip_angle_offset),
            ]
            clip_colors = list(clip_color) * 4
            all_vertices.extend(clip_vertices)
            all_colors.extend(clip_colors)

        if clip_positive:
            extend_clip_indicator(end_x, end_y, arrow_angle)
        if clip_negative:
            extend_clip_indicator(start_x, start_y, arrow_angle + math.pi)

        return self._wind_vector_batch.add(
            len(all_vertices) // 2,
            pyglet.gl.GL_LINES,
            None,
            ("v2f", all_vertices),
            ("c4B", all_colors),
        )

    def _draw_wind_vector(self, wind_speed):
        """
        Draw wind vector showing direction and speed.

        Args:
            wind_speed (np.ndarray): Wind velocity vector [x, y] in m/s
        """
        # Clear previous wind vectors
        for handle in self._wind_vector_vertices.values():
            if handle is not None:
                handle.delete()
        self._wind_vector_vertices.clear()

        # Visualize the true wind flow direction (arrow points toward where the wind travels)
        wind_vector = np.array(wind_speed, dtype=float)

        # Calculate wind speed magnitude and direction
        wind_magnitude = np.linalg.norm(wind_vector)
        # Pre-compute grid of origins (4x4 across window, centered in sailing area)
        grid_cols = grid_rows = 4
        width = self._window.width
        height = self._window.height
        x_positions = [
            width * (i + 1) / (grid_cols + 1) for i in range(grid_cols)
        ]
        y_positions = [
            height * (j + 1) / (grid_rows + 1) for j in range(grid_rows)
        ]
        origins = [(x, y) for x in x_positions for y in y_positions]

        if wind_magnitude < 0.01:
            # Represent calm conditions with small dots at each grid point
            circle_radius = 3
            for origin_x, origin_y in origins:
                vertices = []
                colors = []
                for i in range(8):
                    angle = i * 2 * np.pi / 8
                    x = origin_x + circle_radius * np.cos(angle)
                    y = origin_y + circle_radius * np.sin(angle)
                    vertices.extend([x, y])
                    colors.extend([180, 210, 255, 255])
                handle = self._wind_vector_batch.add(
                    len(vertices) // 2,
                    pyglet.gl.GL_POLYGON,
                    None,
                    ("v2f", vertices),
                    ("c4B", colors),
                )
                self._wind_vector_vertices[(origin_x, origin_y)] = handle
            return

        # Scale arrows based on magnitude (normalized across grid)
        scale_factor = 40.0
        desired_length = wind_magnitude * scale_factor

        wind_angle = compute_angle(wind_vector)
        ux = np.cos(wind_angle)
        uy = np.sin(wind_angle)

        margin = 40.0
        desired_half = desired_length * 0.5
        arrow_limits = []
        min_half_limit = desired_half

        for origin_x, origin_y in origins:
            pos_limit = float("inf")
            neg_limit = float("inf")

            if abs(ux) > 1e-6:
                if ux > 0:
                    pos_limit = min(pos_limit, (width - margin - origin_x) / ux)
                    neg_limit = min(neg_limit, (origin_x - margin) / ux)
                else:
                    pos_limit = min(pos_limit, (origin_x - margin) / (-ux))
                    neg_limit = min(neg_limit, (width - margin - origin_x) / (-ux))

            if abs(uy) > 1e-6:
                if uy > 0:
                    pos_limit = min(pos_limit, (height - margin - origin_y) / uy)
                    neg_limit = min(neg_limit, (origin_y - margin) / uy)
                else:
                    pos_limit = min(pos_limit, (origin_y - margin) / (-uy))
                    neg_limit = min(
                        neg_limit, (height - margin - origin_y) / (-uy)
                    )

            pos_limit = max(pos_limit, 0.0)
            neg_limit = max(neg_limit, 0.0)

            arrow_limits.append((origin_x, origin_y, pos_limit, neg_limit))
            min_half_limit = min(min_half_limit, pos_limit, neg_limit)

        half_length = min(desired_half, min_half_limit)
        vector_length = half_length * 2.0
        head_size = max(8, vector_length * 0.15)
        clip_indicator_size = 6

        for origin_x, origin_y, pos_limit, neg_limit in arrow_limits:
            clip_positive = (
                pos_limit < float("inf") and half_length >= pos_limit - 1e-6
            )
            clip_negative = (
                neg_limit < float("inf") and half_length >= neg_limit - 1e-6
            )

            handle = self._add_wind_arrow(
                origin_x,
                origin_y,
                ux,
                uy,
                vector_length,
                head_size,
                clip_positive,
                clip_negative,
                clip_indicator_size,
            )
            self._wind_vector_vertices[(origin_x, origin_y)] = handle

    def _draw_scale_bar(self):
        if self._scale_vertices is not None:
            self._scale_vertices.delete()
            self._scale_vertices = None

        pixels_per_meter = self._window.height / float(self._map_size)
        if pixels_per_meter <= 0:
            return

        desired_pixel_target = self._window.height * 0.35
        scale_candidates = [5, 10, 20, 25, 50, 75, 100, 150, 200, 400]
        scale_meters = scale_candidates[0]
        for candidate in scale_candidates:
            if candidate * pixels_per_meter <= desired_pixel_target:
                scale_meters = candidate
            else:
                break

        bar_height = scale_meters * pixels_per_meter
        max_bar_height = self._window.height - 160
        if bar_height > max_bar_height and max_bar_height > 0:
            bar_height = max_bar_height
            scale_meters = bar_height / pixels_per_meter
        bottom_y = 100
        scale_value = max(1, int(round(scale_meters)))
        bar_height = scale_value * pixels_per_meter
        top_y = bottom_y + bar_height
        x_pos = 50
        tick_half = 8

        vertices = [
            x_pos,
            bottom_y,
            x_pos,
            top_y,
            x_pos - tick_half,
            bottom_y,
            x_pos + tick_half,
            bottom_y,
            x_pos - tick_half,
            top_y,
            x_pos + tick_half,
            top_y,
        ]
        colors = [200, 220, 255, 255] * (len(vertices) // 2)

        self._scale_vertices = self._scale_batch.add(
            len(vertices) // 2,
            pyglet.gl.GL_LINES,
            None,
            ("v2f", vertices),
            ("c4B", colors),
        )
        self._scale_label.text = f"{scale_value} m"
        self._scale_label.y = top_y + 16
    def on_draw(self):
        self._window.clear()
        self._main_batch.draw()
        self._wind_vector_batch.draw()
        self._scale_batch.draw()
        self._force_vector_batch.draw()

    def update(self, dt, state_list=None, step_size=1):
        self._draw_scale_bar()
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

    def set_step_indicator(
        self,
        step: int,
        paused: bool,
        single_step: bool,
        sim_time_s: float,
        real_time_factor: float | None,
    ) -> None:
        status = f"Step {step} | t={sim_time_s:.1f} s"
        if real_time_factor is not None and real_time_factor > 0:
            if real_time_factor >= 1.0:
                status += f" | {real_time_factor:.1f}x"
            else:
                status += f" | {1.0 / real_time_factor:.1f}/"
        if paused:
            status += " (paused"
            if single_step:
                status += ", single-step"
            status += ")"
        self._status_text.text = status

    def draw_force_vectors(self, boat_position, forces):
        if forces is None:
            return

        origin = map_position(np.array(boat_position), self._map_size)
        colors = {
            "total": (255, 120, 120, 255),
            "sail": (110, 205, 110, 255),
            "hull": (120, 190, 255, 255),
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
