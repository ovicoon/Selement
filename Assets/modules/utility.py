# utility.py
"""
유틸리티 모듈
"""

from tkinter import messagebox
import pygame
import pygame.freetype
import sys
import random
from screeninfo import get_monitors
import math
from enum import Enum
from typing import Any, Optional, Tuple, List


# 파일 직접 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import assets


# -----------------------
# 상수
# -----------------------
DEFAULT_TARGET_WIDTH: int = 1920
DEFAULT_TARGET_HEIGHT: int = 1080
GAME_SURFACE_FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF

DEFAULT_CURSOR_BLINK_SEC: float = 0.5
DEFAULT_COLLIDER_RADIUS: int = 32


# -----------------------
# 초기화 관련 함수
# -----------------------
def init() -> None:
    """Pygame 및 리소스 초기화, 화면 세팅 및 에셋 로드"""
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    pygame.mixer.set_num_channels(16)

    Screen.set_window()
    assets.Image.load()
    assets.Font.load()
    assets.Sound.load()

    # 창 제목 설정
    pygame.display.set_caption("Selement")


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """두 점 사이의 유클리드 거리 반환"""
    return math.sqrt(((x2 - x1) ** 2 + (y2 - y1) ** 2))


# -----------------------
# Collider 관련
# -----------------------
class ColliderType(Enum):
    """콜라이더 종류 구분"""

    mask_collider = 0
    circle_collider = 1


