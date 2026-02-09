# world.py
"""
월드(월드/룸) 생성·업데이트·렌더링을 담당하는 모듈.
"""
from __future__ import annotations

import math
import random
import sys
from typing import Dict, Iterable, List, Optional, Tuple

import pygame
from opensimplex import OpenSimplex
from tkinter import messagebox

# 직접 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import assets
    from . import biome
    from . import entities
    from . import graphic_effect
    from . import player
    from . import utility


# ===== 상수 정의 =====
# LOAD_CHUNK_SIZE 는 홀수만 의미가 있으므로, 아래에서 강제 보정한다.
LOAD_CHUNK_SIZE: int = 3
CHUNK_SIZE: int = 1024
TILE_SIZE: int = 128

GAME_TICK_INTERVAL: float = 0.1

OFFSET_MAX: int = 8192
BIOME_SIZE: int = 8192

MOB_SPAWN_MAX: int = 15
MOB_SPAWN_DISTANCE: Tuple[int, int] = (3000, 10000)  # (최소, 최대)
MOB_DESPAWN_DISTANCE: int = 20000

WORLD_SIZE: int = 1_000_000_000


def _ensure_odd(n: int) -> int:
    """짝수면 +1 해서 홀수로 보정."""
    return n if n % 2 else n + 1


def _ring_range(size_odd: int) -> range:
    """센터(0)를 기준으로 size_odd 크기의 정사각형 인덱스 범위를 반환."""
    half = size_odd // 2
    return range(-half, half + 1)


