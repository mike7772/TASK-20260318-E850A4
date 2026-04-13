from __future__ import annotations

import os
import threading
from dataclasses import dataclass


@dataclass
class RuntimeState:
    env: str
    is_test: bool
    bootstrapped: bool = False
    auth_initialized: bool = False


_lock = threading.Lock()
_state = RuntimeState(env=os.getenv("ENV", "prod").lower(), is_test=os.getenv("ENV", "prod").lower() == "test")


def get_state() -> RuntimeState:
    return _state


def mark_bootstrapped():
    with _lock:
        _state.bootstrapped = True


def mark_auth_initialized():
    with _lock:
        _state.auth_initialized = True

