# run_check.py
"""
런체크 모듈 — 게임 실행 전 환경을 확인합니다.
"""

import sys

# --- 표준/서드파티 임포트 시도 (없으면 즉시 종료) ---
try:
    import platform
    from packaging.version import Version
    from tkinter import messagebox
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


def run_checks() -> None:
    """환경 검사를 실행합니다."""
    check_operating_system()
