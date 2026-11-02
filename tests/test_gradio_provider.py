from unittest.mock import patch

from configs.gradio_provider import call_api


@patch("configs.gradio_provider.send_message")
def test_call_api_returns_chatbot_response(mock_send_message):
    mock_send_message.return_value = "Mercimek, soğan ve havuç."

    result = call_api(
        prompt="Mercimek çorbası için hangi malzemeler gerekir?",
        options={},
        context={}
    )

    assert result == {
        "output": "Mercimek, soğan ve havuç."
    }

    mock_send_message.assert_called_once_with(
        "Mercimek çorbası için hangi malzemeler gerekir?"
    )


@patch("configs.gradio_provider.send_message")
def test_call_api_returns_error_when_request_fails(mock_send_message):
    mock_send_message.side_effect = RuntimeError("Connection failed")

    result = call_api(
        prompt="Mercimek çorbası tarifi ver.",
        options={},
        context={}
    )

    assert "error" in result
    assert "Connection failed" in result["error"]