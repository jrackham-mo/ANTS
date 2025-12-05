# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of ANTS and is released under the BSD 3-Clause license.
# See LICENSE.txt in the root of the repository for full licensing details.
"""Entrypoint for running ANTS applications.

conda env create -p <path/to/install/developer/environment> -f environment.yml
conda activate <path/to/install/developer/environment>
pip install -e .

ants --help
"""

import argparse
import configparser
import importlib
import inspect
import os
import pathlib
import sys

import yaml
from ants import __version__
from ants.application import Application


def resolve_path(filepath: str):  # noqa: D103
    path = pathlib.Path(filepath)
    path = path.resolve(strict=True)
    return path


def load_recipe(filepath: str):  # noqa: D103
    filepath = resolve_path(filepath)
    print(f"Reading recipe from {filepath}")
    match filepath.suffix:
        case ".yml" | ".yaml":
            return _load_yaml(filepath)
        case ".conf" | ".ini":
            return _load_conf(filepath)
        case _:
            raise ValueError(f"Unsupported file type: {filepath.suffix}")


def _load_yaml(filepath):
    with open(filepath) as f:
        recipe = yaml.safe_load(f)
    return recipe


def _load_conf(filepath):
    config = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    config.read(filepath)
    recipe = {section: dict(config[section]) for section in config.sections()}
    return recipe


def validate(recipe):  # noqa: D103
    print("Validating recipe:\n", recipe)


def run(recipe):  # noqa: D103
    print(recipe)
    app: Application
    app = importlib.import_module(recipe["ants"]["app"]).app

    loaded_sources = {}
    for source_name, source_loader in app.loaders.items():
        source_section = f"ants.sources.{source_name}"
        source_load_kwargs = {
            key: os.path.expandvars(value)
            for key, value in recipe[source_section].items()
        }
        print(
            f"Attempting to load {source_name} using {source_loader} with "
            f"{source_load_kwargs}"
        )
        loaded_source = source_loader(**source_load_kwargs)
        loaded_sources[source_name] = loaded_source

    settings = {}
    for setting_name in app.settings:
        recipe_value = recipe["ants.settings"][setting_name]
        recipe_value = os.path.expandvars(recipe_value)
        settings[setting_name] = recipe_value

    kwargs = loaded_sources | settings

    print("Parsed recipe:\n", kwargs)
    results = app.main(**kwargs)

    output_sections = dict(
        filter(lambda x: x[0].startswith("ants.outputs"), recipe.items())
    )
    for output_section in output_sections.values():
        saver_name = output_section["saver"]
        saver = app.savers[saver_name]
        result_name = output_section["result"]
        result = results[result_name]
        save_kwargs = {
            key: os.path.expandvars(value)
            for key, value in output_section.items()
            if key not in ("saver", "result")
        }
        print(
            f"Attempting to save {result_name} using {saver_name} with "
            f"{save_kwargs}"
        )
        saver(result, **save_kwargs)


def recipe_gen(app_module):
    """Generate a blank recipe file consistent with the given app."""
    app: Application
    app = importlib.import_module(app_module).app
    recipe = configparser.ConfigParser(allow_no_value=True)

    recipe.add_section("ants")
    recipe["ants"]["app"] = app_module

    for source_name, source_loader in app.loaders.items():
        source_name_section = f"ants.sources.{source_name}"
        recipe.add_section(source_name_section)
        recipe.set(source_name_section, "# Configure your sources here")
        recipe.set(
            source_name_section,
            f"# uses {source_loader.__module__}.{source_loader.__qualname__}",
        )
        for arg_name, parameter in inspect.signature(source_loader).parameters.items():
            recipe[source_name_section][arg_name] = _gen_entry(parameter)

    recipe.add_section("ants.settings")
    for setting in app.settings:
        recipe.set("ants.settings", setting, f"<{setting}>")

    recipe.write(sys.stdout)


def _gen_entry(param: inspect.Parameter):
    if param.default == param.empty:
        return f"<{param.name}> # (required)"
    else:
        return f"<{param.name}> # (optional, default is {param.default})"


def main():  # noqa: D103
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(title="subcommands")

    # Set up "run" subparser
    run_help = "Run a UG-ANTS application"
    run_subparser = subparsers.add_parser(
        name="run", help=run_help, description=run_help
    )
    run_subparser.add_argument(
        "recipe", help="Path to a recipe file to run", type=load_recipe
    )
    run_subparser.set_defaults(func=run)

    # Set up "validate" subparser
    validate_help = "Validate a UG-ANTS recipe"
    validate_subparser = subparsers.add_parser(
        "validate", help=validate_help, description=validate_help
    )
    validate_subparser.add_argument(
        "recipe", help="Path to a recipe file to validate", type=load_recipe
    )
    validate_subparser.set_defaults(func=validate)

    # Set up "recipe-gen" subparser
    recipe_gen_help = "Generate a blank recipe for an app"
    recipe_gen_subparser = subparsers.add_parser(
        "recipe-gen", help=recipe_gen_help, description=recipe_gen_help
    )
    recipe_gen_subparser.add_argument(
        "app_module", help="Python module defining the app"
    )
    recipe_gen_subparser.set_defaults(func=recipe_gen)

    args = parser.parse_args()
    kwargs = vars(args)
    func = kwargs.pop("func")

    func(**kwargs)
