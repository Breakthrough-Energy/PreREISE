from math import pi, sqrt

import pytest

from prereise.gather.griddata.transmission.const import kilometers_per_mile as km_per_mi
from prereise.gather.griddata.transmission.geometry import (
    Conductor,
    ConductorBundle,
    Line,
    PhaseLocations,
    Tower,
)

# Conversion factor for tower spacing in feet to tower spacing in meters
m_in_ft = 304.8e-3


def test_conductor_by_parameter_values():
    # 'Cardinal' conductor
    outer_diameter = 0.03038
    strand_radius = 1.688e-3
    rated_dc_resistance_per_1000_ft = 0.0179
    rated_dc_resistance_per_km = rated_dc_resistance_per_1000_ft * 3.2808
    # Calculate for solid-aluminum (resistance should be lower than rated)
    conductor = Conductor(radius=(outer_diameter / 2), material="aluminum")
    assert conductor.resistance_per_km < rated_dc_resistance_per_km
    # Count 54 aluminum strands only for conductance purposes, ignore 7 steel strands
    # (resistance should be approximately equal to rated)
    area = 54 * pi * strand_radius**2
    conductor = Conductor(
        radius=(outer_diameter / 2),
        area=area,
        material="aluminum",
        current_limit=1015,
    )
    assert conductor.resistance_per_km == pytest.approx(rated_dc_resistance_per_km, 0.1)


def test_conductor_by_name():
    conductor = Conductor("cardinal")
    assert conductor.resistance_per_km == 0.0709
    assert conductor.radius == pytest.approx(0.01519)
    assert conductor.name == "Cardinal"


def test_conductor_name_and_parameters():
    with pytest.raises(TypeError):
        Conductor("Cardinal", resistance_per_km=0.1)


def test_conductor_bundle():
    spacing = 0.4572
    conductor = Conductor("Cardinal")  # standard ACSR conductor

    for n in (2, 3):
        bundle = ConductorBundle(n=n, spacing=spacing, conductor=conductor)
        assert bundle.resistance_per_km == conductor.resistance_per_km / n
        assert bundle.spacing_L == (conductor.gmr * spacing ** (n - 1)) ** (1 / n)
        assert bundle.spacing_C == (conductor.radius * spacing ** (n - 1)) ** (1 / n)


def test_tower_single_circuit():
    # Tower has two-conductor bundles (1.5 ft spacing), 24 ft b/w phases, 90 ft height
    spacing = 1.5 * m_in_ft
    locations = PhaseLocations(
        a=(-24 * m_in_ft, 90 * m_in_ft),
        b=(0, 90 * m_in_ft),
        c=(24 * m_in_ft, 90 * m_in_ft),
    )

    # Instantiate objects
    conductor = Conductor("Cardinal")  # standard ACSR conductor
    bundle = ConductorBundle(n=2, spacing=spacing, conductor=conductor)
    tower = Tower(locations=locations, bundle=bundle)

    # Calculate for 50-mile distances (test case)
    resistance_per_50_mi = tower.resistance * 50 * km_per_mi
    series_reactance_per_50_mi = 2 * pi * 60 * tower.inductance * 50 * km_per_mi
    shunt_admittance_per_50_mi = 2 * pi * 60 * tower.capacitance * 50 * km_per_mi

    # Expected values
    expected_resistance = 2.82  # Ohms
    expected_series_reactance = 29.2  # Ohms
    expected_shunt_admittance = 3.59e-4  # Siemens

    # Check
    # relative tolerance of 5% to account for unknown temperature for resistivity
    assert resistance_per_50_mi == pytest.approx(expected_resistance, rel=0.05)
    # Reactance & admittance values match within 1%, since they're purely gemetric
    assert series_reactance_per_50_mi == pytest.approx(
        expected_series_reactance, rel=0.01
    )
    assert shunt_admittance_per_50_mi == pytest.approx(
        expected_shunt_admittance, rel=0.01
    )

    line = Line(tower=tower, length=(50 * km_per_mi), voltage=345)
    assert line.power_rating == pytest.approx(1207, rel=0.01)


def test_tower_double_circuit():
    locations = PhaseLocations(
        circuits=2,
        a=((-9 * m_in_ft, 120 * m_in_ft), (9 * m_in_ft, 100 * m_in_ft)),
        b=((-10.5 * m_in_ft, 110 * m_in_ft), (10.5 * m_in_ft, 110 * m_in_ft)),
        c=((-9 * m_in_ft, 100 * m_in_ft), (9 * m_in_ft, 120 * m_in_ft)),
    )

    # Instantiate objects
    conductor = Conductor("Ostrich")  # standard ACSR conductor
    bundle = ConductorBundle(n=1, conductor=conductor)
    tower = Tower(locations=locations, bundle=bundle)

    # Calculate per-mile values (test case)
    series_reactance_per_mi = 2 * pi * 60 * tower.inductance * km_per_mi
    shunt_admittance_per_mi = 2 * pi * 60 * tower.capacitance * km_per_mi

    # Expected values
    expected_series_reactance = 0.372  # Ohms
    expected_shunt_admittance = 11.41e-6  # Siemens

    # Check
    assert series_reactance_per_mi == pytest.approx(expected_series_reactance, rel=0.01)
    assert shunt_admittance_per_mi == pytest.approx(expected_shunt_admittance, rel=0.01)


def test_line_long():
    conductor = Conductor("Rook")  # standard ACSR conductor
    conductor.resistance_per_km = 0.09963  # rated value at 50 C
    locations = PhaseLocations(a=(-7.25, 50), b=(0, 50), c=(7.25, 50))
    bundle = ConductorBundle(n=1, conductor=conductor)
    tower = Tower(locations=locations, bundle=bundle)
    line = Line(tower=tower, length=370, voltage=215)
    # The following values are appreciably different than what we would see using a
    # short-line model that just multiplies per-length by total length
    assert line.series_impedance.imag == pytest.approx(183.6619, rel=0.005)
    assert line.series_impedance.real == pytest.approx(34.20553, rel=0.005)
    assert line.shunt_admittance == pytest.approx(0.001198j, rel=0.005)
    assert line.surge_impedance_loading == pytest.approx(215**2 / 406.4, rel=0.005)
    assert line.thermal_rating == pytest.approx(215 * 795 * sqrt(3) / 1e3)
    assert line.power_rating == pytest.approx(1.14534 * 113.742, rel=0.005)


def test_line_short():
    short_line_length = 10  # km
    omega = 60 * 2 * pi
    conductor = Conductor("Rook")
    locations = PhaseLocations(a=(-7.25, 50), b=(0, 50), c=(7.25, 50))
    bundle = ConductorBundle(n=1, conductor=conductor)
    tower = Tower(locations=locations, bundle=bundle)
    line = Line(tower=tower, length=10, voltage=215)
    assert line.power_rating == line.thermal_rating
    assert line.series_impedance.imag == pytest.approx(
        line.tower.inductance * omega * short_line_length,
        rel=1e-4,
    )
    assert line.series_impedance.real == pytest.approx(
        line.tower.resistance * short_line_length,
        rel=1e-4,
    )
    assert line.shunt_admittance.imag == pytest.approx(
        short_line_length * line.tower.capacitance * omega, rel=1e-4
    )