# ===== World =====
class World:
    """
    무한 월드를 청크 단위로 로드/언로드하며, 엔티티와 타일을 관리.

    생성자 인자:
        seed (int): 월드 시드.

    주요 속성:
        player (player.Player)         : 플레이어 인스턴스
        loaded_chunks (dict)           : {(chunk_x, chunk_y): Chunk}
        entities/background (list)     : 카메라가 그릴 오브젝트 버퍼
        mob/mob_attack/player_attack   : 몹/투사체 리스트
        noise generators               : temp/moist 노이즈
        animations                     : 타일/오브젝트 애니메이션
    """

    # ---- 초기화 ----
    def __init__(self, seed: int) -> None:
        self.seed: int = seed
        self.loaded_chunks: Dict[Tuple[int, int], Chunk] = {}

        # 노이즈 & 오프셋 시드
        random.seed(self.seed)
        self.offset1 = random.uniform(1, OFFSET_MAX) * random.choice([-1, 1])
        self.offset2 = random.uniform(1, OFFSET_MAX) * random.choice([-1, 1])
        self.offset3 = random.uniform(1, OFFSET_MAX) * random.choice([-1, 1])
        self.offset4 = random.uniform(1, OFFSET_MAX) * random.choice([-1, 1])

        self.temp_noise_generator = OpenSimplex(
            seed=random.randint(1, OFFSET_MAX) * random.choice([-1, 1])
        )
        self.moist_noise_generator = OpenSimplex(
            seed=random.randint(1, OFFSET_MAX) * random.choice([-1, 1])
        )

        # 플레이어 스폰
        self.spawn_x = random.randint(-OFFSET_MAX, OFFSET_MAX)
        self.spawn_y = random.randint(-OFFSET_MAX, OFFSET_MAX)
        self.player = player.Player(self.spawn_x, self.spawn_y)

        # 치수/스케일
        self.tile_size: int = TILE_SIZE
        self.chunk_size: int = CHUNK_SIZE
        self.biome_size: int = BIOME_SIZE
        self.width: int = WORLD_SIZE
        self.height: int = WORLD_SIZE

        # 렌더 버퍼 & 시스템 리스트
        self.entities: List[entities.Entity] = []
        self.background: List[Tile] = []
        self.mob: List[entities.Entity] = []
        self.mob_attack: List[entities.Projectile] = []
        self.player_attack: List[entities.Projectile] = []

        # 현재 청크/이전 청크
        self.current_chunk = self._to_chunk_center(self.player.x, self.player.y)
        self.last_chunk = self.current_chunk

        # 게임 틱 타이머
        self.game_tick_timer = utility.TimeKeeper(duration=GAME_TICK_INTERVAL)

        # 애니메이션
        self.water_animation = utility.Animation(assets.Image.water_frames, 2)
        self.fire_animation = utility.Animation(assets.Image.fire_frames, 2)
        self.blue_fire_animation = utility.Animation(assets.Image.blue_fire_frames, 2)
        self.strong_fire_animation = utility.Animation(
            assets.Image.strong_fire_frames, 4
        )
        self.seaweed_animation = utility.Animation(assets.Image.seaweed_frames, 2)

        # 파티클
        self.shooter = graphic_effect.ParticleShooter()

        # 초기 청크 로드
        self._load_chunks_around_player()

    # ---- 좌표/청크 ----
    def _to_chunk_center(self, x: float, y: float) -> Tuple[int, int]:
        """월드 좌표를 해당 청크의 중심 좌표로 스냅."""
        cx = math.floor(x / self.chunk_size) * self.chunk_size + self.chunk_size // 2
        cy = math.floor(y / self.chunk_size) * self.chunk_size + self.chunk_size // 2
        return cx, cy

    def _load_chunks_around_player(self) -> None:
        """플레이어 주변의 청크를 로드하고, 멀어진 청크는 언로드."""
        size = _ensure_odd(LOAD_CHUNK_SIZE)
        need: List[Tuple[int, int]] = []
        for i in _ring_range(size):
            for j in _ring_range(size):
                coord = self._to_chunk_center(
                    self.player.x + i * self.chunk_size,
                    self.player.y + j * self.chunk_size,
                )
                need.append(coord)

        # 언로드 대상
        to_remove = [c for c in self.loaded_chunks.keys() if c not in need]
        for c in to_remove:
            del self.loaded_chunks[c]

        # 신규 로드
        for coord in need:
            if coord not in self.loaded_chunks:
                self.loaded_chunks[coord] = Chunk(coord[0], coord[1], self)

    # ---- 렌더 준비(타일/엔티티) ----
    def _refresh_tiles(self) -> None:
        """타일 버퍼(self.background)를 구성."""
        self.background.clear()
        water_frame = self.water_animation.update()

        for chunk in self._iter_loaded_chunks():
            for tile in chunk.tiles:
                if self.player_biome != biome.Biome.water:
                    # 지상
                    if tile.biome == biome.Biome.dirt:
                        tile.image = assets.Image.dirt_tile
                    elif tile.biome == biome.Biome.fire:
                        tile.image = assets.Image.fire_tile
                    elif tile.biome == biome.Biome.air:
                        tile.image = assets.Image.air_tile
                    elif tile.biome == biome.Biome.water:
                        tile.image = water_frame
                else:
                    # 수중
                    if tile.biome == biome.Biome.water:
                        tile.image = assets.Image.underwater_tile
                    else:
                        tile.image = assets.Image.underwater_ground_tile

                self.background.append(tile)

    def _append_visible_entity(self, e: entities.Entity) -> None:
        """현재 플레이어 바이옴/수역 상태에 따라 표시 여부를 결정해 버퍼에 추가."""
        if self.player_biome == biome.Biome.water:
            # 수중: 물 속 엔티티만 보이게
            if biome.get_biome(self, e.x, e.y) == biome.Biome.water:
                self.entities.append(e)
        else:
            # 지상: 물 속 엔티티는 숨김
            if biome.get_biome(self, e.x, e.y) != biome.Biome.water:
                self.entities.append(e)

    def _refresh_entities(self, dt: float) -> None:
        """엔티티 버퍼(self.entities)를 구성."""
        self.entities.clear()

        # 몹 업데이트/필터
        dead_mobs: List[entities.Entity] = []
        for m in self.mob:
            if m.alive:
                m.update(self, dt)
                self._append_visible_entity(m)
            else:
                assets.Sound.kill_mob.play()
                dead_mobs.append(m)

        for m in dead_mobs:
            self.mob.remove(m)

        # 애니메이션 프레임
        fire_frame = self.fire_animation.update()
        blue_fire_frame = self.blue_fire_animation.update()
        strong_fire_frame = self.strong_fire_animation.update()
        seaweed_frame = self.seaweed_animation.update()

        # 월드 배치 엔티티
        for chunk in self._iter_loaded_chunks():
            for e in chunk.entities:
                if self.player_biome != biome.Biome.water:
                    # 지상: 수중 전용은 스킵
                    if e.name in {
                        "red_coral_reef",
                        "pink_coral_reef",
                        "yellow_coral_reef",
                        "seaweed",
                    }:
                        continue
                    if (
                        e.name == "portal"
                        and biome.get_biome(self, e.x, e.y) == biome.Biome.water
                    ):
                        continue

                    if e.name == "fire":
                        e.image = fire_frame
                    elif e.name == "strong_fire":
                        e.image = strong_fire_frame
                    elif e.name == "blue_fire":
                        e.image = blue_fire_frame

                    self.entities.append(e)

                else:
                    # 수중: 산호/해초/수중 포탈만 보임
                    if e.name in {
                        "red_coral_reef",
                        "pink_coral_reef",
                        "yellow_coral_reef",
                    }:
                        self.entities.append(e)
                    elif e.name == "seaweed":
                        e.image = seaweed_frame
                        self.entities.append(e)
                    elif (
                        e.name == "portal"
                        and biome.get_biome(self, e.x, e.y) == biome.Biome.water
                    ):
                        self.entities.append(e)

        # 플레이어 파티클
        if self.player.alive:
            self.shooter.shoot(
                self.player.x, self.player.y, (0, 100), 1, 1, assets.Image.smog, 1
            )
        self.shooter.update(dt)
        self.entities.extend(self.shooter.particles)

        # 몹 투사체
        self._update_projectiles(self.mob_attack, dt)

        # 플레이어 투사체
        self._update_projectiles(self.player_attack, dt)

    def _update_projectiles(
        self, proj_list: List[entities.Projectile], dt: float
    ) -> None:
        """투사체 리스트 업데이트 및 렌더 버퍼 반영."""
        to_remove: List[entities.Projectile] = []
        for p in proj_list:
            if p.alive:
                p.update(dt)
                self._append_visible_entity(p)
            else:
                to_remove.append(p)
        for p in to_remove:
            proj_list.remove(p)

    # ---- 프레임 업데이트 ----
    def update(self, dt: float, keys, pygame_event) -> None:
        """월드 한 프레임 업데이트."""
        # 청크 이동 감지 >> 로드/언로드
        self.current_chunk = self._to_chunk_center(self.player.x, self.player.y)
        if self.last_chunk != self.current_chunk:
            self._load_chunks_around_player()

        # 현재 플레이어 위치의 바이옴
        self.player_biome = biome.get_biome(self, self.player.x, self.player.y)

        # 게임 틱
        if self.game_tick_timer.is_finished():
            tick_count = int(
                self.game_tick_timer.elapsed_time() // self.game_tick_timer.duration
            )
            for _ in range(max(1, tick_count)):
                self._game_tick()
            self.game_tick_timer.reset()

        # 렌더 버퍼 구성
        self._refresh_tiles()
        self._refresh_entities(dt)

        # 다음 비교를 위해 저장
        self.last_chunk = self.current_chunk

        # 플레이어 업데이트 (입력/물리)
        self.player.update(self, keys, pygame_event, dt)

    # ---- 게임 틱 ----
    def _game_tick(self) -> None:
        """스폰/정리"""
        self._spawn_mob()

    def _spawn_mob(self) -> None:
        """플레이어 주변에 몹 스폰, 멀어진 몹 정리."""
        random.seed()

        # 멀어진 몹 제거
        far: List[entities.Entity] = []
        for m in self.mob:
            if (
                utility.distance(m.x, m.y, self.player.x, self.player.y)
                > MOB_DESPAWN_DISTANCE
            ):
                far.append(m)
        for m in far:
            self.mob.remove(m)

        # 스폰 한도 확인
        if len(self.mob) >= MOB_SPAWN_MAX:
            return

        # 스폰
        if random.random() > 0:
            dist = random.uniform(*MOB_SPAWN_DISTANCE)
            angle = random.uniform(0.0, 360.0)
            pos = pygame.math.Vector2(
                self.player.x + (dist * math.cos(math.radians(angle))),
                self.player.y + (dist * math.sin(math.radians(angle))),
            )
            b = biome.get_biome(self, pos.x, pos.y)
            if b == biome.Biome.fire:
                self.mob.append(entities.Burster(pos.x, pos.y))
            elif b == biome.Biome.water:
                self.mob.append(entities.Biter(pos.x, pos.y))
            elif b == biome.Biome.air:
                self.mob.append(entities.Flutterer(pos.x, pos.y))
            elif b == biome.Biome.dirt:
                self.mob.append(entities.Plower(pos.x, pos.y))

    # ---- 유틸 ----
    def _iter_loaded_chunks(self) -> Iterable[Chunk]:
        """로드된 청크 이터레이터."""
        return self.loaded_chunks.values()


