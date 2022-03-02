import os

import pandas as pd

from prereise.gather.griddata.transmission.const import (
    kilometers_per_mile,
    st_clair_power_approx_coeff,
    st_clair_power_approx_exponent,
)


class DataclassWithValidation:
    """A stub class which defines a method that checks dataclasses.dataclass types."""

    _required_dataclass_attrs = ("__annotations__", "__dataclass_fields__")

    def validate_input_types(self):
        # Check for the presence of attributes which are added via @dataclass
        if not all(hasattr(self, a) for a in self._required_dataclass_attrs):
            raise TypeError(
                "_validate_input_types can only be called on dataclassed objects."
            )
        for (name, specified_type) in self.__annotations__.items():
            # Ignore attributes that aren't passed via the __init__ method
            if not self.__dataclass_fields__[name].init:
                continue
            # Check whether the attribute is the specified or default type
            # This supports inputs which have a default value of None
            default_type = type(self.__dataclass_fields__[name].default)
            value_received = self.__dict__[name]
            if specified_type == float and isinstance(value_received, int):
                # per PEP 484, accept an int when a float is specified
                continue
            if not isinstance(value_received, (specified_type, default_type)):
                current_type = type(value_received)
                raise TypeError(
                    f"for {name}: expected {specified_type}, but got {current_type}"
                )


def calculate_z_base(v_base, s_base):
    """Calculate base impedance from voltage and system base apparent power.

    :param int/float v_base: base voltage (kV).
    :param int/float s_base: base apparent power (MVA).
    :return: (*float*) -- base impedance (ohms).
    """
    return (v_base**2) / s_base


def translate_to_per_unit(x, nominal_unit, z_base):
    """Translate parameters in nominal units to per-unit values.

    :param int/float x: value to be converted.
    :param str nominal_unit: the units of ``x``.
    :param int/float z_base: base impedance (can be calculated with
        :func:`calculate_z_base').
    :return: (*float*) -- per-unit value.
    :raises ValueError: if the nominal unit isn't recognized.
    """
    if nominal_unit.lower() in {"ohm", "ohms", "r", "x"}:
        return x / z_base
    if nominal_unit.lower() in {"siemen", "siemens"}:
        return x * z_base
    raise ValueError(f"Unknown nominal unit: {nominal_unit}")


def get_standard_conductors():
    """Read the data file on standard conductor parameter values.

    :return: (*pandas.DataFrame*) -- data frame, indexed by conductor code name.
    """
    filepath = os.path.join(os.path.dirname(__file__), "data", "conductors.csv")
    return pd.read_csv(filepath, index_col=0)


def approximate_loadability(length_km, method="power"):
    """Approximate the value of the St. Clair curve at a given point, using a given
    approximation method.

    :param float length_km: line length (kilometers).
    :param str method: curve approximation method. Currently, only 'power' is supported.
    :return: (*float*) -- line loadibility (normalized to surge impedance loading).
    :raises ValueError: if the ``method`` is not supported.
    """
    miles = length_km / kilometers_per_mile
    allowable_methods = {"power"}
    if method == "power":
        return st_clair_power_approx_coeff * miles**st_clair_power_approx_exponent
    raise ValueError(f"Unsupported method: {method}. Choose from: {allowable_methods}")
