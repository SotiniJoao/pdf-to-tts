"""Leitor de tela: atalho de teclado -> print (mss) -> OCR (GPT) -> fala (edge-tts).

Uso:
    python screen_reader.py

Atalhos (configuráveis no .env; no Mac, Alt = Option):
    Ctrl+Alt+R  captura a janela em foco, salva e lê o texto em voz alta
    Ctrl+Alt+P  pausa / continua a narração
    Ctrl+Alt+S  para a narração
    Ctrl+Alt+L  repete a última narração
    Ctrl+Alt+T  alterna a língua da narração: espanhol / português
    Ctrl+Alt+Q  encerra

Em cada modo o texto é traduzido para a língua escolhida (se já estiver nela, volta igual).
Cada leitura fica salva numerada na pasta de narrações: 1.txt (texto original do OCR),
1.es.txt ou 1.pt.txt (texto narrado) e 1.mp3; depois 2.*, 3.*, ...
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
import translate  # noqa: E402
import tts  # noqa: E402

READ_HOTKEY = os.getenv("READ_HOTKEY", "<ctrl>+<alt>+r")
PAUSE_HOTKEY = os.getenv("PAUSE_HOTKEY", "<ctrl>+<alt>+p")
STOP_HOTKEY = os.getenv("STOP_HOTKEY", "<ctrl>+<alt>+s")
REPLAY_HOTKEY = os.getenv("REPLAY_HOTKEY", "<ctrl>+<alt>+l")
LANGUAGE_HOTKEY = os.getenv("LANGUAGE_HOTKEY", "<ctrl>+<alt>+t")
QUIT_HOTKEY = os.getenv("QUIT_HOTKEY", "<ctrl>+<alt>+q")

# Pasta relativa ao projeto, não à pasta de onde foi aberto.
OUTPUT_DIR = APP_DIR / os.getenv("OUTPUT_DIR", "narracoes")
AUTO_PLAY = os.getenv("AUTO_PLAY", "true").lower() not in ("0", "false", "nao", "não", "no")

# Modos de língua: o texto do OCR é sempre traduzido para "translate_to" antes de narrar.
LANGUAGES = {
    "es": {
        "label": "espanhol",
        "voice": os.getenv("TTS_VOICE_ES", "es-ES-ElviraNeural"),
        "translate_to": "espanhol",
    },
    "pt": {
        "label": "português",
        "voice": os.getenv("TTS_VOICE_PT", "pt-BR-FranciscaNeural"),
        "translate_to": "português do Brasil",
    },
}
language = os.getenv("LANGUAGE", "es")
if language not in LANGUAGES:
    print(f"LANGUAGE={language!r} inválido no .env, usando 'es'. Opções: {', '.join(LANGUAGES)}")
    language = "es"

_busy = threading.Lock()
player = tts.Player()


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


def _numbered_outputs() -> list[Path]:
    return sorted(
        (p for p in OUTPUT_DIR.glob("*.mp3") if p.stem.isdigit()),
        key=lambda p: int(p.stem),
    )


def _save_output(original: str, spoken: str, lang: str) -> Path:
    """Salva N.txt (original), N.<língua>.txt (texto narrado) e N.mp3 com o próximo
    número livre e devolve o caminho do mp3."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = _numbered_outputs()
    n = int(existing[-1].stem) + 1 if existing else 1
    (OUTPUT_DIR / f"{n}.txt").write_text(original, encoding="utf-8")
    (OUTPUT_DIR / f"{n}.{lang}.txt").write_text(spoken, encoding="utf-8")
    mp3 = OUTPUT_DIR / f"{n}.mp3"
    partial = OUTPUT_DIR / f"{n}.mp3.part"  # não deixa mp3 pela metade se a síntese falhar
    tts.synthesize(spoken, str(partial), voice=LANGUAGES[lang]["voice"])
    partial.replace(mp3)
    return mp3


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
        lang = language  # lê uma vez: o atalho pode trocar a língua no meio
        target = LANGUAGES[lang]["translate_to"]
        print(f"Traduzindo para {target}...")
        spoken = translate.translate(text, target)
        print(f"--- Texto em {target} ---\n{spoken}\n----------------")
        print("Gerando a narração...")
        mp3 = _save_output(text, spoken, lang)
        print(f"Salvo: {mp3.stem}.txt, {mp3.stem}.{lang}.txt e {mp3.name} em {OUTPUT_DIR}")
        if AUTO_PLAY:
            player.play(str(mp3))
            print(f"Narrando {mp3.name}. {_describe_hotkey(PAUSE_HOTKEY)} pausa, {_describe_hotkey(STOP_HOTKEY)} para.")
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

    def on_pause() -> None:
        if not player.playing:
            print("Nada tocando.")
            return
        player.toggle_pause()
        print("Pausado." if player.paused else "Continuando.")

    def on_stop() -> None:
        if player.playing:
            player.stop()
            print("Narração parada.")

    def on_replay() -> None:
        outputs = _numbered_outputs()
        if not outputs:
            print("Nenhuma narração salva ainda.")
            return
        player.play(str(outputs[-1]))
        print(f"Repetindo {outputs[-1].name}.")

    def on_language() -> None:
        global language
        keys = list(LANGUAGES)
        language = keys[(keys.index(language) + 1) % len(keys)]
        print(f"Língua: {LANGUAGES[language]['label']}")

    def on_quit() -> None:
        print("Encerrando.")
        player.stop()
        listener.stop()

    if sys.platform == "darwin":
        check_macos_permissions()

    listener = keyboard.GlobalHotKeys(
        {
            READ_HOTKEY: on_read,
            PAUSE_HOTKEY: on_pause,
            STOP_HOTKEY: on_stop,
            REPLAY_HOTKEY: on_replay,
            LANGUAGE_HOTKEY: on_language,
            QUIT_HOTKEY: on_quit,
        }
    )
    print("Pronto. Atalhos:")
    print(f"  {_describe_hotkey(READ_HOTKEY):18} lê a janela em foco")
    print(f"  {_describe_hotkey(PAUSE_HOTKEY):18} pausa / continua")
    print(f"  {_describe_hotkey(STOP_HOTKEY):18} para")
    print(f"  {_describe_hotkey(REPLAY_HOTKEY):18} repete a última")
    print(f"  {_describe_hotkey(LANGUAGE_HOTKEY):18} troca a língua (espanhol / português)")
    print(f"  {_describe_hotkey(QUIT_HOTKEY):18} encerra")
    print(f"Língua: {LANGUAGES[language]['label']}")
    print(f"Narrações salvas em: {OUTPUT_DIR}" + ("" if AUTO_PLAY else " (narração automática desligada)"))
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()
