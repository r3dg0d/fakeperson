import json
from pathlib import Path

import pytest

from fakeperson import identity as idmod
from fakeperson.safeguards import identity_name_ok


def test_create_list_load(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    assert identity_name_ok("alice").allowed
    ident = idmod.create_identity(
        "alice",
        seed=12345,
        style="passport",
        attributes={"hairstyle": "black pixie", "age": "28"},
    )
    assert ident.seed == 12345
    assert ident.path().is_file()

    loaded = idmod.load_identity("alice")
    assert loaded.attributes["hairstyle"] == "black pixie"
    assert loaded.style_lock == "passport"

    listed = idmod.list_identities()
    assert [i.name for i in listed] == ["alice"]

    with pytest.raises(FileExistsError):
        idmod.create_identity("alice")

    raw = json.loads(ident.path().read_text())
    assert raw["seed"] == 12345


def test_reject_bad_name(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    with pytest.raises(ValueError):
        idmod.create_identity("bad name!")
