# biome.py
"""
바이옴 판정 모듈
"""

import math
from enum import Enum
from tkinter import messagebox
import sys
from typing import Any

# 단독 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()


class Biome(Enum):
    """바이옴 종류 정의"""

    fire = 1
    water = 2
    dirt = 3
    air = 4
    fifth_biome = 5


# -----------------------
# 상수
# -----------------------
# 노이즈 제너레이터가 없을 때 반환할 바이옴
DEFAULT_BIOME_WHEN_NOISE_MISSING = Biome.fifth_biome


def get_biome(world: Any, x: float, y: float) -> Biome:
    """
    주어진 월드와 좌표(x, y)에 따라 바이옴을 판정하여 반환합니다.

    동작 원리:
      - world에 temp_noise_generator 및 moist_noise_generator가 있으면
        해당 노이즈 값을 사용하여 4종 바이옴(fire, water, dirt, air) 중 하나를 반환합니다.
      - 노이즈 제너레이터가 없으면 특별 바이옴(Biome.fifth_biome)을 반환합니다.

    좌표 처리:
      - 입력 좌표를 타일 중심으로 정렬한 뒤 노이즈 값을 조회합니다.
      - 노이즈값(temp, moist)이 양수인지 음수인지로 바이옴을 분류합니다.
    """
    # 노이즈 제너레이터 유무 확인
    has_temp = hasattr(world, "temp_noise_generator")
    has_moist = hasattr(world, "moist_noise_generator")
    if has_temp and has_moist:
        # 타일 중심으로 좌표를 정렬
        tile_size = world.tile_size

        centered_x = math.floor(x / tile_size) * tile_size + tile_size // 2
        centered_y = math.floor(y / tile_size) * tile_size + tile_size // 2

        # 노이즈 좌표(월드 오프셋 및 바이옴 크기 고려)
        temp = world.temp_noise_generator.noise2(
            (centered_x + getattr(world, "offset1", 0))
            / getattr(world, "biome_size", 1),
            (centered_y + getattr(world, "offset2", 0))
            / getattr(world, "biome_size", 1),
        )
        moist = world.moist_noise_generator.noise2(
            (centered_x + getattr(world, "offset3", 0))
            / getattr(world, "biome_size", 1),
            (centered_y + getattr(world, "offset4", 0))
            / getattr(world, "biome_size", 1),
        )

        # 판정 로직
        if temp > 0:
            if moist > 0:
                # 온도 높고 습하면 공기
                return Biome.air
            else:
                # 온도 높고 건조하면 불
                return Biome.fire
        else:
            if moist > 0:
                # 온도 낮고 습하면 물
                return Biome.water
            else:
                # 온도 낮고 건조하면 흙
                return Biome.dirt
    else:
        # 노이즈 제너레이터가 하나라도 없으면 특별 바이옴 반환
        return DEFAULT_BIOME_WHEN_NOISE_MISSING
