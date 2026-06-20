from app import cli


def test_cli_parser_accepts_core_commands():
    parser = cli.build_parser()

    assert parser.parse_args(["list"]).command == "list"
    assert parser.parse_args(["list", "--all"]).all is True
    assert parser.parse_args(["packages"]).command == "packages"
    assert parser.parse_args(["inspect", "qwen3.5:4b"]).model == "qwen3.5:4b"
    assert parser.parse_args(["api", "--port", "11435"]).port == 11435


def test_run_requires_prompt(capsys):
    result = cli.main(["run"])

    captured = capsys.readouterr()
    assert result == 2
    assert "Usage: local-ai run" in captured.err
