# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
import numpy as np
import pytest
from ants.analysis._merge import blend_data


def test_invalid_blending_distance():
    primary = np.array([0])
    alternate = np.array([0])
    mask = np.array([0])
    blending_distance = 0
    expected_msg = "Invalid blending_distance: 0. Must be greater than zero"
    with pytest.raises(ValueError, match=expected_msg):
        blend_data(primary, alternate, mask, blending_distance)


def test_blending_1D():
    primary = np.zeros((7,), dtype=np.float64)
    alternate = np.ones_like(primary)
    mask = np.array([0, 0, 1, 1, 1, 1, 1], dtype=bool)
    blending_distance = 4

    expected = np.array([0, 0, 0.25, 0.5, 0.75, 1, 1])

    blended = blend_data(primary, alternate, mask, blending_distance)

    np.testing.assert_array_equal(blended, expected)


def test_blending_2D():
    primary = np.zeros((7, 7), dtype=np.float64)
    alternate = np.ones_like(primary)
    mask = np.array(
        [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 0, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
        ],
        dtype=bool,
    )
    blending_distance = 2.5

    expected = np.array(
        [
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 0.89442719, 0.8, 0.8, 0.8, 0.89442719, 1.0],
            [0.89442719, 0.56568542, 0.4, 0.4, 0.4, 0.56568542, 0.89442719],
            [0.56568542, 0.4, 0.0, 0.0, 0.0, 0.4, 0.56568542],
            [0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4],
            [0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4],
            [0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4],
        ]
    )

    blended = blend_data(primary, alternate, mask, blending_distance)

    np.testing.assert_array_almost_equal(blended, expected)
