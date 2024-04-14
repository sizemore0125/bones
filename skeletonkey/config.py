"""
Author: Logan Sizemore
Date: 4/27/23

This code provides a set of utility functions to handle YAML configurations. 
It facilitates the management of complex configurations for applications using YAML 
files and enables the dynamic loading of classes and their arguments at runtime.
"""
import yaml
import argparse
import os
from typing import List, Tuple

from .instantiate import instantiate

BASE_DEFAULT_KEYWORD: str = "defaults"
BASE_COLLECTION_KEYWORD: str = "keyring"

class Config():
    def __init__(self, *args, **kwargs):
        """
        Initializes the config from a dictionary or from kwargs.\n

        Args:
            Either a single dictionary as an arg or suply a number of kwargs.
        """

        if (len(args) != 0) and (len(kwargs) != 0):
            raise ValueError("Config should not receive args and kwargs at the same time.")
        
        elif not (len(args) == 0 or len(args) == 1):
            raise ValueError("Config should not receive more than one non-keyword argument.")


        if len(args) == 1:
            if not isinstance(args[0], dict):
                raise ValueError("Supplied arg must be a dictionary")
            self._init_from_dict(args[0])
        else:
            self._init_from_dict(kwargs)


    def _init_from_dict(self, dictionary: dict):
        """
        Initialize the config from a dictionary

        Args:
            dictionary (dict): The dictionary to be converted.
        """
        for key, value in dictionary.items():
            if isinstance(value, dict):
                value = Config(value)
       
            self[key] = value

    def __getitem__(self, key:str):
        return self.__getattribute__(key)

    def __setitem__(self, key: str, value):
        self.__setattr__(key, value)


    def __delitem__(self, key: str):
        self.__delattr__()

    def __str__(self):
        return self._subconfig_str(self, 0)[1:]

    def __repr__(self):
        return f"Config({self._subconfig_str(self, 1)})"
    
    def instantiate(self, **kwargs):
        return instantiate(self, **kwargs)

    def __call__(self, **kwargs):
        return self.instantiate(**kwargs)

    def _subconfig_str(self, subspace: "Config", tab_depth:int):
        """
        Convert a given subconfig to a string with the given tab-depth
        
        args:
            subspace: A Config object
            tab_depth: an integer representing the current tab depth
        """
        s = ""
        for k, v in subspace.__dict__.items():
            s += "\n" + "  "*tab_depth + k + ": "
            
            if isinstance(v, Config):
                s+= "\n"
                s+= self._subconfig_str(v, tab_depth+1)[1:] # [1:] gets rid of uneccesary leading \n
            else:
                s += str(v)

        return s


def find_yaml_path(file_path: str) -> str:
    """
    Given a file path, this function checks if a YAML file exists with either
    '.yml' or '.yaml' extension, and returns the correct path.

    Args:
        file_path (str): The file path without extension or with either '.yml' or '.yaml' extension.

    Returns:
        str: The correct file path with the existing extension.

    Raises:
        FileNotFoundError: If no YAML file is found with either extension.
    """
    base_path, ext = os.path.splitext(file_path)

    yml_path = base_path + ".yml"
    yaml_path = base_path + ".yaml"

    if os.path.isfile(yml_path):
        return yml_path
    elif os.path.isfile(yaml_path):
        return yaml_path
    else:
        raise FileNotFoundError(
            f"No YAML file found with either '.yml' or '.yaml' extension for path: {base_path}. You may have mistakenly specified an absolute path."
        )


def open_yaml(path: str) -> dict:
    """
    Read and parse the YAML file located at the given path.

    Args:
        path (str): The file path to the YAML file.

    Returns:
        dict: A dictionary representing the YAML content.
    """
    path = find_yaml_path(path)
    with open(os.path.expanduser(path), "r") as handle:
        return yaml.safe_load(handle)


