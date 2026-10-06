from app.ai.llm.openai_compat import OpenAICompatProvider


def test_deepseek_payload_disables_thinking_for_short_structured_calls() -> None:
    provider = OpenAICompatProvider(
        base_url="https://api.deepseek.com/v1",
        api_key="test-key",
        model="deepseek-flash",
    )

    payload = provider._payload(
        [{"role": "user", "content": "output json"}],
        stream=False,
        max_tokens=200,
        json_mode=True,
    )

    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}


def test_non_deepseek_payload_does_not_send_vendor_specific_thinking_flag() -> None:
    provider = OpenAICompatProvider(
        base_url="https://example-llm.invalid/v1",
        api_key="test-key",
        model="example-model",
    )

    payload = provider._payload(
        [{"role": "user", "content": "hello"}],
        stream=False,
        max_tokens=200,
    )

    assert "thinking" not in payload
