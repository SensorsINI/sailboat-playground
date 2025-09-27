__all__ = ["constants", "get_time_delta"]

import json
import os


def const(cls):
    def is_special(name):
        return name.startswith("__") and name.endswith("__")

    class_contents = {n: getattr(cls, n) for n in vars(cls) if not is_special(n)}

    def unbind(value):
        return lambda self: value

    propertified_contents = {
        name: property(unbind(value)) for (name, value) in class_contents.items()
    }
    receptor = type(cls.__name__, (object,), propertified_contents)
    return receptor()


def get_time_delta():
    """Load time_delta from simulator.json configuration file."""
    try:
        # Get the directory where this constants.py file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        simulator_config_path = os.path.join(current_dir, "simulator.json")

        with open(simulator_config_path, "r") as f:
            config = json.load(f)
            return config.get("time_delta", 0.1)  # Default to 0.1 if not found
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        # If simulator.json doesn't exist or is malformed, use default value
        print(f"Warning: Could not load time_delta from simulator.json: {e}")
        print("Using default time_delta = 0.1 seconds")
        return 0.1


@const
class constants(object):
    # epsilon is not used anywhere in the project; consider removing if not needed
    # epsilon = 1e-7

    # time_delta is loaded dynamically from simulator.json
    # This function loads the value each time it's accessed
    def time_delta(self):
        return get_time_delta()

    sea_water_rho = 1029  # kg / m^3
    wind_rho = 1.225  # kg / m^3
