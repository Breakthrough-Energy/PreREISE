from dataclasses import dataclass

import pytest

from prereise.gather.griddata.transmission.helpers import (
    DataclassWithValidation,
    calculate_z_base,
    translate_to_per_unit,
)


@pytest.fixture()
def custom_dataclass():
    @dataclass
    class TestDataclass(DataclassWithValidation):
        a: int
        b: float = None

    return TestDataclass


def test_DataclassWithValidation_success(custom_dataclass):  # noqa: N802
    custom_dataclass(a=2, b=3.0).validate_input_types()
    custom_dataclass(a=2).validate_input_types()


def test_DataclassWithValidation_bad_inputs(custom_dataclass):  # noqa: N802
    test_object = custom_dataclass(a=2.0)
    with pytest.raises(TypeError):
        # This should raise an error since we pass a float instead of an int to 'a'
        test_object.validate_input_types()


def test_DataclassWithValidation_not_a_dataclass():  # noqa: N802
    # For consistency, we'll add a class with the same inputs as custom_dataclass
    class NotDataclass(DataclassWithValidation):
        def __init__(self, a, b):
            self.a = a
            self.b = b

    test_object = NotDataclass(a=2, b=3.0)
    with pytest.raises(TypeError):
        test_object.validate_input_types()


def test_calculate_z_base():
    assert calculate_z_base(345, 100) == 1190.25


def test_translate_to_per_unit():
    z_base = 1190.25
    rel = 0.005
    assert translate_to_per_unit(2.82, "ohms", z_base) == pytest.approx(2.37e-3, rel)
    assert translate_to_per_unit(29.2, "x", z_base) == pytest.approx(2.45e-2, rel)
    assert translate_to_per_unit(3.59e-4, "siemen", z_base) == pytest.approx(0.427, rel)
