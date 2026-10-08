# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
# Some of the content of this file has been produced with the assistance of
# Met Office GitHub Copilot Enterprise.
import ants
import ants.tests
import iris
import iris.fileformats
import numpy as np
import numpy.testing
import pytest
from ants.io.load import ants_format_agent


def test_correct_specification_used_gdal():
    """Tests that the correct FileSpecification is being used with a horizontal
    namelist."""
    test_file = ants.tests.get_data_path("load_files/gdal_file")
    with ants_format_agent():
        with open(test_file, "rb") as buffer:
            used_spec = iris.fileformats.FORMAT_AGENT.get_spec(test_file, buffer)
            assert used_spec.name == "gdal"
            assert used_spec.priority == 0


def test_data_loaded_correctly():
    """Tests that the data matches what is expected when loading a gdal cube."""
    test_file = ants.tests.get_data_path("load_files/gdal_file")
    loaded_cube = ants.io.load.load_cube(test_file)
    expected_data = np.arange(18).reshape((6, 3))
    np.testing.assert_array_equal(loaded_cube.data.data, expected_data)


def test_correct_coord_system_loaded():
    """Tests that the coordinate system loads correctly when loading in a gdal file."""
    test_file = ants.tests.get_data_path("load_files/gdal_file")
    expected_coord_system = iris.coord_systems.GeogCS(6371229)
    loaded_cube = ants.io.load.load_cube(test_file)
    assert loaded_cube.coord_system() == expected_coord_system


def test_x_axis_points_loaded_correctly():
    """Tests that the points in the loaded cube on the x axis match what is
    expected."""
    test_file = ants.tests.get_data_path("load_files/gdal_file")
    loaded_cube = ants.io.load.load_cube(test_file)
    points = loaded_cube.coord(axis="x").points
    expected_points = (-120.0, 0.0, 120.0)
    numpy.testing.assert_array_equal(points, expected_points)


def test_y_axis_points_loaded_correctly():
    """Tests that the points in the loaded cube on the y axis match what is
    expected."""
    test_file = ants.tests.get_data_path("load_files/gdal_file")
    loaded_cube = ants.io.load.load_cube(test_file)
    points = loaded_cube.coord(axis="y").points
    expected_points = (-75.0, -45.0, -15.0, 15.0, 45.0, 75.0)
    numpy.testing.assert_array_equal(points, expected_points)


def test_x_axis_bounds_loaded_correctly():
    """Tests that the bounds in the loaded cube on the x axis match what is
    expected."""
    # construct the test bounds
    lower_bound_array = np.linspace(-180.0, 60.0, 3)
    upper_bound_array = np.linspace(-60.0, 180.0, 3)
    expected_bounds = np.column_stack((lower_bound_array, upper_bound_array))

    test_file = ants.tests.get_data_path("load_files/gdal_file")
    loaded_cube = ants.io.load.load_cube(test_file)
    bounds = loaded_cube.coord(axis="x").bounds
    numpy.testing.assert_array_equal(bounds, expected_bounds)


def test_y_axis_bounds_loaded_correctly():
    """Tests that the bounds in the loaded cube on the y axis match what is
    expected."""
    # construct the test bounds
    lower_bound_array = np.linspace(-90.0, 60.0, 6)
    upper_bound_array = np.linspace(-60.0, 90.0, 6)
    expected_bounds = np.column_stack((lower_bound_array, upper_bound_array))

    test_file = ants.tests.get_data_path("load_files/gdal_file")
    loaded_cube = ants.io.load.load_cube(test_file)
    bounds = loaded_cube.coord(axis="y").bounds
    numpy.testing.assert_array_equal(bounds, expected_bounds)


def test_metadata_loaded():
    """Loads a gdal file, along with associated metadata from sidecar files."""
    expected_attributes = {
        "license": "An example license\n",
        "attribution": "An example attribution\n",
        "restrictions": "An example restrictions\n",
        "institution": "An example institution\n",
        "acknowledgement": "An example acknowledgement\n",
        "references": "An example references\n",
    }

    with ants.tests.isolated_resource(
        "load_files/gdal_file", sidecars=expected_attributes
    ) as file_path:
        loaded_cube = ants.io.load.load_cube(file_path)
    assert loaded_cube.attributes["license"] == "An example license\n"
    assert loaded_cube.attributes["attribution"] == "An example attribution\n"
    assert loaded_cube.attributes["restrictions"] == "An example restrictions\n"
    assert loaded_cube.attributes["institution"] == "An example institution\n"
    assert loaded_cube.attributes["acknowledgement"] == "An example acknowledgement\n"
    assert loaded_cube.attributes["references"] == "An example references\n"


def test_metadata_not_loaded():
    """Loads a gdal file, ignoring associated metadata from sidecar files."""
    with ants.tests.isolated_resource(
        "load_files/gdal_file", sidecars={"license": "An example license\n"}
    ) as file_path:
        loaded_cube = ants.io.load.load_cube(file_path, ignore_metadata_files=True)
    assert "license" not in loaded_cube.attributes


def test_misnamed_licence_warning():
    """Loads a gdal file, along with metadata from a .licence sidecar file.

    A warning should be raised, and the metadata added to the license attribute.
    """
    expected_msg = (
        "The attribute name 'licence' has been changed to "
        "'license', in line with ANTS working practices."
    )
    with ants.tests.isolated_resource(
        "load_files/gdal_file", sidecars={"licence": "An example licence\n"}
    ) as file_path:
        with pytest.warns(ants.exceptions.MetadataWarning, match=expected_msg):
            loaded_cube = ants.io.load.load_cube(file_path)
    assert loaded_cube.attributes["license"] == "An example licence\n"


def test_invalid_metadata_warning():
    """Loads a gdal file, and tests that a warning is raised for an unsupported
    sidecar file: .invalid"""
    expected_msg = (
        r"Attribute 'invalid' is not a valid metadata file "
        r"name. Accepted metadata names are: \['license', 'attribution', "
        r"'restrictions', 'institution', 'acknowledgement', 'references'\]"
    )
    with ants.tests.isolated_resource(
        "load_files/gdal_file", sidecars={"invalid": "Invalid metadata file content"}
    ) as file_path:
        with pytest.warns(ants.exceptions.MetadataWarning, match=expected_msg):
            loaded_cube = ants.io.load.load_cube(file_path)
    assert "invalid" not in loaded_cube.attributes
