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
    config = configparser.ConfigParser()
    config.read(filepath)
    recipe = {section: dict(config[section]) for section in config.sections()}
    return recipe


def validate(recipe):  # noqa: D103
    print("Validating recipe:\n", recipe)


def run(recipe):  # noqa: D103
    print(recipe)
    app = importlib.import_module(recipe["ants"]["app"])

    loaded_sources = {}
    for source_name, source_loader in app.SOURCES.items():
        source_section = f"ants.sources.{source_name}"
        source_load_kwargs = {
            key: os.path.expandvars(value)
            for key, value in recipe[source_section].items()
        }
        loaded_source = source_loader(**source_load_kwargs)
        loaded_sources[source_name] = loaded_source

    settings = {}
    for setting_name in app.SETTINGS:
        recipe_value = recipe["ants.settings"][setting_name]
        recipe_value = os.path.expandvars(recipe_value)
        settings[setting_name] = recipe_value

    kwargs = loaded_sources | settings

    print("Parsed recipe:\n", kwargs)
    results = app.main(**kwargs)

    for output_name, output_savers in app.OUTPUTS.items():
        result = results[output_name]
        for saver in output_savers:
            output_section = f"ants.outputs.{output_name}.{saver.__qualname__}"
            save_kwargs = {
                key: os.path.expandvars(config_value)
                for key, config_value in recipe[output_section].items()
            }
            saver(result, **save_kwargs)


def recipe_gen(app_module):
    """Generate a blank recipe file consistent with the given app."""
    app = importlib.import_module(app_module)
    recipe = configparser.ConfigParser(allow_no_value=True)

    recipe.add_section("ants")
    recipe["ants"]["app"] = app_module

    for source_name, source_loader in app.SOURCES.items():
        source_name_section = f"ants.sources.{source_name}"
        recipe.add_section(source_name_section)
        recipe.set(source_name_section, "# Configure your sources here")
        recipe.set(
            source_name_section,
            f"# uses {source_loader.__module__}.{source_loader.__qualname__}",
        )
        for arg_name, parameter in inspect.signature(source_loader).parameters.items():
            recipe[source_name_section][arg_name] = _gen_entry(parameter)

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
