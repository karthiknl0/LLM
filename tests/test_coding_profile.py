from app.coding_profile import CODING_AGENT_PROFILE


def test_profile_requires_evidence_and_verification():
    assert "Use tools instead of guessing" in CODING_AGENT_PROFILE
    assert "Run the most relevant tests" in CODING_AGENT_PROFILE
    assert "without evidence" in CODING_AGENT_PROFILE
    assert "not the hosted Codex model" in CODING_AGENT_PROFILE
