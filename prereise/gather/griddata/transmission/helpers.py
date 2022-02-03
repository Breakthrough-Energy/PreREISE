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
            if not isinstance(self.__dict__[name], (specified_type, default_type)):
                current_type = type(self.__dict__[name])
                raise TypeError(
                    f"for {name}: expected {specified_type}, but got {current_type}"
                )
