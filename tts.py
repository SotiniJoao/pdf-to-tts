"""TTS com edge-tts + reprodução de MP3 sem dependências extras (winmm no Windows, afplay no macOS)."""

import asyncio
import ctypes
import os
import subprocess
import sys
import tempfile

import edge_tts

DEFAULT_VOICE = os.getenv("TTS_VOICE", "pt-BR-FranciscaNeural")
DEFAULT_RATE = os.getenv("TTS_RATE", "+0%")


async def _save(text: str, path: str, voice: str, rate: str) -> None:
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


def synthesize(text: str, path: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
    asyncio.run(_save(text, path, voice, rate))


def _mci(command: str) -> None:
    buf = ctypes.create_unicode_buffer(256)
    err = ctypes.windll.winmm.mciSendStringW(command, buf, len(buf), None)
    if err:
        raise RuntimeError(f"MCI erro {err} em: {command}")


def play_mp3(path: str) -> None:
    """Toca o MP3 e bloqueia até terminar."""
    if sys.platform == "darwin":
        subprocess.run(["afplay", path], check=True)
        return
    alias = "tts_audio"
    _mci(f'open "{path}" type mpegvideo alias {alias}')
    try:
        _mci(f"play {alias} wait")
    finally:
        _mci(f"close {alias}")


def speak(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        synthesize(text, path, voice, rate)
        play_mp3(path)
    finally:
        os.remove(path)


if __name__ == "__main__":
    speak("Teste de reprodução do módulo de fala.")
