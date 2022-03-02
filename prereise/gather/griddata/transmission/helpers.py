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
