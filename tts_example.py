"""Exemplo simples de text-to-speech com edge-tts.

Uso:
    python tts_example.py                          # usa o texto padrão
    python tts_example.py "Seu texto aqui"         # texto customizado
    python tts_example.py "Texto" -v pt-BR-AntonioNeural -o saida.mp3
    python tts_example.py --list-voices            # lista vozes pt-BR
"""

import argparse
import asyncio

import edge_tts

DEFAULT_TEXT = (
    "Olá! Este é um teste de conversão de texto em fala usando o edge-tts. "
    "Se você está ouvindo isso, está tudo funcionando."
)
DEFAULT_VOICE = "pt-BR-FranciscaNeural"


async def list_voices(locale: str = "pt-BR") -> None:
    voices = await edge_tts.list_voices()
    for v in voices:
        if v["Locale"].startswith(locale):
            print(f'{v["ShortName"]:30} {v["Gender"]}')


async def synthesize(text: str, voice: str, output: str, rate: str, volume: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output)
    print(f"Áudio salvo em: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Teste de TTS com edge-tts")
    parser.add_argument("text", nargs="?", default=DEFAULT_TEXT, help="Texto a ser falado")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, help="Voz (ex: pt-BR-AntonioNeural)")
    parser.add_argument("-o", "--output", default="output.mp3", help="Arquivo de saída .mp3")
    parser.add_argument("-r", "--rate", default="+0%", help="Velocidade (ex: +20%%, -10%%)")
    parser.add_argument("--volume", default="+0%", help="Volume (ex: +10%%)")
    parser.add_argument("--list-voices", action="store_true", help="Lista as vozes pt-BR e sai")
    args = parser.parse_args()

    if args.list_voices:
        asyncio.run(list_voices())
    else:
        asyncio.run(synthesize(args.text, args.voice, args.output, args.rate, args.volume))


if __name__ == "__main__":
    main()
