"""Thin Cocoa calls via ctypes (no pyobjc dependency). Every call is best-effort."""
from __future__ import annotations

import ctypes
import ctypes.util
import sys

NS_ACCESSORY = 1  # NSApplicationActivationPolicyAccessory: no Dock icon, no menu bar takeover
CAN_JOIN_ALL_SPACES = 1 << 0
STATIONARY = 1 << 4
IGNORES_CYCLE = 1 << 6
FULLSCREEN_AUXILIARY = 1 << 8

_objc = None


def _lib():
    global _objc
    if _objc is None and sys.platform == "darwin":
        _objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        _objc.objc_getClass.restype = ctypes.c_void_p
        _objc.objc_getClass.argtypes = [ctypes.c_char_p]
        _objc.sel_registerName.restype = ctypes.c_void_p
        _objc.sel_registerName.argtypes = [ctypes.c_char_p]
    return _objc


def _send(receiver: int, selector: bytes, *args: int):
    lib = _lib()
    fn = lib.objc_msgSend
    fn.restype = ctypes.c_void_p
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_ulong] * len(args)
    return fn(receiver, lib.sel_registerName(selector), *args)


def hide_dock_icon() -> None:
    """Run as a menu-bar-only accessory app."""
    if sys.platform != "darwin":
        return
    try:
        app = _send(_lib().objc_getClass(b"NSApplication"), b"sharedApplication")
        _send(app, b"setActivationPolicy:", NS_ACCESSORY)
    except Exception:  # noqa: BLE001
        pass


def disable_shadow(win_id: int) -> None:
    """macOS caches a window's shadow; an animated transparent sprite leaves ghosts."""
    if sys.platform != "darwin" or not win_id:
        return
    try:
        window = _send(int(win_id), b"window")
        if window:
            _send(window, b"setHasShadow:", 0)
            _send(window, b"invalidateShadow")
    except Exception:  # noqa: BLE001
        pass


def has_shadow(win_id: int) -> bool | None:
    if sys.platform != "darwin" or not win_id:
        return None
    try:
        window = _send(int(win_id), b"window")
        return bool(_send(window, b"hasShadow")) if window else None
    except Exception:  # noqa: BLE001
        return None


def show_on_all_spaces(win_id: int, enabled: bool = True) -> None:
    """Pet follows across Spaces and sits above full-screen apps."""
    if sys.platform != "darwin" or not win_id:
        return
    try:
        window = _send(int(win_id), b"window")
        if not window:
            return
        behavior = IGNORES_CYCLE | (CAN_JOIN_ALL_SPACES | FULLSCREEN_AUXILIARY if enabled else 0)
        _send(window, b"setCollectionBehavior:", behavior)
        _send(window, b"setHidesOnDeactivate:", 0)
    except Exception:  # noqa: BLE001
        pass
