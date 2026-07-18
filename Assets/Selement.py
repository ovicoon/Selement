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

# game_play.py
import os

# 작업 디렉터리 변경
os.chdir(os.path.dirname(__file__))

from modules import run_check

# 환경 검사 실행
run_check.run_checks()

import hashlib
import math
import time
import traceback
from typing import Optional

import pygame
from tkinter import messagebox

import requests

from modules import (
    utility,
    world,
    biome,
    assets,
    player,
    entities,
    graphic_effect,
    language,
)

# ==========================
# 상수 정의 (개발/게임 환경)
# ==========================
DEVELOP_MODE: bool = True
RENDER_COLLIDER: bool = False
VERSION: str = "1.4.0" if not DEVELOP_MODE else "dev"
LANGUAGE: language.Language = language.Language.ENGLISH

INTRO_SCENE_DURATION: float = 0.5 if DEVELOP_MODE else 2.0  # 인트로 씬 지속 시간
FPS_LIMIT: int = 60  # 초당 최대 프레임

# HP 바 관련 상수
HP_BAR_MAX_LENGTH: int = 512
HP_BAR_HEIGHT: int = 128

# worker 설정
WORKER_URL = "https://dragonheart.zerodragon.workers.dev"
MESSAGE_TO_DECOMPILER_READ_THIS: str = """
Hey there!
If you reverse-engineered this far, congrats on your skills!
Quick heads up:
- This API only accepts anonymous game statistics (play_time, endings, etc.) via POST
- Direct DB access is protected: You cannot UPDATE, DELETE, or manipulate other users' data
- Your 3+ hours of work vs my 5-minute database rollback = not worth it
But if you're a fellow dev who's curious or found a real bug:
Please reach out! I'd love to chat or add you to credits.
itch.io: https://ovicoon.itch.io
github: https://github.com/ovicoon
email: zerodragon.come159@passinbox.com
Thanks for playing Selement!
- Zero Dragon Team
    """

# 사용되지 않은 변수 방지
print(MESSAGE_TO_DECOMPILER_READ_THIS)


