# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""
A general regrid application
****************************

Regrids data from a source to a target grid using
:class:`ants.regrid.GeneralRegridScheme`.  The result is written to an output
file.  The application supports both horizontal and vertical regridding.  The
regrid algorithm can be specified in the ants configuration file as described
in :class:`ants.config.GlobalConfiguration`. See :mod:`ants.regrid` for further
details.

If a landseamask is provided using the `target-lsm` argument, this mask is
honoured by only filling missing land points with valid land values (or
similarly, missing sea points with valid sea values).

********************
Zonal mean behaviour
********************

If the source and target provided have global extent in the 'x' axis, or if the
source has only one column ('x'), then the target will be processed to ensure
it fits the definition of a zonal mean. This ensures that a zonal mean output
is produced, regardless of the number of longitude
points in the regrid target.
"""
import functools
import ants
import ants.decomposition as decomp
import ants.io.save
import ants.utils
from ants.utils.cube import create_time_constrained_cubes
from ants.application import Application


def load_sources(filepath, begin=None, end=None):
    source_cubes = ants.io.load.load(filepath)
    if begin is not None:
        source_cubes = create_time_constrained_cubes(source_cubes, begin, end)
    return source_cubes


def load_target(
    filepath,
    target_type,
    land_fraction_threshold=None,
):
    """Load a regrid target cube from a grid or land sea mask.

    Parameters
    ----------
    filepath: str
        Path to a file load from
    target_type: str
        Either 'grid' or 'land_sea_mask'
    land_fraction_threshold: float, optional
        Threshold for converting the land fraction field into a landsea mask
        field.  0.5 would mean that any fraction greater than this will be
        masked.  This argument is used when loading a land fraction field.

    Returns
    -------
    iris.cube.Cube
        The regrid target
    """
    match target_type:
        case "grid":
            if land_fraction_threshold:
                raise ValueError(
                    "land_fraction_threshold is not needed for loading a target grid"
                )
            target_cube = ants.io.load.load_grid(filepath)
        case "lsm" | "landseamask" | "land_sea_mask":
            target_cube = ants.io.load.load_landsea_mask(
                filepath, land_fraction_threshold
            )
        case _:
            raise ValueError(f"Unsupported target type: {target_type}")
    return target_cube


SOURCES = {"sources": load_sources, "target": load_target}


OUTPUTS = {  # SAVERS
    "regrid_result": [
        ants.io.save.netcdf,
        ants.io.save.ancil,
        ants.io.save.ukca_netcdf,
    ],
}

SETTINGS = ("horizontal_scheme",)


def regrid(sources, target, horizontal_scheme=None, vertical_scheme=None):
    sources = ants.utils.cube.as_cubelist(sources)
    results = []
    scheme = ants.regrid.GeneralRegridScheme(horizontal_scheme, vertical_scheme)
    for source in sources:
        results.append(source.regrid(target, scheme))
    return results


def main(
    sources,
    target,
    horizontal_scheme,
    # invert_mask,
    # save_ukca,
    # netcdf_only,
    # search_method,
):
    """
    General regrid application top level call function.

    Loads source data cubes, regrids them to match target data cube
    co-ordinates, and saves result to output.  In addition to writing the
    resulting data cube to disk, also returns the regridded data cube.

    Parameters
    ----------

    source_path : str
        File path for one or more files which contain the data to be
        regridded.
    target_path : str
        File path for files that provide the grid to which the source data
        cubes will be mapped.  Separate files can be provided to generate a
        complete grid i.e. a namelist for vertical levels can be used with a
        data file for the horizontal coordinates.
    target_lsm_path : str
        File path for a land sea mask that provides the grid to which
        the source data cube will be mapped.  The output will be made
        consistent with this land sea mask.
    invert_mask : :obj:`bool`, optional
        Determines whether to invert the mask for the `target_lsm_path`
        argument.
        When set to True, treat target mask True (1) values as unmasked.  When set
        to False, treat target mask True (1) values as masked. Default is True.
    output_path : str
        Output file path to write the regridded data to.
    land_fraction_threshold : str
    begin : :obj:`datetime`, optional
        If provided, all source data prior to this year is discarded.  Default is to
        include all source data.
    end : :obj:`datetime`, optional
        If provided, all source data after this year is discarded.  Default is to
        include all source data.
    search_method : :obj:`str`
        This specifies which search routine is used in making the
        provided source(s) consistent with the provided land sea mask.
        This should only be provided if a target land sea mask is also
        provided via target_lsm_path.

    Returns
    -------
    : :class:`~iris.cube.Cube`
    A single data cube with the regridded data.

    """

    if ants.utils.cube._is_ugrid(target):
        raise ValueError(
            "Target appears to be a UGrid mesh - the regrid to mesh application in "
            "UG-ANTS should be used instead."
        )
    regrid_operation = functools.partial(regrid, horizontal_scheme=horizontal_scheme)
    regridded_cubes = decomp.decompose(regrid_operation, sources, target)
    # if target_lsm_path:
    #     ants.analysis.make_consistent_with_lsm(
    #         regridded_cubes, target, invert_mask, search_method
    #     )

    return {"regrid_result": regridded_cubes}


app = Application(SOURCES, SETTINGS, main)
