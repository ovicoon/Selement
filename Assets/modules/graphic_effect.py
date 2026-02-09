# graphic_effect.py
"""
그래픽 이펙트 모듈
"""

import sys
from tkinter import messagebox
import pygame
import random
from typing import List, Optional, Tuple

# 파일 직접 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import utility
    from . import assets


# -----------------------
# 상수
# -----------------------
DEFAULT_PARTICLE_ANGLE_RANGE: Tuple[float, float] = (0.0, 360.0)
EFFECT_SURFACE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SRCALPHA
ALPHA_MIN: int = 0
ALPHA_MAX: int = 255


class Particle:
    """
    단일 파티클을 나타내는 클래스.

    Attributes:
        x, y: 현재 위치
        vel: 현재 속도(크기)
        angle: 이동 각도(도 단위)
        drag: 속도에 곱해지는 감쇠 계수
        life: 남은 생명(초)
        max_life: 초기 생명(초) (투명도 계산용)
        source_image: 원본 서피스 (alpha 변경을 위해 복사)
        image: 현재 그려질 서피스
        image_alpha: 베이스 알파값 (0..255)
    """

    def __init__(
        self,
        x: float,
        y: float,
        vel: float,
        angle: float,
        drag: float,
        life: float,
        image: Optional[pygame.Surface],
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.image: Optional[pygame.Surface] = image
        self.name: str = "particle"
        self.center_pivot: bool = False
        self.do_not_arrange: bool = False

        self.vel: float = vel
        self.angle: float = angle
        self.drag: float = drag
        self.max_life: float = life
        self.life: float = life

        self.source_image: Optional[pygame.Surface] = image
        self.image_alpha: int = 255

    def update(self, dt: float) -> None:
        """파티클 상태(위치, 속도, 남은 수명, 투명도)를 갱신합니다."""
        if self.life <= 0:
            return

        # 이동: polar -> vector 변환하여 위치 갱신
        vec = pygame.math.Vector2()
        vec.from_polar((self.vel, self.angle))
        self.x += vec.x * dt
        self.y += vec.y * dt

        # 감속 적용
        self.vel *= self.drag

        # 수명 감소
        self.life -= dt

        # 알파(투명도) 계산: 남은 수명 비율에 따라 투명화
        # max_life가 0이면 progress를 0으로 처리
        progress = (
            (self.life / self.max_life)
            if (self.max_life and self.max_life != 0)
            else 0.0
        )

        # 안전하게 이미지 및 알파 처리
        if self.source_image:
            try:
                # 복사본을 만들고 알파를 설정
                img = self.source_image.copy()
                base_alpha = max(ALPHA_MIN, min(ALPHA_MAX, self.image_alpha))
                img.set_alpha(int(base_alpha * max(0.0, progress)))
                self.image = img
            except Exception:
                # 이미지 처리 중 오류가 나면 source_image를 그대로 사용하거나 None 설정
                self.image = self.source_image
        else:
            self.image = None


class ParticleShooter:
    """
    파티클을 생성/관리하는 간단한 발사기.
    - shoot(...) 으로 여러 파티클을 한 번에 생성합니다.
    """

    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def shoot(
        self,
        x: float,
        y: float,
        vel_range: Tuple[float, float],
        drag: float,
        life: float,
        image: Optional[pygame.Surface],
        amount: int,
    ) -> None:
        """
        여러 방향으로 파티클을 amount 개수만큼 발사합니다.

        Args:
            x, y: 파티클 출발 위치
            vel_range: (min_vel, max_vel) 범위 내에서 속도를 랜덤 선택
            drag: 속도 감소 계수
            life: 파티클 생명(초)
            image: 파티클에 사용할 이미지(서피스)
            amount: 생성할 파티클 개수
        """
        min_vel, max_vel = vel_range
        for _ in range(amount):
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vel=random.uniform(min_vel, max_vel),
                    angle=random.uniform(
                        DEFAULT_PARTICLE_ANGLE_RANGE[0], DEFAULT_PARTICLE_ANGLE_RANGE[1]
                    ),
                    drag=drag,
                    life=life,
                    image=image,
                )
            )

    def update(self, dt: float) -> None:
        """모든 파티클을 갱신하고 수명이 끝난 파티클을 제거합니다."""
        for p in self.particles:
            p.update(dt)
        # 수명이 남아있는 파티클만 유지
        self.particles = [p for p in self.particles if p.life > 0]


class ScreenEffect:
    """
    전체 화면에 적용할 이펙트를 생성/관리합니다.
    - 현재는 'darken' (서서히 어두워짐) 기능을 제공합니다.
    - get_effect()는 적용된 이펙트가 그려진 서피스를 반환합니다.
    """

    def __init__(self) -> None:
        self.effect_surface: pygame.Surface = pygame.Surface(
            (utility.Screen.target_width, utility.Screen.target_height),
            EFFECT_SURFACE_FLAGS,
        )
        self.dark_surface: Optional[pygame.Surface] = None
        self.darken_timer: Optional[utility.TimeKeeper] = None

    def darken(self, time: float) -> None:
        """time 초 동안 서서히 화면을 어둡게 만드는 효과를 시작합니다."""
        self.darken_timer = utility.TimeKeeper(duration=time)

    def remove_all_effect(self) -> None:
        """적용된 모든 이펙트를 제거합니다."""
        self.dark_surface = None
        self.darken_timer = None

    def get_effect(self) -> pygame.Surface:
        """
        현재 적용 중인 이펙트를 그려서 effect_surface를 반환합니다.
        - darken 타이머가 설정되어 있으면 해당 비율만큼 dark_screen을 alpha로 블렌드합니다.
        """
        # 투명 초기화
        self.effect_surface.fill((255, 255, 255, 0))

        if self.darken_timer:
            # duration 0 방지
            duration = getattr(self.darken_timer, "duration", 0) or 1
            elapsed = self.darken_timer.elapsed_time()
            # 비율 계산 후 0..1 범위로 클램프
            ratio = max(0.0, min(1.0, elapsed / duration))
            alpha = int(ALPHA_MAX * ratio)
            alpha = max(ALPHA_MIN, min(ALPHA_MAX, alpha))

            # dark_screen 복사본을 만들고 alpha 적용
            try:
                self.dark_surface = assets.Image.dark_screen.copy()
                self.dark_surface.set_alpha(alpha)
                self.effect_surface.blit(self.dark_surface, (0, 0))
            except Exception:
                # 이미지 처리 실패 시 무시하고 빈 이펙트 반환
                pass

        return self.effect_surface