# ===== Chunk =====
class Chunk:
    """
    청크는 고정 크기(CHUNK_SIZE) 영역의 타일과 정적 엔티티를 포함한다.
    생성 시 내부적으로 타일/엔티티를 절차적으로 배치한다.
    """

    def __init__(self, x: int, y: int, world: World) -> None:
        self.x = x
        self.y = y
        self.world = world

        self.entities: List[entities.Entity] = []
        self.tiles: List[Tile] = []

        # 타일 생성
        tiles_per_axis = self.world.chunk_size // self.world.tile_size
        half = tiles_per_axis // 2
        for i in range(-half, half):
            for j in range(-half, half):
                tx = self.x + i * self.world.tile_size + self.world.tile_size // 2
                ty = self.y + j * self.world.tile_size + self.world.tile_size // 2
                tb = biome.get_biome(self.world, tx, ty)

                # water 는 애니메이션 프레임이므로 이미지 즉시 할당하지 않음
                if tb == biome.Biome.dirt:
                    img = assets.Image.dirt_tile
                elif tb == biome.Biome.fire:
                    img = assets.Image.fire_tile
                elif tb == biome.Biome.air:
                    img = assets.Image.air_tile
                elif tb == biome.Biome.water:
                    img = None
                else:
                    img = None

                self.tiles.append(Tile(tx, ty, img, tb))

        # 정적 엔티티 생성
        self._generate()

    def _generate(self) -> None:
        """청크 내부에 자연물/불꽃/산호 등 엔티티를 배치."""
        random.seed(f"SelementWorldSeed{self.world.seed}chunk{self.x}_{self.y}")

        # 풀/해초
        for _ in range(self.world.tile_size):
            if random.random() > 0.2:
                ox = self.x + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                oy = self.y + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                ob = biome.get_biome(self.world, ox, oy)
                if ob == biome.Biome.dirt:
                    grass_img, grass_name = random.choice(
                        [
                            (assets.Image.grass, "grass"),
                            (assets.Image.dry_grass, "dry_grass"),
                        ]
                    )
                    self.entities.append(entities.Entity(ox, oy, grass_img, grass_name))
                elif ob == biome.Biome.water:
                    # 해초는 애니메이션 프레임이므로 이미지 None
                    self.entities.append(entities.Entity(ox, oy, None, "seaweed"))

        # 나무 & 불꽃 & 산호
        for _ in range(32):
            # 나무
            if random.random() > 0.5:
                ox = self.x + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                oy = self.y + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                ob = biome.get_biome(self.world, ox, oy)
                if ob == biome.Biome.dirt:
                    tree_img, tree_name = random.choice(
                        [
                            (assets.Image.oak_tree, "oak_tree"),
                            (assets.Image.birch_tree, "birch_tree"),
                            (assets.Image.acacia_tree, "acacia_tree"),
                            (assets.Image.jungle_tree, "jungle_tree"),
                        ]
                    )
                    self.entities.append(entities.Entity(ox, oy, tree_img, tree_name))

            # 불꽃
            if random.random() > 0.3:
                ox = self.x + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                oy = self.y + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                ob = biome.get_biome(self.world, ox, oy)
                if ob == biome.Biome.fire:
                    # 푸른 불꽃은 저확률
                    if random.random() > 0.001:
                        fire = random.choice([(None, "fire"), (None, "strong_fire")])
                    else:
                        fire = (None, "blue_fire")
                    self.entities.append(entities.Entity(ox, oy, fire[0], fire[1]))

            # 산호
            if random.random() > 0.6:
                ox = self.x + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                oy = self.y + random.randint(
                    -self.world.chunk_size // 2, self.world.chunk_size // 2
                )
                ob = biome.get_biome(self.world, ox, oy)
                if ob == biome.Biome.water:
                    coral_img, coral_name = random.choice(
                        [
                            (assets.Image.red_coral_reef, "red_coral_reef"),
                            (assets.Image.pink_coral_reef, "pink_coral_reef"),
                            (assets.Image.yellow_coral_reef, "yellow_coral_reef"),
                        ]
                    )
                    self.entities.append(entities.Entity(ox, oy, coral_img, coral_name))

        # 포탈 (희박)
        if random.random() > 0.99:
            ox = self.x + random.randint(
                -self.world.chunk_size // 2, self.world.chunk_size // 2
            )
            oy = self.y + random.randint(
                -self.world.chunk_size // 2, self.world.chunk_size // 2
            )
            self.entities.append(
                entities.InteractableEntity(ox, oy, assets.Image.portal, "portal", 32)
            )


