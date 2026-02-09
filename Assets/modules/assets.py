# assets.py
"""
에셋 로더 모듈 (이미지/폰트/사운드)
"""

from typing import List, Optional, Tuple
import pygame
import pygame.freetype
import sys
from tkinter import messagebox

# 단독 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()


# ---------------------------
# 이미지/폰트/사운드 로드 상수
# ---------------------------
FONT_PATH: str = "ExternalAssets/font.ttf"
FONT_SMALL_SIZE: int = 30
FONT_MEDIUM_SIZE: int = 100
FONT_BIG_SIZE: int = 300

ANIM_FRAME_SIZE: Tuple[int, int] = (256, 256)
ENTITY_SIZE: Tuple[int, int] = (256, 256)
TILE_SIZE: Tuple[int, int] = (128, 128)
BOSS_SMOG_SIZE: Tuple[int, int] = (64, 64)
PARTICLE_SIZE: Tuple[int, int] = (64, 64)
ICON_SIZE: Tuple[int, int] = (128, 128)
HP_SCREEN_SIZE: Tuple[int, int] = (1920, 1080)


class Font:
    """폰트 로더 및 보관(정적 접근)"""

    small: Optional[pygame.font.Font] = None
    medium: Optional[pygame.font.Font] = None
    big: Optional[pygame.font.Font] = None

    @staticmethod
    def load() -> None:
        """폰트 파일을 불러와 클래스 속성에 저장합니다."""
        Font.small = pygame.freetype.Font(FONT_PATH, FONT_SMALL_SIZE)
        Font.medium = pygame.freetype.Font(FONT_PATH, FONT_MEDIUM_SIZE)
        Font.big = pygame.freetype.Font(FONT_PATH, FONT_BIG_SIZE)