class Collider:
    """
    충돌 판정을 위한 래퍼 클래스
    - data가 pygame.Surface면 마스크 기반 충돌
    - 그렇지 않으면 반지름 기반(circle) 충돌 (data는 반지름)
    """

    def __init__(
        self, x: float, y: float, data: Any, center_pivot: bool = False
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.data: Any = data
        self.center_pivot: bool = center_pivot

        # 타입에 따라 surface/타입 결정
        if isinstance(self.data, pygame.Surface):
            self.type: ColliderType = ColliderType.mask_collider
            self.surface: pygame.Surface = self.data
        else:
            self.type = ColliderType.circle_collider
            # data는 반지름으로 가정
            self.surface = pygame.transform.scale(
                assets.Image.circle, (self.data * 2, self.data * 2)
            )

        # 마스크 및 rect 초기화
        self.mask: pygame.Mask = pygame.mask.from_surface(self.surface)
        if self.center_pivot:
            self.rect: pygame.Rect = self.surface.get_rect(center=(self.x, self.y))
        else:
            self.rect = self.surface.get_rect(midbottom=(self.x, self.y))

    def collide(self, collider: "Collider") -> Optional[Tuple[int, int]]:
        """
        두 콜라이더가 충돌하는지 검사.
        충돌하지 않으면 None, 충돌하면 overlap 좌표 튜플을 반환.
        """
        if not self.rect.colliderect(collider.rect):
            return None

        offset_x = collider.rect.x - self.rect.x
        offset_y = collider.rect.y - self.rect.y
        return self.mask.overlap(collider.mask, (offset_x, offset_y))

    def update(self, x: float, y: float, data: Any) -> None:
        """위치/데이터 갱신. data 변경 시 surface 재생성."""
        self.x = x
        self.y = y

        if data != self.data:
            self.data = data

        if self.type == ColliderType.circle_collider:
            # 반지름 기반이면 surface 재생성
            self.surface = pygame.transform.scale(
                assets.Image.circle, (self.data * 2, self.data * 2)
            )

        # 마스크/rect 갱신
        self.mask = pygame.mask.from_surface(self.surface)
        if self.center_pivot:
            self.rect = self.surface.get_rect(center=(self.x, self.y))
        else:
            self.rect = self.surface.get_rect(midbottom=(self.x, self.y))


# -----------------------
# 화면/해상도 처리
# -----------------------
class Screen:
    """
    화면 관련 전역 설정 보관용 클래스 (정적 멤버)
    - set_window() 호출로 실제 디스플레이 모드 설정
    - get_scaled_mouse_pos()로 실제 마우스 좌표를 game_surface 기준 좌표로 변환
    """

    screen_width: int = get_monitors()[0].width
    screen_height: int = get_monitors()[0].height

    target_width: int = DEFAULT_TARGET_WIDTH
    target_height: int = DEFAULT_TARGET_HEIGHT

    game_surface: pygame.Surface = pygame.Surface(
        (target_width, target_height), GAME_SURFACE_FLAGS
    )

    game_height: Optional[int] = None
    game_width: Optional[int] = None
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    screen: Optional[pygame.Surface] = None

    @staticmethod
    def set_window() -> None:
        """실제 디스플레이 모드와 game_surface의 크기를 결정하여 설정"""
        if Screen.screen_width / Screen.screen_height < 16 / 9:
            Screen.game_width = Screen.screen_width
            Screen.game_height = int(Screen.screen_width * 9 / 16)
        else:
            Screen.game_height = Screen.screen_height
            Screen.game_width = int(Screen.screen_height * 16 / 9)

        Screen.screen = pygame.display.set_mode(
            (Screen.screen_width, Screen.screen_height),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF,
        )
        Screen.center_x = (Screen.screen_width - Screen.game_width) / 2
        Screen.center_y = (Screen.screen_height - Screen.game_height) / 2

    @staticmethod
    def get_scaled_mouse_pos(mouse_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        실제 마우스 좌표(mouse_pos)를 game_surface 좌표계로 변환 반환.
        1) 화면 중앙 오프셋 제거
        2) target_width/height 기준으로 스케일 적용
        """
        adjusted_x = mouse_pos[0] - (Screen.center_x or 0)
        adjusted_y = mouse_pos[1] - (Screen.center_y or 0)

        scale_x = Screen.target_width / (Screen.game_width or Screen.target_width)
        scale_y = Screen.target_height / (Screen.game_height or Screen.target_height)

        scaled_x = int(adjusted_x * scale_x)
        scaled_y = int(adjusted_y * scale_y)

        return (scaled_x, scaled_y)


# -----------------------
# 씬 / 카메라 관련
# -----------------------
class Scene:
    """간단한 씬 컨테이너: background -> entities -> ui 순으로 렌더링"""

    def __init__(self) -> None:
        self.entities: List[Any] = []
        self.background: List[Any] = []  # 엔티티보다 먼저 렌더링
        self.ui: List[Any] = []  # 엔티티 다음에 렌더링


class Camera:
    """카메라: 씬을 기준으로 게임 오브젝트를 렌더링"""

    def __init__(self, x: float, y: float) -> None:
        self.rendering_objects: List[Tuple[Tuple[float, float], Any]] = []
        self.on_ground: List[Tuple[Tuple[float, float], Any]] = []
        self.shake_time: float = 0.0
        self.shake_strength: float = 0.0
        self.x: float = x
        self.y: float = y

    def shake(self, time: float, strength: float) -> None:
        """카메라 흔들기 트리거"""
        self.shake_time = time
        self.shake_strength = strength

    def update_position(self, x: float, y: float, deltatime: float) -> None:
        """카메라 위치 갱신 및 흔들기 처리"""
        self.x = x
        self.y = y
        if self.shake_time > 0:
            self.x += random.randint(
                -int(self.shake_strength), int(self.shake_strength)
            )
            self.y += random.randint(
                -int(self.shake_strength), int(self.shake_strength)
            )
            self.shake_time -= deltatime
        if self.shake_time < 0:
            self.shake_time = 0
            self.shake_strength = 0

    def render_scene(
        self, scene: Scene, pygame_event: List[Any], render_collider: bool = False
    ) -> None:
        """
        씬 렌더링:
         - 배경 타일 렌더링
         - 엔티티 컬링(화면 밖이면 그리지 않음)
         - z-order( y 좌표 기준 )로 정렬하여 렌더링
         - UI 렌더링 (Button/InputField/Line/OverLaySurface 처리)
         - render_collider=True 이면 콜라이더를 시각화
        """
        # 화면 초기화
        Screen.screen.fill((0, 0, 0))
        Screen.game_surface.fill((0, 0, 0))

        collider_visuals: List[Collider] = []

        # 엔티티 리스트 처리: 컬링 및 그리기 대상 분류
        for entity in scene.entities:
            if getattr(entity, "image", None):
                if entity.center_pivot is True:
                    render_coord = (
                        Screen.target_width / 2
                        - entity.image.get_width() / 2
                        + entity.x
                        - self.x,
                        Screen.target_height / 2
                        - entity.image.get_height() / 2
                        + entity.y
                        - self.y,
                    )
                else:
                    render_coord = (
                        Screen.target_width / 2
                        - entity.image.get_width() / 2
                        + entity.x
                        - self.x,
                        Screen.target_height / 2
                        - entity.image.get_height()
                        + entity.y
                        - self.y,
                    )

                entity_rect = pygame.Rect(render_coord, entity.image.get_size())
                screen_rect = pygame.Rect(
                    0, 0, Screen.target_width, Screen.target_height
                )

                # 엔티티 컬링: 화면 내부에 있으면 rendering_objects에, do_not_arrange면 on_ground에
                if entity_rect.colliderect(screen_rect) and not getattr(
                    entity, "do_not_arrange", False
                ):
                    self.rendering_objects.append((render_coord, entity))
                elif getattr(entity, "do_not_arrange", False):
                    self.on_ground.append((render_coord, entity))

            # 디버그용 콜라이더 시각화 대상 수집
            if render_collider and hasattr(entity, "collider"):
                if entity.collider.type == ColliderType.circle_collider:
                    collider_visuals.append(entity.collider)

        # 배경 타일 렌더링 (컬링 포함)
        for tile in scene.background:
            render_coord = (
                Screen.target_width / 2 - tile.image.get_width() / 2 + tile.x - self.x,
                Screen.target_height / 2
                - tile.image.get_height() / 2
                + tile.y
                - self.y,
            )
            tile_rect = pygame.Rect(render_coord, tile.image.get_size())
            screen_rect = pygame.Rect(0, 0, Screen.target_width, Screen.target_height)
            if tile_rect.colliderect(screen_rect):
                Screen.game_surface.blit(tile.image, render_coord)

        # on_ground(땅 위 고정 오브젝트) 먼저 렌더
        for entity in self.on_ground:
            Screen.game_surface.blit(entity[1].image, entity[0])

        # rendering_objects를 y 값으로 정렬하여 그리기 (y가 작으면 먼저 그려짐)
        rendering_order = sorted(self.rendering_objects, key=lambda e: e[1].y)
        for obj in rendering_order:
            Screen.game_surface.blit(obj[1].image, obj[0])

        # 콜라이더 렌더(디버그)
        for col in collider_visuals:
            pygame.draw.circle(
                Screen.game_surface,
                (0, 0, 255),
                (
                    Screen.target_width / 2 + col.x - self.x,
                    Screen.target_height / 2 + col.y - self.y,
                ),
                col.data,
                10,
            )

        # 렌더 큐 초기화
        self.on_ground.clear()
        self.rendering_objects.clear()

        # UI 렌더링: 버튼/입력창/라인/오버레이 등 처리
        for ui in scene.ui:
            # Button, InputField는 업데이트를 통해 자기 자신을 그린다
            if type(ui) in [Button, InputField]:
                ui.update(pygame_event)
            elif type(ui) == Line:
                ui.update(pygame_event)
            elif type(ui) == OverLaySurface:
                # OverLaySurface는 이미 정렬된 surface/rect가 있으므로 바로 blit
                Screen.game_surface.blit(ui.surface, ui.rect)


# -----------------------
# 시간/애니메이션 관련 유틸
# -----------------------
class TimeKeeper:
    """간단한 타이머: 시작 시점 저장, duration 초 이후 is_finished True 반환"""

    def __init__(self, duration: Optional[float] = None) -> None:
        self.duration: Optional[float] = duration
        self.start_time: int = pygame.time.get_ticks()

    def is_finished(self) -> bool:
        if self.duration is None:
            return True
        return (pygame.time.get_ticks() - self.start_time) / 1000 >= self.duration

    def reset(self) -> None:
        self.start_time = pygame.time.get_ticks()

    def elapsed_time(self) -> float:
        return (pygame.time.get_ticks() - self.start_time) / 1000


class Animation:
    """프레임 기반 애니메이션: fps 기반으로 현재 프레임 반환"""

    def __init__(self, frames: List[pygame.Surface], fps: float) -> None:
        self.frames: List[pygame.Surface] = frames
        self.current_frame_index: int = 0
        self.current_frame: pygame.Surface = self.frames[self.current_frame_index]
        # 내부적으로 각 프레임 지속시간 계산 (초)
        self.fps: float = 1 / fps if fps != 0 else 0
        self.stopwatch: TimeKeeper = TimeKeeper()

    def update(self) -> pygame.Surface:
        """경과 시간에 따라 current_frame을 갱신하여 반환"""
        duration = self.stopwatch.elapsed_time()
        past_frames = int(duration / self.fps) if self.fps else 0
        self.current_frame_index = past_frames % len(self.frames)
        self.current_frame = self.frames[self.current_frame_index]
        return self.current_frame


# -----------------------
# UI 컴포넌트들
# -----------------------
class Button:
    """간단한 버튼: 클릭 시 action() 호출 및 자체 렌더링"""

    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        text: str,
        button_color: Tuple[int, int, int],
        hover_color: Tuple[int, int, int],
        action: Any,
        font: Any,
        text_color: Tuple[int, int, int] = (0, 0, 0),
        center_pivot: bool = True,
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.font: Any = font
        self.button_color: Tuple[int, int, int] = button_color
        self.hover_color: Tuple[int, int, int] = hover_color
        self.action: Any = action
        self.text_color: Tuple[int, int, int] = text_color
        self.center_pivot: bool = center_pivot

        self.is_clicked: bool = False

        if self.center_pivot:
            self.rect.center = (
                Screen.target_width / 2 + x,
                Screen.target_height / 2 + y,
            )

    def update(self, pygame_event: List[Any]) -> None:
        """마우스 포인터 검사, 클릭 시 사운드 재생 및 액션 호출, 자체 그리기 수행"""
        mouse_pos = Screen.get_scaled_mouse_pos(pygame.mouse.get_pos())
        current_color = self.button_color
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color
            for event in pygame_event:
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    assets.Sound.button.play()
                    self.action()

        pygame.draw.rect(Screen.game_surface, current_color, self.rect)
        text_surface = str_to_surface(self.text, self.font, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        Screen.game_surface.blit(text_surface, text_rect)


class OverLaySurface:
    """정적인 서피스(텍스트/아이콘 등)를 화면에 오버레이할 때 사용하는 래퍼"""

    def __init__(
        self, x: float, y: float, surface: pygame.Surface, center_pivot: bool = True
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.surface: pygame.Surface = surface
        self.rect: pygame.Rect = surface.get_rect()
        if center_pivot:
            self.rect.center = (
                Screen.target_width / 2 + x,
                Screen.target_height / 2 + y,
            )
        else:
            self.rect.topleft = (x, y)


def str_to_surface(
    text: str,
    font: pygame.freetype.Font,
    color: tuple[int, int, int] = (255, 255, 255),
    space_line: float = 0.1,
) -> pygame.Surface:
    """
    여러 줄 텍스트를 하나의 Surface로 렌더링하여 반환
    """
    lines = text.splitlines()
    surfaces = []
    width = 0
    height = 0
    line_spacing = font.get_sized_height() * space_line  # 줄간격 비율

    # 각 줄을 개별 Surface로 렌더링
    for i, line in enumerate(lines):
        surf = font.render(line, color)[0]
        surfaces.append(surf)
        width = max(width, surf.get_width())
        height += surf.get_height()

        if i < len(lines) - 1:
            height += line_spacing

    # 최종 Surface 생성 (투명 배경)
    final_surf = pygame.Surface((width, height), pygame.SRCALPHA)

    y = 0
    for i, surf in enumerate(surfaces):
        final_surf.blit(surf, (0, y))
        y += surf.get_height()

        if i < len(lines) - 1:
            y += line_spacing

    return final_surf


class InputField:
    """텍스트 입력 필드: 키 입력 수집/렌더링 및 엔터 시 콜백 실행"""

    def __init__(
        self,
        x: float,
        y: float,
        size: Tuple[int, int],
        event: Any,
        max_text_length: Optional[int] = None,
        center_pivot: bool = True,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.background: pygame.Surface = pygame.Surface(size, GAME_SURFACE_FLAGS)
        self.background.fill((255, 255, 255))
        self.center_pivot: bool = center_pivot
        self.font: Any = assets.Font.medium
        self.text: str = ""
        self.edit_pos: int = 0
        self.text_edit: bool = False
        self.text_editing: str = ""
        self.max_text_length: Optional[int] = max_text_length

        self.cursor_timer: TimeKeeper = TimeKeeper(duration=DEFAULT_CURSOR_BLINK_SEC)
        self.cursor: bool = True

        self.event: Any = event

        pygame.key.start_text_input()

    def handle_event(self, pygame_event: List[Any]) -> None:
        """키 입력 이벤트 처리: 백스페이스/엔터/TEXTEDITING/TEXTINPUT 등"""
        for event in pygame_event:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = (
                        self.text[: self.edit_pos - 1] + self.text[self.edit_pos :]
                    )
                    self.edit_pos = max(0, self.edit_pos - 1)
                if event.key == pygame.K_RETURN:
                    self.text_edit = False
                    pygame.key.stop_text_input()
                    self.event()

            elif event.type == pygame.TEXTEDITING:
                self.text_edit = True
                self.text_editing = event.text
                self.text_editing_pos = event.start
            elif event.type == pygame.TEXTINPUT:
                if (
                    self.max_text_length is None
                    or len(self.text) < self.max_text_length
                ):
                    self.text_edit = False
                    self.text_editing = ""
                    self.text = (
                        self.text[: self.edit_pos]
                        + event.text
                        + self.text[self.edit_pos :]
                    )
                    self.edit_pos = min(
                        self.edit_pos + len(event.text),
                        len(self.text + self.text_editing),
                    )

    def render(self) -> None:
        """배경/텍스트/커서 렌더링"""
        self.background.fill((255, 255, 255))

        if self.center_pivot:
            background_rect = self.background.get_rect(
                center=(
                    Screen.target_width / 2 + self.x,
                    Screen.target_height / 2 + self.y,
                )
            )
        else:
            background_rect = self.background.get_rect(
                topleft=(
                    Screen.target_width / 2 + self.x,
                    Screen.target_height / 2 + self.y,
                )
            )

        text_surface = str_to_surface(
            self.text + self.text_editing + " ", self.font, (0, 0, 0)
        )
        text_rect = text_surface.get_rect(
            midright=(background_rect.width, background_rect.height / 2)
        )

        if self.cursor_timer.is_finished():
            self.cursor = not self.cursor
            self.cursor_timer.reset()

        cursor_surface = str_to_surface("|", self.font, (0, 0, 0))
        cursor_rect = cursor_surface.get_rect(
            midright=(background_rect.width, background_rect.height / 2)
        )

        self.background.blit(text_surface, text_rect)
        if self.cursor:
            self.background.blit(cursor_surface, cursor_rect)

        Screen.game_surface.blit(self.background, background_rect)

    def update(self, pygame_event: List[Any]) -> None:
        """이벤트 처리 후 렌더링"""
        self.handle_event(pygame_event)
        self.render()


class Line:
    """대사(문장) 출력용 객체: 타이핑 효과와 엔터로 다음 라인 전환"""

    def __init__(
        self,
        x: float,
        y: float,
        speed: float,
        lines: List[str],
        center_pivot: bool = True,
        name: Optional[str] = None,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.center_pivot: bool = center_pivot

        self.speed: float = speed
        self.name: Optional[str] = name
        self.lines: List[str] = lines

        self.font: Any = assets.Font.medium
        self.active: bool = False
        self.completed: bool = False
        self.timer: Optional[TimeKeeper] = None

    def start(self) -> None:
        """대사 재생 시작"""
        if not self.active:
            self.active = True
            self.line_index: int = 0
            self.text_index: int = 0
            self.timer = TimeKeeper()

    def update(self, pygame_event: List[Any]) -> None:
        """현재 타이머/텍스트 인덱스 기준으로 텍스트를 점진 출력하고, 엔터로 다음 라인 전환"""
        if self.active:
            self.text_index = int(
                (self.timer.elapsed_time() // self.speed) if self.timer else 0
            )
            if self.text_index > len(self.lines[self.line_index]):
                for event in pygame_event:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.line_index += 1
                        self.text_index = 0
                        if self.timer:
                            self.timer.reset()

                if self.line_index >= len(self.lines):
                    self.active = False
                    self.completed = True
                    return

            text = self.lines[self.line_index][: self.text_index]
            self.text_surface = str_to_surface(text, self.font, (255, 255, 255))
            if self.center_pivot:
                self.text_rect = self.text_surface.get_rect(
                    center=(
                        Screen.target_width / 2 + self.x,
                        Screen.target_height / 2 + self.y,
                    )
                )
            else:
                self.text_rect = self.text_surface.get_rect(topleft=(self.x, self.y))

            Screen.game_surface.blit(self.text_surface, self.text_rect)
