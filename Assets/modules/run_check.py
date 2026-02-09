# run_check.py
"""
런체크 모듈 — 게임 실행 전 환경(운영체제, 파이썬, 의존 패키지 등)을 확인합니다.
"""

import sys

# --- 표준/서드파티 임포트 시도 (없으면 즉시 종료) ---
try:
    import platform
    from packaging.version import Version
    from tkinter import messagebox
    import pyaudio
except ImportError:
    # 필수 모듈이 없으면 종료
    sys.exit()

# -----------------------
# 직접 실행 방지용 메시지 (모듈이 직접 실행되면 종료)
# -----------------------
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()

# -----------------------
# 요구 버전 / 플랫폼 상수
# -----------------------
REQUIRED_OS_SYSTEM: str = "Windows"
REQUIRED_OS_RELEASE: str = "11"

REQUIRED_PYTHON_VERSION_STR: str = "3.13.5"
REQUIRED_PYGAME_VERSION_STR: str = "2.6.1"

# -----------------------
# 의존성 임포트 확인
# -----------------------
try:
    import pygame
    from opensimplex import OpenSimplex
    import random
    import math
    import time
    from screeninfo import get_monitors
    import psutil
    from enum import Enum
    import hashlib
    import typing
    from supabase import create_client, Client
except ImportError:
    messagebox.showerror(
        "Import Error",
        "Could not import required dependencies.\nPlease ensure all required packages are installed.",
    )
    sys.exit()

# -----------------------
# 게임 내부 모듈 존재 확인
# -----------------------
try:
    from . import entities  # noqa: F401
    from . import assets  # noqa: F401
    from . import utility  # noqa: F401
    from . import biome  # noqa: F401
    from . import world  # noqa: F401
    from . import graphic_effect  # noqa: F401
    from . import language  # noqa: F401

except ImportError:
    messagebox.showerror("Import Error", "Could not import internal game modules.")
    sys.exit()


# -----------------------
# 환경 검사 함수들
# -----------------------
def _ask_yes_no(title: str, message: str) -> bool:
    """
    예/아니오 메시지를 띄우고 사용자의 응답을 반환합니다.
    True = 예(계속), False = 아니오(종료)
    """
    try:
        return messagebox.askyesno(title, message)
    except Exception:
        # GUI 표시가 불가한 환경이면 안전하게 False 반환하여 종료하도록 함
        return False


def check_operating_system() -> None:
    """운영체제가 권장 환경인지 확인하고, 사용자에게 계속 실행 여부를 물음."""
    current_system = platform.system()
    current_release = platform.release()

    if not (
        current_system == REQUIRED_OS_SYSTEM and current_release == REQUIRED_OS_RELEASE
    ):
        response = _ask_yes_no(
            "OS Warning",
            (
                f"This game was developed for {REQUIRED_OS_SYSTEM} {REQUIRED_OS_RELEASE}.\n"
                "Running on a different OS may cause unexpected behavior.\n\n"
                f"Current OS: {current_system} {current_release}\n\n"
                "Do you want to continue?"
            ),
        )
        if not response:
            sys.exit()


def check_python_version() -> None:
    """파이썬 버전이 권장 버전 이상인지 확인하고, 사용자에게 계속 실행 여부를 물음."""
    python_version = Version(platform.python_version())
    required_version = Version(REQUIRED_PYTHON_VERSION_STR)
    if python_version < required_version:
        response = _ask_yes_no(
            "Python Version Warning",
            (
                f"This game was developed for Python {REQUIRED_PYTHON_VERSION_STR}.\n"
                f"Current version: {platform.python_version()}\n"
                "Do you want to continue?"
            ),
        )
        if not response:
            sys.exit()


def check_pygame_version() -> None:
    """
    pygame 환경(ce 여부 및 버전)을 확인한다.
    - pygame.IS_CE 존재 여부로 pygame-ce 사용 여부를 확인한다.
    - 이후 버전 체크를 수행한다.
    """
    try:
        # pygame.IS_CE 존재 여부 판단 (없으면 AttributeError)
        is_ce = bool(getattr(pygame, "IS_CE", False))
    except Exception:
        is_ce = False

    # pygame이 CE일 경우 경고
    if is_ce:
        response = _ask_yes_no(
            "Pygame Version Warning",
            (
                f"This game was developed for pygame {REQUIRED_PYGAME_VERSION_STR}.\n"
                "You are using pygame-ce.\n"
                "Do you want to continue?"
            ),
        )
        if not response:
            sys.exit()
        return

    # pygame 이고 버전이 낮은 경우 경고
    try:
        pygame_version = Version(pygame.version.ver)
    except Exception:
        # 버전을 정확히 읽지 못하면 경고하고 종료 여부 묻기
        response = _ask_yes_no(
            "Pygame Version Warning",
            "Could not determine pygame version.\nDo you want to continue?",
        )
        if not response:
            sys.exit()
        return

    required = Version(REQUIRED_PYGAME_VERSION_STR)
    if pygame_version < required:
        response = _ask_yes_no(
            "Pygame Version Warning",
            (
                f"This game was developed for pygame {REQUIRED_PYGAME_VERSION_STR}.\n"
                f"Current version: pygame {pygame_version}\n"
                "Do you want to continue?"
            ),
        )
        if not response:
            sys.exit()


def check_audio() -> None:
    """오디오 출력장치가 있는지 확인하고, 사용자에게 계속 실행 여부를 물음."""
    try:
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        has_output_device = any(
            p.get_device_info_by_index(i).get("maxOutputChannels", 0) > 0
            for i in range(device_count)
        )
        p.terminate()
    except Exception:
        has_output_device = False

    if not has_output_device:
        response = _ask_yes_no(
            "Audio Warning",
            (
                "No audio output device found.\n"
                "Sound may not play.\n"
                "Do you want to continue?"
            ),
        )
        if not response:
            sys.exit()


def run_checks() -> None:
    """모든 환경 검사를 실행합니다."""
    check_operating_system()
    check_python_version()
    check_pygame_version()
    check_audio()
