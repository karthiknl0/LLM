from app.content.coding_profile import CODING_AGENT_PROFILE


def test_profile_requires_evidence_and_verification():
    assert "Don't guess where code lives" in CODING_AGENT_PROFILE
    assert "actually run it" in CODING_AGENT_PROFILE
    assert "use edit_file" in CODING_AGENT_PROFILE
    assert "write_file for new/small" in CODING_AGENT_PROFILE
    assert "do not ask again" in CODING_AGENT_PROFILE
    assert "Never claim a file changed" in CODING_AGENT_PROFILE
    assert "hosted Codex" in CODING_AGENT_PROFILE
