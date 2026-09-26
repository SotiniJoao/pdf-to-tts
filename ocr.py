"""Agente de OCR: manda uma imagem PNG para um modelo GPT e devolve o texto extraído."""

import base64
import os

from openai import OpenAI

# gpt-5-nano é o modelo mais barato da OpenAI que aceita imagem ($0.05 / $0.40 por 1M tokens).
DEFAULT_MODEL = os.getenv("OCR_MODEL", "gpt-5-nano")

INSTRUCTIONS = (
    "Você é um motor de OCR. Extraia TODO o texto legível da imagem, na ordem natural de leitura "
    "(de cima para baixo, da esquerda para a direita). Devolva apenas o texto extraído, sem "
    "comentários, sem markdown e sem descrever a imagem. Ignore ícones e elementos sem texto. "
    "Se não houver texto, devolva uma string vazia."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # lê OPENAI_API_KEY do ambiente
    return _client


def extract_text(png_bytes: bytes, model: str = DEFAULT_MODEL) -> str:
    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    response = _get_client().responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        reasoning={"effort": "minimal"},
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Extraia todo o texto dessa captura que não esteja nas bordas da imagem. Se não houver texto, devolva uma string vazia."},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }
        ],
    )
    return response.output_text.strip()


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    load_dotenv()
    with open(sys.argv[1], "rb") as f:
        print(extract_text(f.read()))
