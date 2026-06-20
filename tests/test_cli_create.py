from argparse import Namespace
from types import SimpleNamespace

from app import cli


def test_core_parser_includes_create_command():
    parser = cli.build_parser()

    args = parser.parse_args(["create", "-f", "LocalModel.yaml", "--force", "--activate"])

    assert args.func is cli.cmd_create
    assert args.file == "LocalModel.yaml"
    assert args.force is True
    assert args.activate is True


def test_cmd_create_installs_and_optionally_activates(monkeypatch, capsys):
    package = SimpleNamespace(
        name="demo",
        base="qwen3.5:4b",
        path="data/models/demo/LocalModel.yaml",
    )
    calls = {}

    def fake_install(path, *, overwrite=False):
        calls["path"] = path
        calls["overwrite"] = overwrite
        return package

    def fake_set_model(name):
        calls["activated"] = name
        return f"Active model/package set to: {name}\n"

    monkeypatch.setattr(cli, "install_package_file", fake_install)
    monkeypatch.setattr(cli, "set_model", fake_set_model)

    code = cli.cmd_create(Namespace(file="LocalModel.yaml", force=True, activate=True))

    output = capsys.readouterr().out
    assert code == 0
    assert calls == {
        "path": "LocalModel.yaml",
        "overwrite": True,
        "activated": "demo",
    }
    assert "Created LocalModel package" in output
    assert "Name: demo" in output
    assert "Base: qwen3.5:4b" in output
    assert "Path: data/models/demo/LocalModel.yaml" in output
