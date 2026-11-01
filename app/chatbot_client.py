from gradio_client import Client

CHATBOT_ID = "cagla1989/Yemek_Botu_QA_Final"


def send_message(prompt: str) -> str:
    """
    Sends a prompt to the Gradio chatbot and returns its response.
    """
    try:
        client = Client(CHATBOT_ID)

        response = client.predict(
            user_input=prompt,
            api_name="/yemek_botu"
        )

        return response

    except Exception as e:
        raise RuntimeError(
            f"Chatbot API request failed: {e}"
        ) from e