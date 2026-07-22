"""User configuration for ggit.

Read from ``$XDG_CONFIG_HOME/ggit/config.toml`` (defaults to
``~/.config/ggit/config.toml``). All keys are optional:

.. code-block:: toml

    # Directories scanned when no path argument is given (default: ".")
    paths = ["~/code"]

    # Look up open PR counts via the gh CLI (default: true)
    github_prs = true
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib


@dataclass
class Config:
    paths: list = field(default_factory=list)
    github_prs: bool = True


def default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ggit" / "config.toml"


def load_config(path: Optional[Path] = None) -> Config:
    """Load the config file, returning defaults if it does not exist.

    Raises ValueError if the file exists but cannot be parsed or has
    invalid values, so the user learns about a broken config instead of
    silently getting defaults.
    """
    config_path = path or default_config_path()
    if not config_path.exists():
        return Config()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid config file {config_path}: {e}") from e

    paths = data.get("paths", [])
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise ValueError(f"Invalid config file {config_path}: 'paths' must be a list of strings")

    github_prs = data.get("github_prs", True)
    if not isinstance(github_prs, bool):
        raise ValueError(f"Invalid config file {config_path}: 'github_prs' must be a boolean")

    return Config(
        paths=[str(Path(p).expanduser()) for p in paths],
        github_prs=github_prs,
    )
