"""Captura de tela com mss: monitor inteiro ou só a janela em foco (Windows e macOS)."""

import os
import sys
from datetime import datetime
from pathlib import Path

import mss
import mss.tools

CAPTURE_MODE = os.getenv("CAPTURE_MODE", "window")  # "window" = janela em foco, "monitor" = monitor inteiro
MONITOR = int(os.getenv("MONITOR", "1"))  # usado no modo "monitor": 1 = principal, 0 = todos juntos
DEBUG_DIR = os.getenv("DEBUG_CAPTURES_DIR", "")  # se definido, salva cada print nessa pasta
DEBUG_KEEP = int(os.getenv("DEBUG_CAPTURES_KEEP", "20"))  # quantos prints manter na pasta

_DWMWA_EXTENDED_FRAME_BOUNDS = 9


def _foreground_window_region_windows() -> dict:
    """Retângulo visível da janela em foco, sem as bordas invisíveis do Windows 10/11."""
    import ctypes
    import ctypes.wintypes

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    rect = ctypes.wintypes.RECT()
    hr = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd, _DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(rect), ctypes.sizeof(rect)
    )
    if hr != 0:
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return {
        "left": rect.left,
        "top": rect.top,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }


def _foreground_window_region_macos() -> dict | None:
    """Retângulo (em pontos, origem no canto superior esquerdo) da janela da frente do app ativo."""
    import Quartz
    from AppKit import NSWorkspace

    pid = NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    # A lista vem da frente para trás; layer 0 = janelas normais (sem menu bar, dock etc.).
    for w in windows:
        if w.get("kCGWindowOwnerPID") == pid and w.get("kCGWindowLayer") == 0:
            b = w["kCGWindowBounds"]
            return {"left": int(b["X"]), "top": int(b["Y"]), "width": int(b["Width"]), "height": int(b["Height"])}
    return None


def _foreground_window_region() -> dict | None:
    if sys.platform == "win32":
        return _foreground_window_region_windows()
    if sys.platform == "darwin":
        return _foreground_window_region_macos()
    return None


def _save_debug(png: bytes) -> Path:
    folder = Path(DEBUG_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"capture_{datetime.now():%Y%m%d_%H%M%S_%f}.png"
    path.write_bytes(png)
    for old in sorted(folder.glob("capture_*.png"))[:-DEBUG_KEEP]:
        old.unlink()
    return path


def capture() -> bytes:
    # No Windows o mss deixa o processo DPI-aware ao iniciar, então as coordenadas da janela
    # precisam ser lidas depois dele, senão saem erradas com escala de tela != 100%.
    with mss.mss() as sct:
        if CAPTURE_MODE == "window":
            region = _foreground_window_region()
            if not region or region["width"] <= 0 or region["height"] <= 0:
                region = sct.monitors[MONITOR]
        else:
            region = sct.monitors[MONITOR]
        shot = sct.grab(region)
    png = mss.tools.to_png(shot.rgb, shot.size)
    if DEBUG_DIR:
        print(f"Print salvo em: {_save_debug(png).resolve()} ({shot.width}x{shot.height})")
    return png
