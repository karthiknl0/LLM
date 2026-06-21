from app.local_code.instructions import collect_project_instructions, format_instructions
from app.local_code import cli


def test_collect_project_instructions_orders_parent_first(tmp_path):
    parent = tmp_path / "repo"
    child = parent / "src"
    child.mkdir(parents=True)
    (parent / "CLAUDE.md").write_text("parent rules", encoding="utf-8")
    (child / "AGENTS.md").write_text("child rules", encoding="utf-8")

    files = collect_project_instructions(child)

    assert [item.content for item in files] == ["parent rules", "child rules"]


def test_format_instructions_includes_paths():
    files = [
        type("Instruction", (), {"path": "CLAUDE.md", "content": "Be careful."})(),
    ]

    text = format_instructions(files)

    assert "Project instructions" in text
    assert "CLAUDE.md" in text
    assert "Be careful." in text


def test_local_code_parser_accepts_commands():
    parser = cli.build_parser()

    assert parser.parse_args(["ask", "hello"]).command == "ask"
    assert parser.parse_args(["chat"]).command == "chat"
    assert parser.parse_args(["init", "--force"]).force is True
    assert parser.parse_args(["instructions"]).command == "instructions"
