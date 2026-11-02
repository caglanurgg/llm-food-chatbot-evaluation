import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.chatbot_client import send_message


def call_api(prompt, options, context):
    try:
        result = send_message(prompt)

        return {
            "output": result
        }

    except Exception as e:
        return {
            "error": f"Gradio Client hatasi: {str(e)}"
        }