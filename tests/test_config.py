from pathlib import Path

import pytest

from ggit.config import Config, default_config_path, load_config


def test_missing_file_returns_defaults(tmp_path: Path):
    config = load_config(tmp_path / "nope.toml")
    assert config == Config()
    assert config.paths == []
    assert config.github_prs is True


def test_load_full_config(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('paths = ["~/code", "/srv/repos"]\ngithub_prs = false\n')
    config = load_config(config_file)
    assert config.paths == [str(Path("~/code").expanduser()), "/srv/repos"]
    assert config.github_prs is False


def test_load_partial_config(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('paths = ["/srv/repos"]\n')
    config = load_config(config_file)
    assert config.paths == ["/srv/repos"]
    assert config.github_prs is True


def test_invalid_toml_raises(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("paths = [broken\n")
    with pytest.raises(ValueError, match="Invalid config file"):
        load_config(config_file)


def test_invalid_paths_type_raises(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('paths = "~/code"\n')
    with pytest.raises(ValueError, match="'paths' must be a list of strings"):
        load_config(config_file)


def test_invalid_github_prs_type_raises(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('github_prs = "yes"\n')
    with pytest.raises(ValueError, match="'github_prs' must be a boolean"):
        load_config(config_file)


def test_default_config_path_respects_xdg(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_config_path() == tmp_path / "ggit" / "config.toml"


def test_default_config_path_falls_back_to_home(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert default_config_path() == Path.home() / ".config" / "ggit" / "config.toml"