class Game:
    """
    Game 클래스 — 게임 전체 흐름을 제어하는 메인 컨트롤러.
    """

    def __init__(self) -> None:
        """게임과 씬, 카메라, 타이머 등 주요 객체 초기화"""
        # 유틸 초기화(화면/입력 등)
        utility.init()

        # 기본 상태값들
        self.running: bool = True
        self.username: str = ""

        # 언어 관리
        self.lang: language.LanguageManager = language.LanguageManager(LANGUAGE)

        # 씬 구성 초기화
        self._setup_scene()

        # 대사/스토리 관련 초기값
        self.current_line: Optional[utility.Line] = None
        self.last_line_completed: bool = False

        # 디버그 토글
        self.debug: bool = False

        # 카메라 및 화면 이펙트
        self.cam: utility.Camera = utility.Camera(0, 0)
        self.post_processor: graphic_effect.ScreenEffect = graphic_effect.ScreenEffect()
        self.set_scene(self.intro_scene)
        self.title_scene_timer: utility.TimeKeeper = utility.TimeKeeper(
            duration=INTRO_SCENE_DURATION
        )

        # 프레임 타이밍 용 클록 및 dt
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.dt: float = 0.0

        # 게임 월드 및 플레이어 관련 (게임 시작 전 None 가능)
        self.game_world: Optional[world.World] = None
        self.player_biome: Optional[biome.Biome] = None
        self.player_element_charge_timer: Optional[utility.TimeKeeper] = None
        self.hp_bar_surface: Optional[pygame.Surface] = None

        # 이전 프레임 상태 트래킹 변수들
        self.last_player_biome: Optional[biome.Biome] = None
        self.last_player_ended: bool = False
        self.last_player_alive: bool = True

        # 보스/암전 관련 상태
        self.boss_alive: bool = False
        self.last_boss_alive: bool = False
        self.last_darken_finished: bool = False

    # ----------------------
    # 씬 및 초기화 헬퍼
    # ----------------------
    def set_scene(self, scene: utility.Scene) -> None:
        """씬 전환을 중앙에서 처리"""
        self.active_scene: utility.Scene = scene

    def _setup_scene(self) -> None:
        """모든 씬 객체 생성 및 각 씬 초기 구성 호출"""
        self.active_scene = None
        self.intro_scene: utility.Scene = utility.Scene()
        self.language_scene: utility.Scene = utility.Scene()
        self.play_scene: utility.Scene = utility.Scene()
        self.title_scene: utility.Scene = utility.Scene()
        self.credit_scene: utility.Scene = utility.Scene()
        self.input_username: utility.Scene = utility.Scene()
        self.end_scene: utility.Scene = utility.Scene()
        self.key_scene: utility.Scene = utility.Scene()

        # 최소 씬 구성 메서드 호출
        self._setup_intro_scene()
        self._setup_language_scene()

    def _setup_all_scene(self) -> None:
        """나머지 모든 씬 구성 호출"""
        self._setup_title_scene()
        self._setup_credit_scene()
        self._setup_username_scene()
        self._setup_key_scene()

    def _setup_intro_scene(self) -> None:
        """인트로 로고 씬 구성"""
        self.intro_scene.ui.append(
            utility.OverLaySurface(0, 0, assets.Image.zero_dragon_logo)
        )

    def _setup_language_scene(self) -> None:
        """언어 선택 씬 구성"""
        self.language_scene.ui.append(
            utility.OverLaySurface(
                0,
                -400,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.SELECT_LANGUAGE)[0],
                    assets.Font.medium,
                    (255, 255, 255),
                ),
            )
        )
        # 영어 버튼
        self.language_scene.ui.append(
            utility.Button(
                0,
                -150,
                600,
                200,
                self.lang.get(language.TextKey.ENGLISH)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.set_language_english,
                assets.Font.medium,
            )
        )
        # 한국어 버튼
        self.language_scene.ui.append(
            utility.Button(
                0,
                150,
                600,
                200,
                self.lang.get(language.TextKey.KOREAN)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.set_language_korean,
                assets.Font.medium,
            )
        )

    def _setup_title_scene(self) -> None:
        """타이틀 씬 구성: 게임 로고, 타이틀 텍스트, 주요 버튼들"""
        self.title_scene.ui.append(
            utility.OverLaySurface(
                0,
                0,
                pygame.transform.scale(assets.Image.icon, (1920, 1920)),
            )
        )
        self.title_scene.ui.append(
            utility.OverLaySurface(
                0,
                -300,
                utility.str_to_surface("Selement", assets.Font.big, (255, 255, 255)),
            )
        )
        # 플레이 버튼
        self.title_scene.ui.append(
            utility.Button(
                0,
                0,
                600,
                200,
                self.lang.get(language.TextKey.PLAY)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.game_start,
                assets.Font.medium,
            )
        )

        # 우측 상단 버튼들: 종료 / 만든 이 / 조작법
        self.title_scene.ui.append(
            utility.Button(
                1820,
                980,
                100,
                100,
                self.lang.get(language.TextKey.EXIT)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.quit_game,
                assets.Font.small,
                center_pivot=False,
            )
        )
        self.title_scene.ui.append(
            utility.Button(
                1820,
                880,
                100,
                100,
                self.lang.get(language.TextKey.DEVELOPED_BY)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.show_credit,
                assets.Font.small,
                center_pivot=False,
            )
        )
        self.title_scene.ui.append(
            utility.Button(
                1820,
                780,
                100,
                100,
                self.lang.get(language.TextKey.CONTROLS)[0],
                (255, 255, 255),
                (100, 100, 100),
                self.show_keys,
                assets.Font.small,
                center_pivot=False,
            )
        )

    def _setup_credit_scene(self) -> None:
        """크레딧 씬 구성"""
        self.credit_scene.ui.append(
            utility.OverLaySurface(
                0,
                0,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.CREDIT)[0],
                    assets.Font.medium,
                    (255, 255, 255),
                ),
            )
        )
        self.credit_scene.ui.append(
            utility.OverLaySurface(
                0,
                0,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.ESC_TO_EXIT)[0],
                    assets.Font.small,
                    (255, 255, 255),
                ),
                center_pivot=False,
            )
        )

    def _setup_username_scene(self) -> None:
        """플레이어 이름 입력 씬 구성"""
        self.input_username.ui.append(
            utility.OverLaySurface(
                0,
                0,
                pygame.transform.scale(assets.Image.icon, (1920, 1920)),
            )
        )

        self.input_username.ui.append(
            utility.OverLaySurface(
                0,
                -300,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.INPUT_NAME)[0],
                    assets.Font.medium,
                    (255, 255, 255),
                ),
            )
        )

        self.input_username.ui.append(
            utility.InputField(0, 0, (500, 200), self.ready_to_play)
        )

    def _setup_key_scene(self) -> None:
        """조작법 안내 씬 구성"""
        self.key_scene.ui.append(
            utility.OverLaySurface(
                0,
                0,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.ESC_TO_EXIT)[0],
                    assets.Font.small,
                    (255, 255, 255),
                ),
                center_pivot=False,
            )
        )

        self.key_scene.ui.append(
            utility.OverLaySurface(
                0,
                100,
                utility.str_to_surface(
                    self.lang.get(language.TextKey.KEY_CONTROLS)[0],
                    assets.Font.medium,
                    (255, 255, 255),
                ),
                center_pivot=False,
            )
        )

    # ----------------------
    # 게임 기본 동작
    # ----------------------
    def quit_game(self) -> None:
        """게임 종료 플래그 설정"""
        self.running = False

    def create_debug_info(self, current_chunk: Optional[int]) -> str:
        """
        플레이어 상태 및 시스템 디버그 정보 문자열 반환.
        dt가 0일 경우 분모 보호 처리.
        에러 발생시 처리
        """
        speed: float = round(self.game_world.player.velocity.length() / self.dt, 1)
        try:
            if DEVELOP_MODE:
                debug_info = (
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[0]}: {math.floor(self.game_world.player.x)},{math.floor(self.game_world.player.y)}\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[1]}: {int(self.clock.get_fps())}\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[2]}: {self.game_world.get_tile_biome(self.game_world.player.x, self.game_world.player.y)}\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[3]}: {current_chunk}\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[4]}: {speed}\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[9]}: {self.game_world.player.defence}%\n"
                    f"{self.lang.get(language.TextKey.DEBUG_INFO)[10]}: {self.game_world.player.hp}/{self.game_world.player.max_hp}\n"
                )
            else:
                debug_info = f"{self.lang.get(language.TextKey.DEBUG_INFO)[1]}: {int(self.clock.get_fps())}\n"
        except Exception:
            debug_info = self.lang.get(language.TextKey.ERR_WHILE_DEBUG)[0]

        return debug_info

    def play_bgm(self) -> None:
        """플레이어 바이옴에 따라 알맞은 BGM 재생 (바이옴 변경 시 실행)"""
        if self.last_player_biome != self.player_biome:
            if self.player_biome == biome.Biome.fire:
                assets.Sound.fadein_music("Sounds/fire_burning.wav", 2000)
            elif self.player_biome == biome.Biome.water:
                assets.Sound.fadein_music("Sounds/underwater.flac", 2000)
            elif self.player_biome == biome.Biome.dirt:
                assets.Sound.fadein_music("Sounds/bird_singing.wav", 2000)
            elif self.player_biome == biome.Biome.air:
                assets.Sound.fadein_music("Sounds/wind_blowing.wav", 2000)
            elif self.player_biome == biome.Biome.fifth_biome:
                assets.Sound.pause_music()

    def show_keys(self) -> None:
        """키 안내 씬으로 전환"""
        self.set_scene(self.key_scene)

    def set_language_english(self) -> None:
        """언어를 영어로 설정하고 씬 구성 후 이름 입력 씬으로 전환"""
        self.lang.set_language(language.Language.ENGLISH)
        self._setup_all_scene()
        self.set_scene(self.input_username)

    def set_language_korean(self) -> None:
        """언어를 한국어로 설정하고 씬 구성 후 이름 입력 씬으로 전환"""
        self.lang.set_language(language.Language.KOREAN)
        self._setup_all_scene()
        self.set_scene(self.input_username)

    def game_start(self) -> None:
        """플레이 시작: username -> SHA256 -> numeric seed -> 월드 생성"""
        encoded_text: bytes = self.username.encode("utf-8")
        sha256 = hashlib.sha256()
        sha256.update(encoded_text)
        hex_hash: str = sha256.hexdigest()
        numeric_hash: int = int(hex_hash, 16)

        # 월드 생성 및 초기 상태 설정
        self.game_world = world.World(numeric_hash)
        self.player_biome = self.game_world.get_tile_biome(
            self.game_world.player.x, self.game_world.player.y
        )
        self.player_element_charge_timer = utility.TimeKeeper(duration=0)

        # 이전 프레임 데이터 초기화
        self.last_player_biome = None
        self.last_player_ended = self.game_world.player.ended

        # 플레이 씬으로 전환 및 초기 대사 설정
        self.set_scene(self.play_scene)
        self.current_line = utility.Line(
            0,
            300,
            0.1,
            self.lang.get(language.LineKey.INTRO, username=self.username),
            self.lang,
        )
        self.current_line.start()

    def show_credit(self) -> None:
        """크레딧 씬으로 전환"""
        self.set_scene(self.credit_scene)

    def ready_to_play(self) -> None:
        """이름 입력 완료 콜백: username 저장 후 타이틀 씬으로 이동"""
        self.set_scene(self.title_scene)
        for ui in self.input_username.ui:
            # type 체크
            if type(ui) == utility.InputField:
                self.username = ui.text

    # ----------------------
    # UI 렌더링 헬퍼
    # ----------------------
    def _append_element_ui(
        self,
        x_icon: int,
        y_icon: int,
        icon_surface: pygame.Surface,
        quantity: int,
    ) -> None:
        """원소 아이콘과 해당 수량 텍스트를 play_scene.ui에 추가하는 헬퍼"""
        copied = icon_surface.copy()
        copied.set_alpha(int(255 * (quantity / self.game_world.player.element_max)))
        self.play_scene.ui.append(
            utility.OverLaySurface(x_icon, y_icon, copied, center_pivot=False)
        )

    def show_ui(self) -> None:
        """플레이 씬 UI 구성 및 렌더링 준비"""
        # UI 초기화
        self.play_scene.ui.clear()

        # 플레이어 뷰 이미지
        self.play_scene.ui.append(
            utility.OverLaySurface(
                0,
                0,
                self.game_world.player.player_view_image,
            )
        )

        # 원소들 렌더링(아이콘 위치와 텍스트 위치를 헬퍼로 추가)
        self._append_element_ui(
            1600,
            412,
            assets.Image.fire_icon,
            self.game_world.player.fire,
        )
        self._append_element_ui(
            1600,
            540,
            assets.Image.water_icon,
            self.game_world.player.water,
        )
        self._append_element_ui(
            1600,
            668,
            assets.Image.dirt_icon,
            self.game_world.player.dirt,
        )
        self._append_element_ui(
            1600,
            796,
            assets.Image.air_icon,
            self.game_world.player.air,
        )

        # Selement는 존재할 때만 추가
        if self.game_world.player.selement > 0:
            self._append_element_ui(
                1600,
                924,
                assets.Image.selement_icon,
                100,
            )

        # 선택된 공격 타입에 따른 선택 아이콘 표시
        sel = self.game_world.player.selected_attack
        if sel == player.attack_type.fire:
            self.play_scene.ui.append(
                utility.OverLaySurface(
                    1600, 412, assets.Image.attack_select, center_pivot=False
                )
            )
        elif sel == player.attack_type.water:
            self.play_scene.ui.append(
                utility.OverLaySurface(
                    1600, 540, assets.Image.attack_select, center_pivot=False
                )
            )
        elif sel == player.attack_type.dirt:
            self.play_scene.ui.append(
                utility.OverLaySurface(
                    1600, 668, assets.Image.attack_select, center_pivot=False
                )
            )
        elif sel == player.attack_type.air:
            self.play_scene.ui.append(
                utility.OverLaySurface(
                    1600, 796, assets.Image.attack_select, center_pivot=False
                )
            )
        elif sel == player.attack_type.selement:
            self.play_scene.ui.append(
                utility.OverLaySurface(
                    1600, 924, assets.Image.attack_select, center_pivot=False
                )
            )

        # 대사/스토리 처리
        self.story()

        # 디버그 정보 표시
        if self.debug:
            if hasattr(self.game_world, "current_chunk"):
                debug_info = self.create_debug_info(self.game_world.current_chunk)
            else:
                debug_info = self.create_debug_info(None)

            self.play_scene.ui.append(
                utility.OverLaySurface(
                    0,
                    0,
                    utility.str_to_surface(
                        debug_info, assets.Font.small, (255, 255, 255)
                    ),
                    center_pivot=False,
                )
            )

    # ----------------------
    # 스토리 / 대사 처리
    # ----------------------
    def story(self) -> None:
        """스토리 진행 및 대사 처리 (보스 및 Selement 관련 트리거 포함)"""
        # 보스 바이옴 처리
        if self.player_biome == biome.Biome.fifth_biome:
            if self.last_player_biome != self.player_biome:
                self.boss_alive = True
                self.last_boss_alive = self.boss_alive
                if not DEVELOP_MODE:
                    self.current_line = utility.Line(
                        0,
                        300,
                        0.1,
                        self.lang.get(language.LineKey.BEFORE_BOSS),
                        self.lang,
                        name="before boss",
                    )
                else:
                    self.current_line = utility.Line(
                        0, 300, 0.1, ["before boss"], self.lang, name="before boss"
                    )

                self.current_line.start()

            for mob in self.game_world.mob:
                if type(mob) == entities.BossSelf:
                    self.boss_alive = mob.alive
                    self.boss_coord = (mob.x, mob.y)

            if not self.boss_alive:
                for mob in self.game_world.mob:
                    mob.hp = 0

                if self.last_boss_alive:
                    # 엔딩 노래 재생
                    assets.Sound.play_music("Sounds/ending_song.mp3")
                    if not DEVELOP_MODE:
                        self.current_line = utility.Line(
                            0,
                            300,
                            0.1,
                            self.lang.get(language.LineKey.AFTER_BOSS),
                            self.lang,
                            name="after boss",
                        )
                    else:
                        self.current_line = utility.Line(
                            0, 300, 0.1, ["after boss"], self.lang, name="after boss"
                        )
                    self.current_line.start()

            self.last_boss_alive = self.boss_alive

        # Selement 사용(엔딩 트리거) 처리
        if self.game_world.player.ended and self.game_world.player.alive:
            if not self.last_player_ended:
                self.post_processor.darken(3)
                self.last_darken_finished = False

            if self.post_processor.darken_timer:
                if (
                    self.post_processor.darken_timer.is_finished()
                    and not self.last_darken_finished
                ):
                    self.post_processor.remove_all_effect()
                    self.set_scene(self.end_scene)

                    if not DEVELOP_MODE:
                        if not self.game_world.player.easter_egg_ending:
                            self.current_line = utility.Line(
                                0,
                                0,
                                0.1,
                                self.lang.get(
                                    language.LineKey.NORMAL_ENDING,
                                    username=self.username,
                                ),
                                self.lang,
                                name="the end",
                            )
                        else:
                            self.current_line = utility.Line(
                                0,
                                0,
                                0.1,
                                self.lang.get(
                                    language.LineKey.EASTER_EGG_ENDING,
                                    username=self.username,
                                ),
                                self.lang,
                                name="the end",
                            )
                    else:
                        self.current_line = utility.Line(
                            0, 0, 0.1, ["The End"], self.lang, name="the end"
                        )

                    self.current_line.start()

        # 게임 오버 처리
        if self.game_world.player.alive == False and self.last_player_alive:
            self.post_processor.darken(3)
            self.last_darken_finished = False
            assets.Sound.fadeout_music(3000)

        if self.post_processor.darken_timer:
            if (
                self.post_processor.darken_timer.is_finished()
                and not self.last_darken_finished
            ):
                self.post_processor.remove_all_effect()
                self.set_scene(self.title_scene)
                self.current_line = None

        # 활성 대사 추가 및 완료 후 후속 처리
        if self.current_line:
            if self.current_line.active:
                self.active_scene.ui.append(self.current_line)
            if self.current_line.completed and not self.last_line_completed:
                if self.current_line.name == "before boss":
                    for mob in self.game_world.mob:
                        if type(mob) == entities.BossSelf:
                            mob.start = True

                    assets.Sound.play_music("Sounds/boss_bgm.mp3")

                if self.current_line.name == "after boss":
                    self.game_world.static_objects.append(
                        entities.InteractableEntity(
                            self.boss_coord[0],
                            self.boss_coord[1],
                            assets.Image.selement,
                            "selement",
                            32,
                        )
                    )

                if self.current_line.name == "the end":
                    self.quit_game()

            self.last_line_completed = self.current_line.completed
            self.last_player_ended = self.game_world.player.ended
            self.last_player_alive = self.game_world.player.alive

            if self.post_processor.darken_timer:
                self.last_darken_finished = (
                    self.post_processor.darken_timer.is_finished()
                )

    # ----------------------
    # 메인 루프
    # ----------------------
    def run(self) -> None:
        """메인 루프: 이벤트 처리, 월드/씬 업데이트, 렌더링"""
        while self.running:
            # 이벤트 폴링
            pygame_event = pygame.event.get()
            for event in pygame_event:
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F12 and DEVELOP_MODE:
                        # 디버그 토글 (F12)
                        self.debug = not self.debug
                    if event.key == pygame.K_ESCAPE:
                        # 크레딧/조작법 씬에서 esc를 누르면 타이틀로 복귀
                        if (
                            self.active_scene == self.credit_scene
                            or self.active_scene == self.key_scene
                        ):
                            self.set_scene(self.title_scene)

            # 델타 타임 업데이트
            self.dt = self.clock.tick(FPS_LIMIT) / 1000.0

            # 인트로 종료 시 이름 입력 씬으로 전환
            if (
                self.title_scene_timer.is_finished()
                and self.active_scene == self.intro_scene
            ):
                self.set_scene(self.language_scene)

            # 플레이 씬 로직
            if self.active_scene == self.play_scene:
                # 카메라 동기화
                self.cam = self.game_world.player.cam
                keys = pygame.key.get_pressed()

                # ending 플래그에 따라 룸 전환 처리
                if (
                    self.game_world.player.ending
                    and type(self.game_world) == world.World
                ):
                    self.game_world = world.Room(
                        4096,
                        4096,
                        assets.Image.fifth_biome_tile,
                        self.game_world.player,
                    )

                # 바이옴 갱신
                self.player_biome = self.game_world.get_tile_biome(
                    self.game_world.player.x,
                    self.game_world.player.y,
                )

                # 월드 업데이트 및 씬 동기화
                self.game_world.update(
                    self.dt, keys, pygame_event, self.active_scene.ui
                )
                self.play_scene.entities = self.game_world.entities
                self.play_scene.background = self.game_world.background

                # BGM 및 UI 업데이트
                self.play_bgm()

                self.post_processor.motion_blur = 1 - (
                    self.game_world.player.hp / self.game_world.player.max_hp
                )

                self.show_ui()

                # 바이옴 상태 저장
                self.last_player_biome = self.player_biome

            # 엔딩 씬 처리
            if self.active_scene == self.end_scene:
                self.end_scene.ui.clear()
                self.story()

            # 씬 렌더링
            if self.game_world != None:
                self.cam.render_scene(
                    self.active_scene,
                    pygame_event,
                    self.game_world.player.player_view,
                    render_collider=RENDER_COLLIDER,
                )
            else:
                self.cam.render_scene(
                    self.active_scene, pygame_event, utility.Screen.game_width
                )

            processed_game_surface = self.post_processor.post_process(
                utility.Screen.game_surface
            )

            # 화면 그리기 (스케일 후 중앙에 blit)
            render_surface = pygame.transform.scale(
                processed_game_surface,
                (utility.Screen.game_width, utility.Screen.game_height),
            )
            utility.Screen.screen.blit(
                render_surface, (utility.Screen.center_x, utility.Screen.center_y)
            )
            pygame.display.flip()

        # 정리
        pygame.quit()


