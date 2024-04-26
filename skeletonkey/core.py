import argparse
import functools
import os
import sys
from typing import Callable, Optional

from .config import (
    get_command_line_config,
    load_yaml_config,
    add_args_from_dict,
    add_yaml_extension,
    update_flat_config_types,
    config_to_nested_config,
    Config
)


def get_config_dir_path(config_path: str) -> str:
    """
    Convert a given relative or absolute config file path to its absolute directory path.

    Args:
        config_path (str): The path to the configuration file. Can be either relative or absolute.

    Returns:
        str: The absolute directory path containing the configuration file.
    """
    # Check if the given config_path is a relative path
    if not os.path.isabs(config_path):
        # Get the directory of the main script file (entry point) in absolute form
        path_from_main = os.path.dirname(
            os.path.abspath(str(sys.modules["__main__"].__file__))
        )

        if config_path.startswith("./"):
            config_path = config_path[len("./") :]

        # Traverse up the directory structure for each "../" in config_path
        # Remove the "../" string from the path, and remove a directory from main.
        while config_path.startswith("../"):
            config_path = config_path[len("../") :]
            path_from_main = os.path.dirname(path_from_main)

        # Create absolute path.
        config_path = os.path.join(path_from_main, config_path)
    return config_path


def unlock(config_name: Optional[str] = None, config_path: Optional[str] = None) -> Callable:
    """
    Create a decorator for parsing and injecting configuration arguments into a
    main function from a YAML file.

    Args:
        config_name (str): The name of the YAML configuration file.
        config_path (str): The path to the directory containing the configuration
                           file. Defaults to the current directory.

    Returns:
        Callable: A decorator function that, when applied to a main function, will
                  parse the configuration file and inject the arguments into the
                  main function.
    """
    parser = argparse.ArgumentParser()
    command_line_config_path, remaining_args = get_command_line_config(parser)
    
    if command_line_config_path:
        config_name = os.path.abspath(command_line_config_path)
        config_path = None

    if config_name == None and command_line_config_path == None:
        raise ValueError("config path is neither specified in 'unlock' nor via the command line.")
    
    config_path = config_path if config_path else os.path.dirname(config_name)
    
    if not command_line_config_path:
        config_path = get_config_dir_path(config_path)

    config_name = add_yaml_extension(config_name)
    config_name = os.path.basename(config_name)

    config = load_yaml_config(config_path, config_name)

    def _parse_config(main: Callable):
        @functools.wraps(main)
        def _inner_function():
            add_args_from_dict(parser, config)
            args = parser.parse_args(remaining_args)
            args = update_flat_config_types(args)
            args = config_to_nested_config(args)
            return main(args)

        return _inner_function

    return _parse_config

