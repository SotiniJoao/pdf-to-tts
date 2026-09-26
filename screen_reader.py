"""Leitor de tela: atalho de teclado -> print (mss) -> OCR (GPT) -> fala (edge-tts).

Uso:
    python screen_reader.py

Atalhos (configuráveis no .env):
    Ctrl+Alt+R  captura a janela em foco e lê o texto em voz alta
    Ctrl+Alt+Q  encerra
"""

import os
import random
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from pynput import keyboard

# No .exe (PyInstaller) o .env fica ao lado do executável; rodando como .py, ao lado deste arquivo.
# O load_dotenv() sem caminho usaria a pasta atual no .exe, que muda se abrir por atalho.
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
load_dotenv(APP_DIR / ".env")

import capture  # noqa: E402  (precisa do .env carregado antes)
import ocr  # noqa: E402
import tts  # noqa: E402

READ_HOTKEY = os.getenv("READ_HOTKEY", "<ctrl>+<alt>+r")
QUIT_HOTKEY = os.getenv("QUIT_HOTKEY", "<ctrl>+<alt>+q")

_busy = threading.Lock()

DEBUG_TEXTS_DIR = os.getenv("DEBUG_TEXTS_DIR", False)
debug = True if DEBUG_TEXTS_DIR else False
def read_screen() -> None:
    if not _busy.acquire(blocking=False):
        if debug:
            print("Ainda processando a leitura anterior, ignorando.")
        return
    try:
        png = capture.capture()
        text = ocr.extract_text(png)
        if not text:
            if debug:
                print("Nenhum texto encontrado.")
            return
        if debug:
            open(f"{os.path.join(DEBUG_TEXTS_DIR, f'debug_text_{hex(random.randint(0, 16**8))}.txt')}", "w", encoding="utf-8").write(text)
            print(f"Texto extraído e salvo em arquivo de debug: {text}")
        tts.speak(text)
    except Exception as e:
        if debug:
            print(f"Erro: {e}")
    finally:
        _busy.release()


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Defina OPENAI_API_KEY no arquivo .env (veja .env.example).")

    listener: keyboard.GlobalHotKeys

    def on_read() -> None:
        # Roda fora da thread do listener para não travar o teclado.
        threading.Thread(target=read_screen, daemon=True).start()

    def on_quit() -> None:
        listener.stop()

    listener = keyboard.GlobalHotKeys({READ_HOTKEY: on_read, QUIT_HOTKEY: on_quit})
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()
