import pytest

from app.runtime.chat_templates import format_chat_messages


MESSAGES = [
    {"role": "system", "content": "Be useful."},
    {"role": "user", "content": "Hello"},
]


def test_chatml_template():
    text = format_chat_messages(MESSAGES, "chatml")

    assert "<|im_start|>system" in text
    assert text.endswith("<|im_start|>assistant\n")


def test_llama3_template():
    text = format_chat_messages(MESSAGES, "llama3")

    assert "<|begin_of_text|>" in text
    assert "<|start_header_id|>assistant" in text


def test_mistral_template():
    text = format_chat_messages(MESSAGES, "mistral")

    assert "[INST]" in text
    assert "Be useful." in text


def test_unknown_template_rejected():
    with pytest.raises(ValueError):
        format_chat_messages(MESSAGES, "unknown")
