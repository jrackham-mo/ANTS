# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
from collections.abc import Callable
import ants.io.save
import iris
import inspect


class Application:

    def _init_savers(self):
        savers = {
            "ancil": ants.io.save.ancil,
            "netcdf": ants.io.save.netcdf,
            "ukca_netcdf": ants.io.save.ukca_netcdf,
            "iris": iris.save,
        }
        return savers

    def _validate_loaders(self, loaders, main):
        main_signature = inspect.signature(main)
        for loader in loaders:
            assert (
                loader in main_signature.parameters
            ), f"{loader} not a parameter of main: {main_signature.parameters}"

    def __init__(self, loaders: dict, settings: tuple, main: Callable):
        self._validate_loaders(loaders, main)
        self._validate_loaders(settings, main)
        self.loaders = loaders
        self.settings = settings
        self.main = main
        self.savers = self._init_savers()

    def add_saver(self, saver_name, saver_function):
        if saver_name in self.savers:
            raise ValueError(f"Cannot overwrite existing saver {saver_name}")
        self.savers[saver_name] = saver_function