# 게임 실행 진입점
if __name__ == "__main__":
    if DEVELOP_MODE:
        game = Game()
        game.run()
    else:
        try:
            start_time: int = time.time()
            game = Game()
            game.run()

            if (
                game.game_world is not None
                and hasattr(game.game_world, "player")
                and game.game_world.player is not None
            ):
                try:
                    play_time: int = int(time.time() - start_time)
                    data = {
                        "play_time": play_time,
                        "ending": game.game_world.player.ending,
                        "ended": game.game_world.player.ended,
                        "easter_egg_ending": game.game_world.player.easter_egg_ending,
                        "version": VERSION,
                    }
                    # Worker의 플레이 세션 엔드포인트로 POST 요청 전송
                    response = requests.post(
                        f"{WORKER_URL}/api/sessions", json=data, timeout=5
                    )
                except Exception:
                    print("데이터 전송 중 오류 발생")

        except Exception as e:
            messagebox.showerror(
                f"Error:{type(e).__name__}",
                f"{e}\nTraceBack:{traceback.format_exc()}\n",
            )
            try:
                data = {
                    "error_type": type(e).__name__,
                    "version": VERSION,
                }
                # Worker의 에러 로그 엔드포인트로 POST 요청 전송
                response = requests.post(
                    f"{WORKER_URL}/api/errors", json=data, timeout=5
                )
            except Exception:
                print("데이터 전송 중 오류 발생")