# ===== Tile =====
class Tile(entities.Entity):
    """타일 엔터티(간단한 데이터 캐리어)."""

    def __init__(
        self, x: int, y: int, image: Optional[pygame.Surface], biome_type: biome.Biome
    ):
        self.x = x
        self.y = y
        self.image: Optional[pygame.Surface] = image
        self.biome = biome_type  # biome.Biome


# ===== Room (고정 맵) =====
class Room(World):
    """
    Room 은 한 번에 모두 로드되는 고정 크기 맵.
    너무 크게 만들면 성능 저하가 있을 수 있다.
    """

    def __init__(
        self,
        width: int,
        height: int,
        tile_image: pygame.Surface,
        player_data: player.Player,
    ):
        # Room 은 World 와 인터페이스를 공유하지만 월드 스케일/청크가 없다.
        self.width = width
        self.height = height

        self.background: List[Tile] = []
        self.entities: List[entities.Entity] = []
        self.static_objects: List[entities.Entity] = []
        self.mob: List[entities.Entity] = []
        self.mob_attack: List[entities.Projectile] = []
        self.player_attack: List[entities.Projectile] = []

        self.player = player_data
        self.player.x = 0
        self.player.y = 400
        self.player_biome: Optional[biome.Biome] = None

        self.shooter = graphic_effect.ParticleShooter()

        self.tile_size = TILE_SIZE
        tiles_x = self.width // self.tile_size
        tiles_y = self.height // self.tile_size
        for i in range(-(tiles_x // 2), tiles_x // 2):
            for j in range(-(tiles_y // 2), tiles_y // 2):
                self.background.append(
                    Tile(
                        self.tile_size * i + self.tile_size // 2,
                        self.tile_size * j + self.tile_size // 2,
                        tile_image,
                        None,  # Room 은 바이옴이 고정 맵 컨셉이므로 None 허용
                    )
                )

        # 보스 배치
        self.mob.append(entities.BossSelf(0, 0))

    def update(self, dt: float, keys, pygame_event) -> None:
        self.entities.clear()

        self.player_biome = biome.get_biome(self, self.player.x, self.player.y)

        self._render_entities_room(dt)

        self.player.update(self, keys, pygame_event, dt)

    # Room 전용 엔티티 렌더 버퍼 구성
    def _render_entities_room(self, dt: float) -> None:
        # 플레이어 파티클
        if self.player.alive:
            self.shooter.shoot(
                self.player.x, self.player.y, (0, 100), 1, 1, assets.Image.smog, 1
            )
        self.shooter.update(dt)
        self.entities.extend(self.shooter.particles)

        # 몹
        dead_mobs: List[entities.Entity] = []
        for m in self.mob:
            if m.alive:
                m.update(self, dt)
                if self.player_biome == biome.Biome.water:
                    if biome.get_biome(self, m.x, m.y) == biome.Biome.water:
                        self.entities.append(m)
                else:
                    if biome.get_biome(self, m.x, m.y) != biome.Biome.water:
                        self.entities.append(m)
            else:
                dead_mobs.append(m)
        for m in dead_mobs:
            self.mob.remove(m)

        # 몹 투사체
        self._update_projectiles(self.mob_attack, dt)
        # 플레이어 투사체
        self._update_projectiles(self.player_attack, dt)

        # 정적 오브젝트
        self.entities.extend(self.static_objects)
