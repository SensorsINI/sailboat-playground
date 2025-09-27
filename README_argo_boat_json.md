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

### Basic Properties

| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `name` | "Argo DragonForce 65" | - | Descriptive name |
| `length` | 0.65 | m | Actual hull length |
| `mass` | 1.2 | kg | Actual boat weight |

### Center of Mass
| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `com_length` | 0.325 | m | Estimated at 50% of hull length (typical for RC boats) |

### Sail Configuration
| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `sail_area` | 0.2226 | m² | Actual sail area (22.26 dm²) |
| `sail_foil` | "naca0015" | - | Standard foil profile (same as sample boat) |

### Rudder Configuration
| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `rudder_area` | 0.008 | m² | Estimated ~3.6% of sail area for good control |
| `rudder_foil` | "naca0015" | - | Standard foil profile (same as sample boat) |

### Hull Properties
| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `hull_area` | 0.015 | m² | Estimated frontal area based on length and beam |
| `hull_friction_coefficient` | 0.15 | - | Lower than sample boat (0.2) due to smaller size and smoother hull |
| `hull_rotation_resistance` | 0.3 | - | Reduced from sample boat (0.4) for lighter, more responsive boat |

### Inertial Properties
| Parameter | Value | Unit | Source/Calculation |
|-----------|-------|------|-------------------|
| `moment_of_inertia` | 0.8 | kg⋅m² | Much lower than sample boat (100) due to smaller mass and size |

## Comparison with Sample Boat

| Parameter | Sample Boat | Argo DF65 | Ratio | Notes |
|-----------|-------------|-----------|-------|-------|
| Length | 1.1m | 0.65m | 0.59 | ~59% of sample boat |
| Mass | 30kg | 1.2kg | 0.04 | ~4% of sample boat |
| Sail Area | 1.0m² | 0.2226m² | 0.22 | ~22% of sample boat |
| Rudder Area | 0.02m² | 0.008m² | 0.4 | ~40% of sample boat |
| Hull Area | 0.03m² | 0.015m² | 0.5 | ~50% of sample boat |
| Moment of Inertia | 100 | 0.8 | 0.008 | ~0.8% of sample boat |

## Expected Behavior

The Argo DragonForce 65 configuration should exhibit:

1. **Higher Responsiveness**: Lower moment of inertia and friction coefficients make the boat more responsive to control inputs
2. **Faster Acceleration**: Lower mass allows quicker acceleration and deceleration
3. **More Sensitive to Wind**: Smaller sail area relative to mass makes wind effects more pronounced
4. **Quicker Turning**: Reduced rotation resistance allows faster heading changes
5. **Scale-Appropriate Dynamics**: All parameters scaled appropriately for the 65cm boat size

## Usage

To use this configuration in simulations, replace the boat configuration file:

```python
m = Manager(
    "boats/argo_boat.json",  # Use Argo configuration
    "environments/playground.json",
    boat_heading=270
)
```

## Tuning Notes

If the simulation behavior doesn't match expected RC boat characteristics, consider adjusting:

- **`hull_friction_coefficient`**: Increase (0.15 → 0.2) if boat seems too responsive
- **`hull_rotation_resistance`**: Increase (0.3 → 0.4) if turning is too quick
- **`moment_of_inertia`**: Increase (0.8 → 1.2) if boat feels too light/agile
- **`rudder_area`**: Adjust (0.008 → 0.006-0.012) for steering sensitivity

## References

- DragonForce 65 specifications from New Zealand Radio Yachting Association
- RC sailboat design principles and scaling factors
- Comparison with sample boat configuration for parameter estimation
