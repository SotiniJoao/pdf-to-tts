"""TTS com edge-tts + player de MP3 com pausa/parar, sem dependências extras
(winmm no Windows, afplay no macOS)."""

import asyncio
import ctypes
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

import edge_tts

DEFAULT_VOICE = os.getenv("TTS_VOICE", "es-ES-ElviraNeural")
DEFAULT_RATE = os.getenv("TTS_RATE", "+0%")


async def _save(text: str, path: str, voice: str, rate: str) -> None:
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


def synthesize(text: str, path: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
    asyncio.run(_save(text, path, voice, rate))


def _mci(command: str) -> str:
    buf = ctypes.create_unicode_buffer(256)
    err = ctypes.windll.winmm.mciSendStringW(command, buf, len(buf), None)
    if err:
        raise RuntimeError(f"MCI erro {err} em: {command}")
    return buf.value


class Player:
    """Toca um MP3 por vez numa thread própria; pode pausar/continuar e parar a qualquer momento."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._pause = threading.Event()

    @property
    def playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def paused(self) -> bool:
        return self.playing and self._pause.is_set()

    def play(self, path: str) -> None:
        """Para o que estiver tocando e começa o arquivo novo (não bloqueia)."""
        with self._lock:
            self._stop_locked()
            self._stop = threading.Event()
            self._pause = threading.Event()
            self._thread = threading.Thread(
                target=self._run, args=(os.path.abspath(path), self._stop, self._pause), daemon=True
            )
            self._thread.start()

    def toggle_pause(self) -> None:
        if not self.playing:
            return
        if self._pause.is_set():
            self._pause.clear()
        else:
            self._pause.set()

    def stop(self) -> None:
        with self._lock:
            self._stop_locked()

    def wait(self) -> None:
        if self._thread is not None:
            self._thread.join()

    def _stop_locked(self) -> None:
        if self.playing:
            self._stop.set()
            self._thread.join()

    # Os comandos de cada reprodução ficam todos na thread dela: o MCI do Windows não gosta de
    # um alias aberto numa thread e controlado por outra.
    def _run(self, path: str, stop: threading.Event, pause: threading.Event) -> None:
        if sys.platform == "darwin":
            self._run_afplay(path, stop, pause)
        else:
            self._run_mci(path, stop, pause)

    @staticmethod
    def _run_afplay(path: str, stop: threading.Event, pause: threading.Event) -> None:
        proc = subprocess.Popen(["afplay", path])
        paused = False
        try:
            while proc.poll() is None and not stop.is_set():
                if pause.is_set() != paused:
                    paused = pause.is_set()
                    proc.send_signal(signal.SIGSTOP if paused else signal.SIGCONT)
                time.sleep(0.05)
        finally:
            if proc.poll() is None:
                proc.kill()  # SIGKILL funciona mesmo com o processo pausado (SIGSTOP)
                proc.wait()

    @staticmethod
    def _run_mci(path: str, stop: threading.Event, pause: threading.Event) -> None:
        alias = f"tts_{threading.get_ident()}"
        _mci(f'open "{path}" type mpegvideo alias {alias}')
        try:
            _mci(f"play {alias}")
            paused = False
            while not stop.is_set():
                if pause.is_set() != paused:
                    paused = pause.is_set()
                    _mci(f"{'pause' if paused else 'resume'} {alias}")
                if not paused and _mci(f"status {alias} mode") == "stopped":
                    break
                time.sleep(0.05)
        finally:
            _mci(f"close {alias}")


def speak(text: str, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
    """Fala o texto e bloqueia até terminar."""
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        synthesize(text, path, voice, rate)
        player = Player()
        player.play(path)
        player.wait()
    finally:
        os.remove(path)


if __name__ == "__main__":
    speak("Hola, esta es una prueba del módulo de voz.")
