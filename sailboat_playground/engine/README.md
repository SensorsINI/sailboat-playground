# Engine Module - Sailing Simulation Physics Engine

The `engine` module contains the core physics simulation components for the sailboat playground. It provides a complete 2D sailing simulation with realistic boat dynamics, environmental forces, and control systems.

## Architecture Overview

The engine follows a modular architecture with clear separation of concerns:

```
Manager (Coordinator)
├── Boat (Physics Model)
├── Environment (Wind/Current)
└── utils (Mathematical Utilities)
```

## Core Components

### Manager.py - Simulation Coordinator
**Purpose**: Central controller that integrates all simulation components

**Key Responsibilities**:
- Coordinates between Boat physics and Environment dynamics
- Computes and applies all physical forces (wind, water, rudder)
- Provides agent interface for sailing algorithms
- Manages simulation state and debug logging

**Main Methods**:
- `step([sail_angle, rudder_angle])`: Main simulation step - requires integer angles
- `state`: Complete simulation state (environment + boat + controls)
- `agent_state`: Simplified state for sailing algorithms

**Force Integration**:
1. **Wind Forces on Sail**: Apparent wind calculation, aerodynamics, driving force
2. **Water Forces on Hull**: Hull resistance and drag forces
3. **Water Forces on Rudder**: Rudder aerodynamics and steering torque

### Boat.py - Physical Boat Model
**Purpose**: Implements boat physics, kinematics, and control surfaces

**Key Responsibilities**:
- Manages boat physical state (position, velocity, heading)
- Handles sail and rudder control surfaces
- Implements force/acceleration integration
- Provides aerodynamic foil lookup tables

**State Variables**:
- `_position`: 2D position [x, y] in meters
- `_speed`: 2D velocity [vx, vy] in m/s
- `_heading`: Boat orientation in degrees (0° = East)
- `_alpha`: Sail angle of attack in degrees
- `_rudder_angle`: Rudder deflection in degrees

**Physics Methods**:
- `apply_force(force)`: Apply translational forces
- `apply_angular_acceleration(accel)`: Apply rotational forces
- `execute()`: Integrate position and heading (handles 2π cut problem)

### Environment.py - Environmental Dynamics
**Purpose**: Models wind patterns and water currents

**Key Responsibilities**:
- Simulates realistic wind speed variations
- Handles wind gust events with configurable parameters
- Provides water current vectors
- Manages environmental time evolution

**Wind System**:
- **Base Wind**: Configurable min/max speeds with gradual changes
- **Wind Gusts**: Stochastic gust events with duration and intensity ranges
- **Wind Direction**: Fixed direction vector

**Water Current System**:
- **Current Speed**: Constant water flow velocity
- **Current Direction**: Fixed direction vector

### utils.py - Mathematical Utilities
**Purpose**: Provides essential vector mathematics for the simulation

**Functions**:
- `compute_angle(vec)`: Convert 2D vector to angle in radians [0, 2π)
- `norm_to_vector(norm, angle)`: Convert magnitude/angle to 2D vector

## Configuration System

### Boat Configuration (JSON)
```json
{
  "mass": 1000,
  "sail_area": 25,
  "hull_area": 5,
  "rudder_area": 2,
  "sail_foil": "naca0015",
  "rudder_foil": "naca0015",
  "hull_friction_coefficient": 0.02,
  "hull_rotation_resistance": 0.01,
  "length": 10,
  "com_length": 3,
  "moment_of_inertia": 5000
}
```

### Environment Configuration (JSON)
```json
{
  "wind_direction": 45,
  "wind_min_speed": 5,
  "wind_max_speed": 15,
  "wind_max_delta_percent": 10,
  "wind_gust_probability": 0.1,
  "wind_gust_min_duration": 5,
  "wind_gust_max_duration": 15,
  "wind_gust_min_speed": 20,
  "wind_gust_max_speed": 30,
  "wind_gust_max_delta_percent": 15,
  "current_direction": 0,
  "current_speed": 1
}
```

### Foil Data (CSV)
Aerodynamic coefficients for sail and rudder foils:
- `alpha`: Angle of attack in degrees
- `cl`: Lift coefficient
- `cd`: Drag coefficient

## Coordinate System

The simulation uses standard trigonometric circle convention:
- **X-axis**: East (0°)
- **Y-axis**: North (90°)
- **Positive rotation**: Counter-clockwise
- **Angles**: Degrees for input/output, radians for internal calculations
- **Positions**: Meters in Cartesian coordinates

## Critical Requirements

### Integer Angles
**IMPORTANT**: The `Manager.step()` method requires integer arguments:
```python
# CORRECT
m.step([int(sail_angle), int(rudder_angle)])

# INCORRECT - Will cause TypeError
m.step([sail_angle, rudder_angle])  # if angles are floats
```

### Angle Normalization
The simulation handles the 2π cut problem through:
- **Boat heading**: Normalized to [0°, 360°) in `Boat.execute()`
- **Vector angles**: Normalized to [0, 2π) in `utils.compute_angle()`
- **Force calculations**: Angle wrapping handled throughout `Manager.step()`

## Integration Example

```python
from sailboat_playground.engine import Manager

# Initialize simulation
m = Manager("boats/my_boat.json", "environments/race_course.json")

# Simulation loop
for step in range(1000):
    state = m.agent_state
    
    # Your sailing algorithm here
    sail_angle = calculate_sail_angle(state)
    rudder_angle = calculate_rudder_angle(state)
    
    # Step simulation (requires integer angles)
    m.step([int(sail_angle), int(rudder_angle)])
    
    # Access complete state if needed
    full_state = m.state
```

## Performance Considerations

- Uses Cython for performance-critical components
- Force calculations optimized for real-time simulation
- Foil lookup tables pre-computed for efficiency
- Fixed timestep integration for numerical stability

## Error Handling

- Validates configuration file formats
- Handles angle normalization gracefully
- Provides debug logging for physics troubleshooting
- Validates agent input format and types