class Image:
    """
    이미지 및 애니메이션 프레임을 정적으로 보관하는 클래스.
    사용 전 Image.load()를 호출하여 모든 에셋을 메모리에 올려야 합니다.
    """

    # static image references (초기값 None 유지)
    oak_tree: Optional[pygame.Surface] = None
    birch_tree: Optional[pygame.Surface] = None
    acacia_tree: Optional[pygame.Surface] = None
    jungle_tree: Optional[pygame.Surface] = None
    grass: Optional[pygame.Surface] = None
    dry_grass: Optional[pygame.Surface] = None
    red_coral_reef: Optional[pygame.Surface] = None
    pink_coral_reef: Optional[pygame.Surface] = None
    yellow_coral_reef: Optional[pygame.Surface] = None

    portal: Optional[pygame.Surface] = None

    burster: Optional[pygame.Surface] = None
    biter: Optional[pygame.Surface] = None
    plower: Optional[pygame.Surface] = None
    flutterer: Optional[pygame.Surface] = None
    boss_smog: Optional[pygame.Surface] = None

    dirt_tile: Optional[pygame.Surface] = None
    fire_tile: Optional[pygame.Surface] = None
    air_tile: Optional[pygame.Surface] = None
    underwater_tile: Optional[pygame.Surface] = None
    underwater_ground_tile: Optional[pygame.Surface] = None
    fifth_biome_tile: Optional[pygame.Surface] = None

    zero_dragon_logo: Optional[pygame.Surface] = None
    icon: Optional[pygame.Surface] = None
    player_view: Optional[pygame.Surface] = None
    hp_bar: Optional[pygame.Surface] = None
    hp_frame: Optional[pygame.Surface] = None

    smog: Optional[pygame.Surface] = None
    hit_particle: Optional[pygame.Surface] = None
    recovery_particle: Optional[pygame.Surface] = None
    light: Optional[pygame.Surface] = None

    fire_ball_image: Optional[pygame.Surface] = None
    magma_arrow: Optional[pygame.Surface] = None
    shield: Optional[pygame.Surface] = None
    super_shield: Optional[pygame.Surface] = None
    shock_wave: Optional[pygame.Surface] = None
    boss_wave: Optional[pygame.Surface] = None
    boss_projectile: Optional[pygame.Surface] = None

    dead_screen: Optional[pygame.Surface] = None
    dark_screen: Optional[pygame.Surface] = None

    circle: Optional[pygame.Surface] = None

    fire_icon: Optional[pygame.Surface] = None
    water_icon: Optional[pygame.Surface] = None
    dirt_icon: Optional[pygame.Surface] = None
    air_icon: Optional[pygame.Surface] = None
    selement_icon: Optional[pygame.Surface] = None
    attack_select: Optional[pygame.Surface] = None

    selement: Optional[pygame.Surface] = None

    # 애니메이션 프레임 리스트 초기화
    water_frames: List[pygame.Surface] = []
    fire_frames: List[pygame.Surface] = []
    strong_fire_frames: List[pygame.Surface] = []
    blue_fire_frames: List[pygame.Surface] = []
    seaweed_frames: List[pygame.Surface] = []

    biter_attack_frames: List[pygame.Surface] = []
    burster_attack_frames: List[pygame.Surface] = []
    plower_attack_frames: List[pygame.Surface] = []
    flutterer_attack_frames: List[pygame.Surface] = []

    @staticmethod
    def load_animation_frames(name: str, frame_count: int) -> List[pygame.Surface]:
        """
        애니메이션 프레임을 파일에서 읽어와 정해진 크기로 스케일한 리스트를 반환합니다.
        파일 경로는 Images/{name}{index}.png 형식입니다.
        """
        frames: List[pygame.Surface] = []
        for i in range(frame_count):
            frame = pygame.transform.scale(
                pygame.image.load(f"Images/{name}{i}.png").convert_alpha(),
                ANIM_FRAME_SIZE,
            )
            frames.append(frame)
        return frames

    @staticmethod
    def load() -> None:
        """
        프로젝트에서 사용하는 모든 이미지 에셋을 로드하여 클래스 속성에 저장합니다.
        * 이 함수는 pygame 초기화 이후에 호출되어야 합니다.
        """
        # 아이콘 설정 (창 아이콘)
        Image.icon = pygame.image.load("Images/icon.jpeg").convert_alpha()
        pygame.display.set_icon(Image.icon)

        # 나무
        Image.oak_tree = pygame.transform.scale(
            pygame.image.load("Images/oak_tree.png").convert_alpha(), ENTITY_SIZE
        )
        Image.birch_tree = pygame.transform.scale(
            pygame.image.load("Images/birch_tree.png").convert_alpha(), ENTITY_SIZE
        )
        Image.acacia_tree = pygame.transform.scale(
            pygame.image.load("Images/acacia_tree.png").convert_alpha(), ENTITY_SIZE
        )
        Image.jungle_tree = pygame.transform.scale(
            pygame.image.load("Images/jungle_tree.png").convert_alpha(), ENTITY_SIZE
        )

        # 풀 / 산호초
        Image.grass = pygame.transform.scale(
            pygame.image.load("Images/grass.png").convert_alpha(), ENTITY_SIZE
        )
        Image.dry_grass = pygame.transform.scale(
            pygame.image.load("Images/dry_grass.png").convert_alpha(), ENTITY_SIZE
        )

        Image.red_coral_reef = pygame.transform.scale(
            pygame.image.load("Images/red_coral_reef.png").convert_alpha(), ENTITY_SIZE
        )
        Image.pink_coral_reef = pygame.transform.scale(
            pygame.image.load("Images/pink_coral_reef.png").convert_alpha(), ENTITY_SIZE
        )
        Image.yellow_coral_reef = pygame.transform.scale(
            pygame.image.load("Images/yellow_coral_reef.png").convert_alpha(),
            ENTITY_SIZE,
        )

        # 포탈
        Image.portal = pygame.transform.scale(
            pygame.image.load("Images/portal.png").convert_alpha(), ENTITY_SIZE
        )

        # 타일
        Image.dirt_tile = pygame.transform.scale(
            pygame.image.load("Images/dirt_tile.png").convert_alpha(), TILE_SIZE
        )
        Image.fire_tile = pygame.transform.scale(
            pygame.image.load("Images/fire_tile.png").convert_alpha(), TILE_SIZE
        )
        Image.air_tile = pygame.transform.scale(
            pygame.image.load("Images/air_tile.png").convert_alpha(), TILE_SIZE
        )
        Image.underwater_tile = pygame.transform.scale(
            pygame.image.load("Images/underwater_tile.png").convert_alpha(), TILE_SIZE
        )
        Image.underwater_ground_tile = pygame.transform.scale(
            pygame.image.load("Images/underwater_ground_tile.png").convert_alpha(),
            TILE_SIZE,
        )
        Image.fifth_biome_tile = pygame.transform.scale(
            pygame.image.load("Images/fifth_biome_tile.png").convert_alpha(), TILE_SIZE
        )

        # 몹 / 보스
        Image.burster = pygame.transform.scale(
            pygame.image.load("Images/burster_normal.png").convert_alpha(), ENTITY_SIZE
        )
        Image.biter = pygame.transform.scale(
            pygame.image.load("Images/biter_normal.png").convert_alpha(), ENTITY_SIZE
        )
        Image.plower = pygame.transform.scale(
            pygame.image.load("Images/plower_normal.png").convert_alpha(), ENTITY_SIZE
        )
        Image.flutterer = pygame.transform.scale(
            pygame.image.load("Images/flutterer_normal.png").convert_alpha(),
            ENTITY_SIZE,
        )
        Image.boss_smog = pygame.transform.scale(
            pygame.image.load("Images/boss_smog.png").convert_alpha(), BOSS_SMOG_SIZE
        )

        # 로고 / HP UI
        Image.zero_dragon_logo = pygame.transform.scale(
            pygame.image.load("Images/Zero Dragon.png").convert_alpha(), (512, 512)
        )
        Image.hp_frame = pygame.image.load("Images/hp_frame.png").convert_alpha()
        Image.hp_bar = pygame.image.load("Images/hp_bar.png").convert_alpha()

        # 파티클
        Image.recovery_particle = pygame.transform.scale(
            pygame.image.load("Images/recovery_particle.png").convert_alpha(),
            PARTICLE_SIZE,
        )
        Image.smog = pygame.transform.scale(
            pygame.image.load("Images/smog.png").convert_alpha(), PARTICLE_SIZE
        )
        Image.hit_particle = pygame.transform.scale(
            pygame.image.load("Images/hit_particle.png").convert_alpha(), PARTICLE_SIZE
        )
        Image.light = pygame.transform.scale(
            pygame.image.load("Images/light.png").convert_alpha(), PARTICLE_SIZE
        )

        # 투사체 / 효과
        Image.fire_ball_image = pygame.transform.scale(
            pygame.image.load("Images/fire_ball.png").convert_alpha(), (128, 128)
        )
        Image.magma_arrow = pygame.transform.scale(
            pygame.image.load("Images/magma_arrow.png").convert_alpha(), (256, 256)
        )
        Image.shield = pygame.transform.scale(
            pygame.image.load("Images/shield.png").convert_alpha(), (256, 256)
        )
        Image.super_shield = pygame.transform.scale(
            pygame.image.load("Images/super_shield.png").convert_alpha(), (256, 256)
        )
        Image.shock_wave = pygame.image.load("Images/shock_wave.png").convert_alpha()
        Image.boss_wave = pygame.image.load("Images/boss_wave.png").convert_alpha()
        Image.boss_projectile = pygame.transform.scale(
            pygame.image.load("Images/boss_projectile.png").convert_alpha(), (128, 128)
        )

        # 화면 효과
        Image.dead_screen = pygame.transform.scale(
            pygame.image.load("Images/dead_screen.png").convert_alpha(), HP_SCREEN_SIZE
        )
        Image.dark_screen = pygame.transform.scale(
            pygame.image.load("Images/dark_screen.png").convert_alpha(), HP_SCREEN_SIZE
        )

        # circle (collider 시각화 등)
        Image.circle = pygame.image.load("Images/circle.png").convert_alpha()

        # 아이콘
        Image.fire_icon = pygame.transform.scale(
            pygame.image.load("Images/fire_icon.png").convert_alpha(), ICON_SIZE
        )
        Image.water_icon = pygame.transform.scale(
            pygame.image.load("Images/water_icon.png").convert_alpha(), ICON_SIZE
        )
        Image.air_icon = pygame.transform.scale(
            pygame.image.load("Images/air_icon.png").convert_alpha(), ICON_SIZE
        )
        Image.dirt_icon = pygame.transform.scale(
            pygame.image.load("Images/dirt_icon.png").convert_alpha(), ICON_SIZE
        )
        Image.selement_icon = pygame.transform.scale(
            pygame.image.load("Images/selement_icon.png").convert_alpha(), ICON_SIZE
        )
        Image.attack_select = pygame.transform.scale(
            pygame.image.load("Images/attack_select.png").convert_alpha(), ICON_SIZE
        )

        # 플레이어 뷰(원본 이미지는 저장만 하고 필요 시 스케일)
        Image.player_view = pygame.image.load("Images/player_view.png").convert_alpha()

        Image.selement = pygame.transform.scale(
            pygame.image.load("Images/selement.png").convert_alpha(), ENTITY_SIZE
        )

        # 애니메이션 프레임 로드 (기본 프레임 리스트 생성)
        Image.fire_frames = Image.load_animation_frames("fire", 2)
        Image.strong_fire_frames = Image.load_animation_frames("strong_fire", 2)
        Image.blue_fire_frames = Image.load_animation_frames("blue_fire", 2)

        Image.seaweed_frames = Image.load_animation_frames("seaweed", 4)

        Image.biter_attack_frames = Image.load_animation_frames("biter_attack", 2)
        Image.burster_attack_frames = Image.load_animation_frames("burster_attack", 2)
        Image.plower_attack_frames = Image.load_animation_frames("plower_attack", 2)
        Image.flutterer_attack_frames = Image.load_animation_frames(
            "flutterer_attack", 2
        )

        # water tile frames
        for i in range(2):
            Image.water_frames.append(
                pygame.transform.scale(
                    pygame.image.load(f"Images/water_tile{i}.png").convert_alpha(),
                    TILE_SIZE,
                )
            )