def dict_to_path(dictionary: dict, parent_key="") -> List[str]:
    """
    Flatten a nested dictionary into a single-level dictionary by concatenating
    nested keys using a specified separator.

    Args:
        dictionary (dict): The nested dictionary to be flattened.
        parent_key (str): The initial parent key, default is an empty string.
        sep (str): The separator used to concatenate nested keys, default is '/'.

    Returns:
        dict: A flattened dictionary with single-level keys.
    """
    items = []
    for key, value in dictionary.items():
        # Create a new key by concatenating the parent key and the current key
        new_key = os.path.join(parent_key, key) if parent_key else key
        if isinstance(value, dict):
            # If the value is a nested dictionary, recursively flatten it
            items.extend(dict_to_path(value, new_key))
        elif isinstance(value, list):
            # If the value is a list, iterate through the items in the list
            for item in value:
                if isinstance(item, dict):
                    # If an item in the list is a dictionary, flatten it
                    sublist_items = dict_to_path(item, new_key)
                    items.extend(sublist_items)
                else:
                    # If the item is not a dictionary, append it to the key
                    items.append(os.path.join(new_key, item))
        else:
            # If the value is neither a dictionary nor a list, add it to the items
            items.append(os.path.join(new_key, value))

    return items


def add_yaml_extension(path: str) -> str:
    """
    Append the '.yaml' extension to a given path if it doesn't already have it.

    Args:
        path (str): The input file path or name.

    Returns:
        str: The modified file path or name with the '.yaml' extension added.
    """
    yaml_extention1 = ".yaml"
    yaml_extention2 = ".yml"
    if not path.endswith(yaml_extention1) and not path.endswith(yaml_extention2):
        path += yaml_extention1
    return path


def get_default_yaml_paths_from_dict(default_yaml: dict) -> List[str]:
    """
    Process a nested dictionary of default YAML file paths, flattening the
    dictionary, converting it to a list of paths, and ensuring each path has
    a '.yaml' extension.

    Args:
        default_yaml (dict): A nested dictionary containing default YAML file paths.

    Returns:
        List[str]: A list of processed and validated default YAML file paths.
    """
    default_yaml = dict_to_path(default_yaml)
    default_yaml = [add_yaml_extension(filename) for filename in default_yaml]
    return default_yaml


def get_default_args_from_dict(config_path: str, default_yaml: dict) -> dict:
    """
    Load a YAML default configuration files in dict format and returns a dictionary of args.

    Args:
        config_path (str): The file path to the YAML configuration file.
        default_yml (dict): A dictionary data structure representing the paths to many
            YAML configuration files.

    Returns:
        dict: The updated configuration dictionary."""
    yaml_paths = get_default_yaml_paths_from_dict(default_yaml)
    default_configs = [
        open_yaml(os.path.join(config_path, yaml_path)) for yaml_path in yaml_paths
    ]
    default_config = {
        key: value
        for config_dict in default_configs
        if config_dict
        for key, value in config_dict.items()
    }
    return default_config


def get_default_args_from_path(config_path: str, default_yaml: str) -> dict:
    """
    Load a YAML default configuration files and returns a dictionary of args.

    Args:
        config_path (str): The file path to the YAML base configuration file.
        default_yml (str): The relative path to to the default YAML subconfiguration file.

    Returns:
        dict: The updated configuration dictionary.
    """
    default_yaml = add_yaml_extension(default_yaml)
    default_config_path = os.path.join(config_path, default_yaml)
    default_config = open_yaml(default_config_path)
    return default_config


def load_yaml_config(
    config_path: str, config_name: str, default_keyword: str = BASE_DEFAULT_KEYWORD, collection_keyword: str = BASE_COLLECTION_KEYWORD
) -> dict:
    """
    Load a YAML configuration file and update it with default configurations.

    Args:
        config_path (str): The file path to the YAML configuration file.
        config_name (str): The name of the YAML configuration file.
        default_keyword (str): The keyword used to identify default configurations
            in the YAML file. Defaults to "defaults".

    Returns:
        dict: The updated configuration dictionary.
    """
    path = os.path.join(config_path, config_name)
    config = open_yaml(path)

    if default_keyword in config:
        default_path_dict = config[default_keyword]
        if isinstance(default_path_dict, dict):
            default_config = get_default_args_from_dict(config_path, default_path_dict)

            if default_config:
                config.update(
                    (key, value)
                    for key, value in default_config.items()
                    if key not in config
                )
        else:
            for default_yaml in default_path_dict:
                if isinstance(default_yaml, dict):
                    default_config = get_default_args_from_dict(
                        config_path, default_yaml
                    )

                elif isinstance(default_yaml, str):
                    default_config = get_default_args_from_path(
                        config_path, default_yaml
                    )

                if default_config:
                    config.update(
                        (key, value)
                        for key, value in default_config.items()
                        if key not in config
                    )
        del config[default_keyword]

    if collection_keyword in config:
        unpack_collection(config, config_path, collection_keyword)

    
    return config

