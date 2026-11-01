import pytest
from unittest.mock import patch

from app.chatbot_client import send_message


@patch("app.chatbot_client.Client")
def test_send_message_returns_chatbot_response(mock_client):
    mock_instance = mock_client.return_value
    mock_instance.predict.return_value = "Mercimek, soğan ve havuç."

    response = send_message("Mercimek çorbası için hangi malzemeler gerekir?")

    assert response == "Mercimek, soğan ve havuç."

    mock_client.assert_called_once_with(
        "cagla1989/Yemek_Botu_QA_Final"
    )

    mock_instance.predict.assert_called_once_with(
        user_input="Mercimek çorbası için hangi malzemeler gerekir?",
        api_name="/yemek_botu"
    )


@patch("app.chatbot_client.Client")
def test_send_message_raises_runtime_error_when_api_fails(mock_client):
    mock_instance = mock_client.return_value
    mock_instance.predict.side_effect = Exception("Connection failed")

    with pytest.raises(RuntimeError, match="Chatbot API request failed"):
        send_message("Mercimek çorbası tarifi ver.")