"""YAML file handling utilities for slide project persistence.

This module provides functions to read and write outline.yml files with
proper datetime serialization and deserialization.
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


def datetime_representer(dumper: yaml.Dumper, data: datetime) -> yaml.Node:
    """Custom YAML representer for datetime objects.

    Args:
        dumper: YAML dumper instance
        data: datetime object to represent

    Returns:
        YAML scalar node with ISO format datetime string
    """
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', data.isoformat())


def datetime_constructor(loader: yaml.Loader, node: yaml.Node) -> datetime:
    """Custom YAML constructor for datetime objects.

    Args:
        loader: YAML loader instance
        node: YAML node to construct from

    Returns:
        Parsed datetime object
    """
    value = loader.construct_scalar(node)
    return datetime.fromisoformat(value)


# Register custom datetime handlers
yaml.add_representer(datetime, datetime_representer)
yaml.add_constructor('tag:yaml.org,2002:timestamp', datetime_constructor)


def read_yaml(file_path: Path) -> Dict[str, Any]:
    """Read and parse a YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Parsed YAML content as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file contains invalid YAML
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_yaml(file_path: Path, data: Dict[str, Any]) -> None:
    """Write data to a YAML file with proper formatting.

    Args:
        file_path: Path to the YAML file
        data: Dictionary to serialize to YAML

    Raises:
        IOError: If the file cannot be written
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2
        )
