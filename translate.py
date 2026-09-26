"""Tradução do texto extraído pelo OCR (chamada só de texto, sem imagem)."""

import os

from openai import OpenAI

DEFAULT_MODEL = os.getenv("TRANSLATE_MODEL", os.getenv("OCR_MODEL", "gpt-5-nano"))
# minimal é o mais barato; se a tradução vier resumida ou pulando trechos, tente "low".
REASONING_EFFORT = os.getenv("TRANSLATE_REASONING", "minimal")

INSTRUCTIONS = (
    "Você é um tradutor profissional. Traduza o texto do usuário para {language}. "
    "Traduza TUDO, frase por frase: não resuma, não omita e não acrescente nada. "
    "Mantenha a ordem e as quebras de linha do original. Nomes próprios ficam como estão. "
    "Se o texto já estiver em {language}, devolva-o sem alterações. "
    "Devolva apenas a tradução, sem comentários, sem markdown e sem aspas."
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # lê OPENAI_API_KEY do ambiente
    return _client


def translate(text: str, language: str, model: str = DEFAULT_MODEL) -> str:
    response = _get_client().responses.create(
        model=model,
        instructions=INSTRUCTIONS.format(language=language),
        reasoning={"effort": REASONING_EFFORT},
        input=text,
    )
    return response.output_text.strip()


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    load_dotenv()
    print(translate(" ".join(sys.argv[1:]) or "Hola, ¿cómo estás?", "português do Brasil"))