class Sound:
    """
    사운드 효과 및 배경 음악 로더/플레이어
    - Sound.load()를 호출하여 효과음들을 미리 로드
    - play_music(path)으로 배경음 재생
    """

    button: Optional[pygame.mixer.Sound] = None
    player_hit: Optional[pygame.mixer.Sound] = None
    game_over: Optional[pygame.mixer.Sound] = None
    skill_use: Optional[pygame.mixer.Sound] = None
    projectile_shoot: Optional[pygame.mixer.Sound] = None
    projectile_hit: Optional[pygame.mixer.Sound] = None
    portal_enter: Optional[pygame.mixer.Sound] = None
    earn_selement: Optional[pygame.mixer.Sound] = None
    kill_mob: Optional[pygame.mixer.Sound] = None

    @staticmethod
    def load() -> None:
        """사운드 파일들을 로드하여 클래스 속성에 할당합니다."""
        Sound.button = pygame.mixer.Sound("Sounds/button_click.wav")
        Sound.player_hit = pygame.mixer.Sound("Sounds/player_hit.wav")
        Sound.game_over = pygame.mixer.Sound("Sounds/game_over.wav")
        Sound.skill_use = pygame.mixer.Sound("Sounds/skill.wav")
        Sound.projectile_shoot = pygame.mixer.Sound("Sounds/projectile_shoot.flac")
        Sound.projectile_hit = pygame.mixer.Sound("Sounds/mob_hit.wav")
        Sound.portal_enter = pygame.mixer.Sound("Sounds/portal_enter.mp3")
        Sound.earn_selement = pygame.mixer.Sound("Sounds/earn_selement.ogg")
        Sound.kill_mob = pygame.mixer.Sound("Sounds/kill_mob.wav")

    @staticmethod
    def play_music(music_path: str) -> None:
        """주어진 음악 파일을 반복 재생합니다."""
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(loops=-1)

    @staticmethod
    def pause_music() -> None:
        """현재 재생 중인 배경 음악을 일시 정지합니다."""
        pygame.mixer.music.pause()

    @staticmethod
    def fadein_music(music_path: str, duration_ms: int) -> None:
        """배경 음악을 지정된 시간(ms) 동안 페이드인하여 재생합니다."""
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(loops=-1, fade_ms=duration_ms)

    @staticmethod
    def fadeout_music(duration_ms: int) -> None:
        """배경 음악을 지정된 시간(ms) 동안 페이드아웃하여 정지합니다."""
        pygame.mixer.music.fadeout(duration_ms)
