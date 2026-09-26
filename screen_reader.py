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


def _describe_hotkey(hotkey: str) -> str:
    """'<ctrl>+<alt>+r' -> 'Ctrl+Alt+R' (no Mac: 'Control+Option+R')."""
    names = {"<ctrl>": "Ctrl", "<alt>": "Alt", "<shift>": "Shift", "<cmd>": "Win"}
    if sys.platform == "darwin":
        names.update({"<ctrl>": "Control", "<alt>": "Option", "<cmd>": "Cmd"})
    return "+".join(names.get(part, part.upper()) for part in hotkey.split("+"))

DEBUG_TEXTS_DIR = os.getenv("DEBUG_TEXTS_DIR", "")  # se definido, salva cada texto extraído nessa pasta


def _save_debug_text(text: str) -> Path:
    folder = Path(DEBUG_TEXTS_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"debug_text_{hex(random.randint(0, 16**8))}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def read_screen() -> None:
    if not _busy.acquire(blocking=False):
        print("Ainda processando a leitura anterior, ignorando.")
        return
    try:
        print("Atalho recebido. Capturando a janela...")
        png = capture.capture()
        print("Extraindo o texto...")
        text = ocr.extract_text(png)
        if not text:
            print("Nenhum texto encontrado.")
            return
        print(f"--- Texto extraído ---\n{text}\n----------------------")
        if DEBUG_TEXTS_DIR:
            print(f"Texto salvo em: {_save_debug_text(text).resolve()}")
        print("Falando...")
        tts.speak(text)
        print("Pronto. Aguardando o atalho.")
    except Exception as e:
        print(f"Erro: {type(e).__name__}: {e}")
    finally:
        _busy.release()


def _open_macos_settings(pane: str) -> None:
    import subprocess

    subprocess.run(["open", f"x-apple.systempreferences:com.apple.preference.security?{pane}"], check=False)


def check_macos_permissions() -> None:
    """Avisa (e abre a tela certa dos Ajustes) quando falta permissão para o Terminal."""
    import HIServices
    import Quartz

    missing = False
    if not Quartz.CGPreflightScreenCaptureAccess():
        missing = True
        print("FALTA PERMISSÃO: Gravação de Tela. Sem ela o print sai só com o papel de parede.")
        Quartz.CGRequestScreenCaptureAccess()  # faz o Terminal aparecer na lista
        _open_macos_settings("Privacy_ScreenCapture")
    if not HIServices.AXIsProcessTrusted():
        missing = True
        print("FALTA PERMISSÃO: Acessibilidade. Sem ela o atalho de teclado não funciona.")
        _open_macos_settings("Privacy_Accessibility")
    if missing:
        print("Ative o Terminal nas telas que abriram, feche o Terminal (Cmd+Q) e abra de novo.")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Defina OPENAI_API_KEY no arquivo .env (veja .env.example).")

    listener: keyboard.GlobalHotKeys

    def on_read() -> None:
        # Roda fora da thread do listener para não travar o teclado.
        threading.Thread(target=read_screen, daemon=True).start()

    def on_quit() -> None:
        print("Encerrando.")
        listener.stop()

    if sys.platform == "darwin":
        check_macos_permissions()

    listener = keyboard.GlobalHotKeys({READ_HOTKEY: on_read, QUIT_HOTKEY: on_quit})
    print(f"Pronto. {_describe_hotkey(READ_HOTKEY)} lê a janela em foco, {_describe_hotkey(QUIT_HOTKEY)} encerra.")
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()
