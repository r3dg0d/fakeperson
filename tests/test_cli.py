from click.testing import CliRunner

from fakeperson.cli import main


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "fakeperson" in result.output.lower() or "fictional" in result.output.lower()


def test_generate_help():
    runner = CliRunner()
    result = runner.invoke(main, ["generate", "--help"])
    assert result.exit_code == 0
    assert "--count" in result.output
    assert "--seed" in result.output
    assert "--style" in result.output


def test_identity_and_models_help():
    runner = CliRunner()
    assert runner.invoke(main, ["identity", "--help"]).exit_code == 0
    assert runner.invoke(main, ["models", "list"]).exit_code == 0


def test_generate_stub(tmp_path):
    runner = CliRunner()
    out = tmp_path / "out"
    result = runner.invoke(
        main,
        [
            "generate",
            "--backend",
            "stub",
            "--count",
            "2",
            "--seed",
            "99",
            "--style",
            "selfie",
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    files = list(out.glob("*.png"))
    assert len(files) == 2


def test_identity_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    runner = CliRunner()
    r = runner.invoke(
        main,
        [
            "identity",
            "create",
            "--name",
            "bob",
            "--seed",
            "7",
            "--style",
            "candid",
            "--attr",
            "hairstyle=curly red",
        ],
    )
    assert r.exit_code == 0, r.output
    r2 = runner.invoke(main, ["identity", "list"])
    assert "bob" in r2.output
    out = tmp_path / "bob.png"
    r3 = runner.invoke(
        main,
        [
            "identity",
            "render",
            "bob",
            "--backend",
            "stub",
            "--prompt",
            "sitting in a cafe",
            "-o",
            str(out),
        ],
    )
    assert r3.exit_code == 0, r3.output
    assert out.exists() or out.with_suffix(".png").exists()
