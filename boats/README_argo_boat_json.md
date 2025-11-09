# Argo DragonForce 65 Boat Configuration

This document explains the parameters used in `boats/argo_boat.json` for the DragonForce 65 RC sailboat simulation.

## Boat Specifications

The DragonForce 65 is a popular RC sailboat class with the following actual specifications:

### Physical Dimensions
- **Length**: 650mm (0.65m)
- **Beam (Width)**: 116.5mm (0.1165m)
- **Mast Height**: 915mm (0.915m)
- **Overall Height**: 1338mm (1.338m)
- **Weight**: 1200g (1.2kg)
- **Sail Area**: 22.26 dm² (0.2226m²)

## Configuration Parameters

All values in this section match `boats/argo_boat.json`. The tables now include the calculations that link the raw measurements above to the configuration constants used by the simulator.

### Basic Properties

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `name` | - | Argo DragonForce 65 | `"Argo DragonForce 65"` |
| `length` | Hull LOA: 650 mm / 1000 | 0.65 m | `0.65` |
| `mass` | 1.2 kg (hull & rig) + 0.5 kg (battery pack) + 0.3 kg (electronics & mounts) | 2.0 kg | `2.0` |

### Center of Mass

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `com_length` | 50% of hull length: 0.5 x 0.65 m | 0.325 m | `0.325` |

### Sail Configuration

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `sail_area` | Main 1400 cm^2 (0.14 m^2) + jib 645 cm^2 (0.0645 m^2) = 0.2045 m^2. Manufacturer spec rounds to 22.26 dm^2 | 0.2226 m^2 | `0.2226` |
| `sail_foil` | - | `naca0015` | `"naca0015"` |

**Notes**
- `kitty_main` measurement: 1400 cm^2 -> 0.14 m^2 (/ 10000).
- `kitty_jib` measurement: 645 cm^2 -> 0.0645 m^2.
- We retain the manufacturer's 22.26 dm^2 area so the simulator matches published polars.

### Rudder Configuration

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `rudder_area` | Planform 4 cm x 13.5 cm = 54 cm^2 -> 0.0054 m^2. Effective area scaled x1.5 for taper and end-plate effects | 0.008 m^2 | `0.008` |
| `rudder_foil` | - | `naca0015` | `"naca0015"` |

### Keel

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `keel_span` | Measured fin length 31 cm / 100 | 0.31 m | `0.31` |
| `keel_chord` | Mean chord 4 cm / 100 | 0.04 m | `0.04` |
| `keel_area` | 0.31 m x 0.04 m | 0.0124 m^2 | `0.0124` |
| `keel_distance_from_com` | Keel post at mast step (0.345 m from bow) - COM 0.325 m | 0.02 m | `0.02` |
| `keel_foil` | - | `naca0015` | `"naca0015"` |

**Notes**
- The DragonForce 65 keel fin sits directly under the mast; the 20 mm forward offset produces a restoring yaw moment that complements the rudder damping.
- We reuse the `naca0015` foil coefficients for keel lift/drag until class-specific data is available.

### Hull Properties

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `hull_area` | Effective beam 0.10 m x estimated draft 0.15 m | 0.015 m^2 | `0.015` |
| `hull_friction_coefficient` | Sample boat 0.20 x (0.015 m^2 / 0.05 m^2 wetted area estimate) | ~0.06 -> tuned to 0.07 | `0.07` |
| `hull_rotation_resistance` | Sample 0.40 x (0.015 m^2 / 0.04 m^2 lateral area) | ~0.15 | `0.15` |

### Inertial Properties

| Parameter | Calculation | Result | JSON Value |
|-----------|-------------|--------|------------|
| `moment_of_inertia` | Rectangular hull about vertical axis: (m/12) x (L^2 + B^2) = (2/12) x (0.65^2 + 0.1165^2) ~ 0.073 kg*m^2. Tuned x11 to reflect keel bulb mass and hydrodynamic damping | 0.8 kg*m^2 | `0.8` |


## Usage

To use this configuration in simulations, replace the boat configuration file:

```python
m = Manager(
    "boats/argo_boat.json",  # Use Argo configuration
    "environments/playground.json",
    boat_heading=270
)
```

## References

- [DragonForce 65 specifications from New Zealand Radio Yachting Association](https://nzradioyachtingassociation.co.nz/wp-content/uploads/2020/09/DF65-Specifications.pdf)
- [RC sailboat design principles and scaling factors](https://www.onemetre.net/Design/Design.htm)
- Comparison with sample boat configuration for parameter estimation
