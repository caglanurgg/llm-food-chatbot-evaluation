import json
from gradio_client import Client

def call_api(prompt, options, context):
    try:
        # Doğrudan senin API dökümantasyonundaki resmi kontratı çalıştırıyoruz
        client = Client("cagla1989/Yemek_Botu_QA_Final")
        result = client.predict(
            user_input=prompt,
            api_name="/yemek_botu"
        )
        # Promptfoo'nun anlayacağı ham metin formatında cevabı dönüyoruz
        return {
            "output": result
        }
    except Exception as e:
        return {
            "error": f"Gradio Client hatasi: {str(e)}"
        }