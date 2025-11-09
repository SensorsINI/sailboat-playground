## Hull Torque and Sail Trim Notes

Work-in-progress summary so we can pick up the physics tuning on another machine.

### Recent Fixes
- Normalise apparent-wind direction and keep the mainsail on the leeward side inside `Manager.step()`. This prevents the “sail on wrong tack” reversal when the apparent flow crosses the bow.
- Increased `MAX_SAIL_DEG` to `70°` in the manual keyboard demo to reflect the DragonForce 65 sheet limits. The wrapper now just passes the magnitude; the physics engine chooses the sign.
- Added explicit keel geometry (`keel_span`, `keel_chord`, `keel_area`, `keel_distance_from_com`, `keel_foil`) to `boats/argo_boat.json` and extended `Manager.step()` to compute keel lift/drag plus a forward-offset yaw torque.
- Introduced state logging (`state_log_path` argument on `Manager`) and force/velocity sanity guards so runaway cases can be captured as JSONL traces.
- Split aerodynamic/hydrodynamic scale factors in `Manager.compute_force()`: air uses `×10` for numerical stability, water now uses `×1` so keel/rudder forces reflect physical magnitudes.

### Current Findings (Oct 2025)
- Adding the keel produced the expected yaw-damping directionally, but hydrodynamic lift now overwhelms the 2 kg hull. In headless tests (wind 220°, sail −22°, rudder 0°) speed still explodes to ~94 m/s within 2 s even with the timestep reduced to 0.002 s.
- Keel force magnitudes climb into the hundreds of newtons (see `logs/headless_manual.jsonl` / `logs/headless_manual_dt002.jsonl`), so the instability is physical rather than integrator-related.
- Next tuning tasks:
  - Reduce effective keel lift (smaller `keel_area`, shorter `keel_span`, or use a milder foil table) and/or introduce additional viscous damping.
  - Revisit the empirical `SLIP_FORCE_COEFF` in `Manager.step()` once keel-driven lateral resistance is balanced.
  - Consider upping `moment_of_inertia` in `boats/argo_boat.json` if yaw accelerations keep slamming into the ±720 deg/s² clamp.

### Parameters Worth Tweaking
- `boats/argo_boat.json`
  - `keel_area`, `keel_span`, `keel_chord`, `keel_distance_from_com`: trim these first to moderate keel lift and yaw torque.
  - `moment_of_inertia`: increase to soften angular response if rudder/keel torques remain too snappy.
- `sailboat_playground/engine/Manager.py`
  - `SLIP_FORCE_COEFF` (search in `Manager.step()`): currently `0.25`, still acting in parallel with the keel force.
  - `force_scale` logic inside `compute_force()`: set both branches to `1` temporarily to isolate the effect of the air-side scale-up.
  - `MAX_RELATIVE_SPEED` inside `_sanitize_relative_velocity()`: reduce if you need a hard ceiling on apparent flow when debugging.
- `sailboat_playground/simulator.json`
  - `time_delta`: default `0.02` s. We confirmed that shrinking it 10× does not cure the runaway, but useful when experimenting with stiffer damping terms.

### Suggested Next Steps
1. Sweep `keel_area`/`keel_distance_from_com` and re-run the headless manual scenario (`python3 -u - <<'PY' ... PY`) while logging to JSONL to correlate force magnitudes with slip velocity.
2. Rebalance or temporarily zero `SLIP_FORCE_COEFF` once keel forces are reasonable, then re-evaluate lateral damping.
3. If keel lift still spikes, experiment with a flatter foil curve (e.g. scale `cl`/`cd` columns in `foils/naca0015.csv` for a “keel-lite” variant).
4. After hydrodynamic loads are stable, revisit yaw damping: consider explicit hull yaw drag proportional to angular speed rather than relying solely on the keel lever arm.
5. Keep running the beam-reach demo (`timeout 10 python3 -u manual_keyboard_control.py`) after each change and stash the resulting `logs/*.jsonl` for comparison.

Keep this file updated as we iterate on the physics. Once the keel model is implemented we can promote the notes into the main project documentation.

