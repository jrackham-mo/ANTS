#!/usr/bin/env python

import json

import ants.io.save
import ants.tests.stock
import numpy as np

SHAPE = (216, 432)

source_data_1 = np.arange(np.prod(SHAPE), dtype=np.float64).reshape(SHAPE)
source_cube_1 = ants.tests.stock.geodetic(data=source_data_1)

source_data_2 = np.zeros_like(source_data_1)
source_cube_2 = ants.tests.stock.geodetic(data=source_data_2)

ants.io.save.netcdf(source_cube_1, ".scratch/source_1.nc", netcdf_format="NETCDF4")
ants.io.save.netcdf(source_cube_2, ".scratch/source_2.nc", netcdf_format="NETCDF4")


# generate polygon
theta = np.linspace(0, np.pi * 2)
r = 30.0 + 10 * np.sin(theta * 5)
x = r * np.cos(theta)
y = r * np.sin(theta)
xy = np.stack((x, y)).T
with open(".scratch/polygon.json", "w") as f:
    json.dump(xy.tolist(), f)
