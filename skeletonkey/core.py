import argparse
import functools
import os
import sys
from typing import Callable, Optional
import warnings

from .config import (
    parse_initial_args,
    load_yaml_config,
    add_args_from_dict,
    add_yaml_extension,
    namespace_to_config,
    config_to_nested_config,
    Config,
)

BASE_PROFILES_KEYWORD: str = "profiles"
BASE_COLLECTION_KEYWORD: str = "keyring"
BASE_CL_CONFIG_KEYWORD: str = "config"


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


def unlock(
    config_name: Optional[str] = None, 
    config_dir: Optional[str] = None,
    prefix: Optional[str] = None,
    config_argument_keyword: Optional[str] = BASE_CL_CONFIG_KEYWORD,
    profiles_keyword: Optional[str] = BASE_PROFILES_KEYWORD,
    collection_keyword: Optional[str] = BASE_COLLECTION_KEYWORD,
) -> Callable:
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
    # Parse high-level arguments
    parser = argparse.ArgumentParser(allow_abbrev=False)    
    initial_args = parse_initial_args(
        arg_parser=parser, 
        config_argument_keyword=config_argument_keyword, 
        profiles_keyword=profiles_keyword,
    )
    config_dir_command_line, profile, profile_specifiers, temp_args = initial_args
    
    # Find final config name and directory
    if config_dir_command_line is not None:
        config_name = os.path.abspath(config_dir_command_line)
        config_dir = None

        # If they have more than one unlock, warn user than the command-line config will
        # overwrite all the configs for all unlocks.
        if not hasattr(unlock, "_command_line_unlock"):
            setattr(unlock, "_command_line_unlock", {})
            unlock._command_line_unlock[config_argument_keyword] = unlock._command_line_unlock.get(config_argument_keyword, 0) + 1

        if unlock._command_line_unlock.get(config_argument_keyword, 0) > 1:
            warnings.warn(f"Multiple @unlock decorators are present with the same command line keyword " 
                          + f"'{config_argument_keyword}'. The command line configurations will be used for all @unlock calls.")

    if config_name is not None:
        config_dir = get_config_dir_path(os.path.dirname(config_name))
    else: 
        raise ValueError("config path is neither specified in 'unlock' nor via the command line.")
    config_name = os.path.basename(add_yaml_extension(config_name))

    # Create decorator
    def _parse_config(main: Callable):
        @functools.wraps(main)
        def _inner_function(config: Config=None):
            config_dict = load_yaml_config(
                config_path=config_dir, 
                config_name=config_name, 
                profile=profile, 
                profile_specifiers=profile_specifiers,
                profiles_keyword=profiles_keyword,
                collection_keyword=collection_keyword
            )

            add_args_from_dict(
                arg_parser=parser, 
                config_dict=config_dict, 
                prefix=prefix + "." if prefix is not None else "",
            )

            args, unparsed_args = parser.parse_known_args()
            unparsed_args = [arg.strip("--") for arg in unparsed_args]
            args = namespace_to_config(args)

            for temp_arg in temp_args:
                del args[temp_arg]

            args = config_to_nested_config(args, unparsed_args)
            
            if config is not None:
                args.update(config)

            return main(args)

        return _inner_function

    return _parse_config

