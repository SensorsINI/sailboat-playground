"""
Environmental Dynamics - Wind and Current Modeling

This module implements the environmental conditions for the sailing simulation,
including wind patterns, water currents, and their dynamic behavior over time.

## Environmental Components

The Environment class models two primary fluid dynamics:

### Wind System
- **Base Wind Speed**: Configurable minimum and maximum wind speeds
- **Wind Direction**: Fixed direction vector in degrees
- **Wind Gusts**: Stochastic gust events with configurable:
  - Probability of occurrence
  - Duration range (min/max)
  - Speed range (min/max)
  - Maximum delta percentage for gradual changes

### Water Current System
- **Current Speed**: Constant water flow velocity
- **Current Direction**: Fixed direction vector in degrees
- **Apparent Current**: Computed relative to boat motion in Manager

## Dynamic Behavior

### Wind Speed Evolution
The wind speed changes stochastically each simulation step:

1. **Normal Conditions**: Wind varies within base speed range
   - Uses `wind_min_speed` to `wind_max_speed`
   - Limited by `wind_max_delta_percent` for gradual changes

2. **Gust Events**: Enhanced wind during gust periods
   - Uses `wind_gust_min_speed` to `wind_gust_max_speed`
   - Limited by `wind_gust_max_delta_percent`
   - Duration controlled by gust duration parameters

### Time Integration
- **Simulation Time**: Tracks current simulation time in seconds
- **Gust Timing**: Manages gust start time and duration
- **State Transitions**: Handles normal ↔ gust state transitions

## Configuration Parameters

The environment loads from JSON configuration files containing:

### Wind Parameters
- `wind_direction`: Wind direction in degrees (0° = East)
- `wind_min_speed`, `wind_max_speed`: Base wind speed range
- `wind_max_delta_percent`: Maximum percentage change per step

### Gust Parameters
- `wind_gust_probability`: Probability of gust occurrence (0-1)
- `wind_gust_min_duration`, `wind_gust_max_duration`: Gust duration range
- `wind_gust_min_speed`, `wind_gust_max_speed`: Gust speed range
- `wind_gust_max_delta_percent`: Maximum gust speed change per step

### Current Parameters
- `current_direction`: Water current direction in degrees
- `current_speed`: Water current speed magnitude

## Vector Representations

Both wind and current are represented as 2D velocity vectors:
- **Wind Vector**: `[cos(wind_direction), sin(wind_direction)] * wind_speed`
- **Current Vector**: `[cos(current_direction), sin(current_direction)] * current_speed`
- **Coordinate System**: Uses trigonometric circle convention (0° = East)

## Integration with Simulation

The Environment integrates with the Manager class to provide:
- Apparent wind/current calculations relative to boat motion
- Realistic environmental variability for sailing algorithms
- Configurable difficulty through wind/current parameters
"""

__all__ = ["Environment"]

import json
import random
import numpy as np
from sailboat_playground.constants import constants, get_time_delta


class Environment:
    def __init__(self, config_file: str):
        try:
            with open(config_file, "r") as f:
                self._config = json.loads(f.read())
                f.close()
        except Exception as e:
            raise Exception(f"Failed to load configuration file: {e}")
        self._currentWindSpeed = (
            self.config["wind_min_speed"] + self.config["wind_max_speed"]
        ) / 2
        self._isWindGust = False
        self._currentWindGustStart = 0
        self._currentWindGustDuration = 0
        self._currentTime = 0

    @property
    def config(self):
        return self._config

    @property
    def wind_direction_rad(self):
        return self.config["wind_direction"] * np.pi / 180

    @property
    def current_direction_rad(self):
        return self.config["current_direction"] * np.pi / 180

    @property
    def wind_speed(self):
        return (
            np.array([np.cos(self.wind_direction_rad), np.sin(self.wind_direction_rad)])
            * self._currentWindSpeed
        )

    @property
    def water_speed(self):
        return (
            np.array(
                [np.cos(self.current_direction_rad), np.sin(self.current_direction_rad)]
            )
            * self.config["current_speed"]
        )

    @classmethod
    def get_delta_range(cls, current_speed, min_speed, max_speed, max_delta):
        delta_range = np.arange(min_speed, max_speed, 0.1)
        return list(
            delta_range[
                (delta_range > current_speed * (1 - max_delta / 100))
                & (delta_range < current_speed * (1 + max_delta / 100))
            ]
        )

    def execute(self):
        self._currentTime += get_time_delta()
        self.change_wind_speed()

    def change_wind_speed(self):
        if self._isWindGust:
            delta_range = self.get_delta_range(
                self._currentWindSpeed,
                self.config["wind_gust_min_speed"],
                self.config["wind_gust_max_speed"],
                self.config["wind_gust_max_delta_percent"],
            )
            try:
                self._currentWindSpeed = random.choice(delta_range)
            except IndexError:
                pass
            except Exception as e:
                raise e
            self._isWindGust = (
                self._currentTime - self._currentWindGustStart
            ) < self._currentWindGustDuration
        else:
            delta_range = self.get_delta_range(
                self._currentWindSpeed,
                self.config["wind_min_speed"],
                self.config["wind_max_speed"],
                self.config["wind_max_delta_percent"],
            )
            try:
                self._currentWindSpeed = random.choice(delta_range)
            except IndexError:
                pass
            except Exception as e:
                raise e
            self._isWindGust = random.random() < self.config["wind_gust_probability"]
            if self._isWindGust:
                self._currentWindGustDuration = random.choice(
                    np.arange(
                        self.config["wind_gust_min_duration"],
                        self.config["wind_gust_max_duration"],
                        get_time_delta(),
                    )
                )