def unpack_collection(config, config_path, collection_keyword):
        collections_dict = config[collection_keyword]
        
        for collection_key in collections_dict.keys():
            if collection_key in config:
                return ValueError("You cannot have a collection with the same name as an argument.")

            collection_entry = collections_dict[collection_key]

            if isinstance(collection_entry, dict):
                # The collection entry contains multiple sub-entries, add all of them to the sub-config
                config[collection_key] = {}
                for subconfig_key in collection_entry.keys():
                    subconfig = get_default_args_from_path(config_path, collection_entry[subconfig_key])
                    config[collection_key].update({subconfig_key : subconfig})
            else:
                # The collection entry is a single entry, add it to the config
                subconfig = get_default_args_from_path(config_path, collection_entry)
                config[collection_key] = subconfig

        del config[collection_keyword]


def add_args_from_dict(
    arg_parser: argparse.ArgumentParser, config_dict: dict, prefix=""
) -> None:
    """
    Add arguments to an ArgumentParser instance using key-value pairs from a
    configuration dictionary. If the dictionary contains a nested dictionary, the
    argument will be added as --key.key value.
    Args:
        arg_parser (argparse.ArgumentParser): The ArgumentParser instance to which
                                              arguments will be added.
        config (dict): A dictionary containing key-value pairs representing
                       the arguments and their default values.
        prefix (str, optional): The prefix string for nested keys. Defaults to ''.
    """
    for key, value in config_dict.items():
        if isinstance(value, dict):
            add_args_from_dict(arg_parser, value, f"{prefix}{key}.")
        else:
            if key.startswith("$"):
                if key[1:] in os.environ:
                    value = os.environ[key[1:]]
                arg_parser.add_argument(
                    f"--{prefix}{key[1:]}", default=value, type=type(value)
                )
            elif key.startswith("?"):
                arg_parser.add_argument(
                    f"--{prefix}{key[1:]}", default=value, action='store_true'
                )
            else:
                arg_parser.add_argument(
                    f"--{prefix}{key}", default=value, type=type(value)
                )


def get_command_line_config(arg_parser: argparse.ArgumentParser, config_argument_keyword: str="config") -> Tuple[str, List[str]]:
    """
    Check to see if the user specified an alternative config via the command line. If so,
    return the path of that config, and the remaining arguments. Otherwise, return None
    and the remaining arguments.

    Args:
        arg_parser (argparse.ArgumentParser): The argparse object to add the config arg to.
        config_argument_keyword (str): Default keyword to accept new config path from the 
            command line.
    
    Returns:
        str: A string of the path to the alternate config.
        List[str]: All remaining arguments.
    """
    arg_parser.add_argument(f"--{config_argument_keyword}", default=None, type=str)
    known_args, unknown_args = arg_parser.parse_known_args()
    config_path = vars(known_args)[config_argument_keyword]
    return config_path, unknown_args


def config_to_nested_config(config: Config) -> Config:
    """
    Convert an Config object with 'key1.keyn' formatted keys into a nested Config object.

    Args:
        config (Config): The Config object to be converted.

    Returns:
        Config: A nested Config representation of the input Config object.
    """
    nested_dict = {}
    for key, value in vars(config).items():
        keys = key.split(".")
        current_dict = nested_dict
        for sub_key in keys[:-1]:
            if sub_key not in current_dict:
                current_dict[sub_key] = {}
            current_dict = current_dict[sub_key]
        current_dict[keys[-1]] = value

    return Config(nested_dict)
