# Selement - A philosophical game about self and elements.
# Copyright (C) 2025  Brayden Seung-hoon Oh
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# graphic_effect.py
"""
그래픽 이펙트 모듈
"""

import sys
import array
from tkinter import messagebox
import pygame
import random
import moderngl
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

# ----------------- GLSL Shader Sources -----------------
VERTEX_SHADER = """
#version 330
in vec2 in_vert;
in vec2 in_texcoord;
out vec2 v_texcoord;
void main() {
    // Pygame 서피스 -> OpenGL 텍스처 업로드 시 발생하는 상하 반전을 셰이더에서 해결
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_texcoord = vec2(in_texcoord.x, 1.0 - in_texcoord.y);
}
"""

FRAGMENT_SHADER = """
#version 330
uniform sampler2D Texture;
uniform float gray_intensity; // 0.0 ~ 1.0

in vec2 v_texcoord;
out vec4 f_color;

void main() {
    vec4 color = texture(Texture, v_texcoord);
    
    // 표준 그레이스케일 공식
    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    
    // gray_intensity 만큼 원본과 그레이스케일을 보간(mix)
    vec3 final_color = mix(color.rgb, vec3(gray), gray_intensity);
    f_color = vec4(final_color, color.a);
}
"""


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
    GPU(ModernGL)를 활용하여 실시간 포스트 프로세싱 후 진짜 디스플레이에 출력합니다.
    """

    def __init__(self) -> None:
        self.effect_surface: pygame.Surface = pygame.Surface(
            (utility.Screen.target_width, utility.Screen.target_height)
        )
        self.dark_surface: Optional[pygame.Surface] = None
        self.darken_timer: Optional[utility.TimeKeeper] = None

        self.gray_intensity: int = 0
        self.ctx = moderngl.create_context()

        # 셰이더 프로그램 컴파일
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )

        # 화면 좌표계 설정 (-1.0 ~ 1.0 범위로 꽉 차게 그리기)
        vertices = array.array(
            "f",
            [
                -1.0,
                1.0,
                0.0,
                1.0,  # 좌상
                -1.0,
                -1.0,
                0.0,
                0.0,  # 좌하
                1.0,
                1.0,
                1.0,
                1.0,  # 우상
                1.0,
                -1.0,
                1.0,
                0.0,  # 우하
            ],
        )
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.simple_vertex_array(
            self.program, self.vbo, "in_vert", "in_texcoord"
        )

        # 진짜 디스플레이 해상도(target_width/height)에 맞춰 텍스처 버퍼 생성
        self.texture = self.ctx.texture(
            (utility.Screen.target_width, utility.Screen.target_height), 4
        )
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.texture.swizzle = "BGRA"

    def darken(self, time: float) -> None:
        """time 초 동안 서서히 화면을 어둡게 만드는 효과를 시작합니다."""
        self.darken_timer = utility.TimeKeeper(duration=time)

    def remove_all_effect(self) -> None:
        """적용된 모든 이펙트를 제거합니다."""
        self.dark_surface = None
        self.darken_timer = None
        self.gray_intensity = 0

    def post_process(self, surface: pygame.Surface) -> None:
        """
        인자로 받은 게임 화면 서피스(surface)에 이펙트를 처리하고,
        GPU를 거쳐 최종 진짜 디스플레이(OpenGL 윈도우)에 바로 그려버립니다.
        """
        final_surface = surface

        # 1. Darken 효과 (기존 CPU 블릿 방식 적용)
        if self.darken_timer:
            duration = getattr(self.darken_timer, "duration", 0) or 1
            elapsed = self.darken_timer.elapsed_time()
            ratio = max(0.0, min(1.0, elapsed / duration))
            alpha = int(ALPHA_MAX * ratio)
            alpha = max(ALPHA_MIN, min(ALPHA_MAX, alpha))

            self.dark_surface = assets.Image.dark_screen.copy()
            self.dark_surface.set_alpha(alpha)

            # 최종 완성본 서피스에 암전 블릿
            final_surface.blit(self.dark_surface, (0, 0))

        # 2. ModernGL 포스트 프로세싱 및 최종 디스플레이 렌더링
        # 게임이 그려진 최종 서피스의 픽셀 뷰를 통째로 가져와 GPU 텍스처로 전송
        texture_data = pygame.image.tobytes(final_surface, "RGBA")
        self.texture.write(texture_data)

        # OpenGL 백버퍼(진짜 화면이 그려질 임시 공간) 클리어
        self.ctx.clear(0, 0, 0, 1)

        # 그레이스케일 강도 계산 (0~255 -> 0.0~1.0 변환)
        intensity_normalized = float(self.gray_intensity) / 255.0
        self.program["gray_intensity"].value = intensity_normalized

        # 텍스처 유포 및 셰이더 적용하여 진짜 디스플레이 백버퍼에 그리기
        self.texture.use(0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        # [주의] 이 작업이 끝나면 호출측(메인 루프)에서 pygame.display.flip()만 해주면 끝납니다!
