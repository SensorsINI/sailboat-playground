README – Environment Configs
============================

This directory holds JSON files that parameterize the Sailboat Playground environment model. Each file follows the schema consumed by `sailboat_playground.engine.Environment`, and any unused key can be omitted. All angles use the trigonometric convention (0° = East, 90° = North).

## Core Parameters (`playground.json`)

- `name`  
  Human-readable identifier only; not used programmatically.

- `wind_min_speed`, `wind_max_speed` *(m/s)*  
  Bounds for the nominal true-wind magnitude. The environment randomly drifts within this range each timestep, limited by `wind_max_delta_percent`.

  **Tip:** To match real-world anemometer readings (usually in knots), here are some conversions:

    - 5 knots ≈ 2.57 m/s  
    - 10 knots ≈ 5.14 m/s  
    - 15 knots ≈ 7.72 m/s  

  For example, to simulate a steady 10-knot breeze, set both `wind_min_speed` and `wind_max_speed` to `5.14`.

- `wind_max_delta_percent` *(% per step)*  
  Maximum fractional change allowed between consecutive wind-speed samples while outside a gust event.

- `wind_direction` *(degrees)*  
  Direction the true wind blows **from**. Converted to a vector when computing apparent wind.

- `wind_gust_probability` *(0–1)*  
  Probability during a non-gust step that a gust starts this timestep.

- `wind_gust_min_duration`, `wind_gust_max_duration` *(seconds)*  
  Duration range for a gust episode once triggered.

- `wind_gust_min_speed`, `wind_gust_max_speed` *(m/s)*  
  Speed bounds used while a gust is active.

- `wind_gust_max_delta_percent` *(% per step)*  
  Maximum fractional wind-speed change while a gust is active.

- `current_speed` *(m/s)*  
  Magnitude of the steady water current vector. Set to `0` for still water.

- `current_direction` *(degrees)*  
  Direction the current flows **to**. Combined with `current_speed` to produce the water-velocity vector supplied to the physics engine.

## Usage Notes

- JSON does not support comments; retain documentation in this README instead.
- Any custom environment file must include at least the wind and current keys expected by `Environment`.
- Keep speeds non-negative and probabilities within `[0, 1]` to avoid runtime validation errors.

