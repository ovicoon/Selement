# entities.py
"""
엔티티 정의 모듈
"""

from enum import Enum
import pygame
from tkinter import messagebox
import sys
import random
import math
from typing import Tuple, Optional, Any, List

if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import utility
    from . import biome
    from . import assets

DEFAULT_COLLIDER_RADIUS: int = 32
BOSS_MINION_OFFSET: int = 200


class Entity:
    """
    월드에 렌더링 되는 기본 엔티티.

    역할:
      - 위치(x,y), 이미지, 이름, 피벗 등 기본 속성 보유
      - 간단한 데이터 컨테이너 역할
    """

    def __init__(
        self,
        x: float,
        y: float,
        image: Optional[pygame.Surface],
        name: str,
        center_pivot: bool = False,
        do_not_arrange: bool = False,
    ) -> None:
        # 위치 및 시각적 표현
        self.x: float = x
        self.y: float = y
        self.image: Optional[pygame.Surface] = image

        # 식별자 / 배치 관련 플래그
        self.name: str = name
        self.center_pivot: bool = center_pivot
        self.do_not_arrange: bool = do_not_arrange


class MobState(Enum):
    """몹 상태 머신의 상태 정의"""

    idle = 0
    chase = 1
    attack_startup = 2
    attack_execute = 3
    attack_recovery = 4
    attack_again = 5


class Mob(Entity):
    """
    기본 몹 클래스

    주된 책임:
      - 플레이어 감지/추격/공격 상태 머신 처리
      - 콜라이더 및 HP 관리
      - 애니메이션 결과를 이미지로 반영
    """

    def __init__(
        self,
        x: float,
        y: float,
        name: str,
        image: Optional[pygame.Surface],
        view: float,
        speeds: Tuple[float, float, float],
        hp: float,
        attack_distance: Optional[float],
        attack_startup: float,
        attack_recovery: float,
        attack_animation: Any = None,
        move_while_attack: bool = False,
    ) -> None:
        super().__init__(x, y, image, name)

        # 원본 이미지 보관(애니메이션 실패 시 복구용)
        self.original_image: Optional[pygame.Surface] = image

        # 감지/속도/체력 관련
        self.view: float = view
        self.attack_distance: Optional[float] = attack_distance
        self.speeds: Tuple[float, float, float] = speeds
        self.speed: float = speeds[0] if speeds else 0.0
        self.hp: float = hp

        # 콜라이더 초기화: 이미지 기반 또는 반지름 기반
        if self.image:
            self.collider: utility.Collider = utility.Collider(
                self.x, self.y, self.image
            )
        else:
            self.collider: utility.Collider = utility.Collider(
                self.x, self.y, DEFAULT_COLLIDER_RADIUS
            )

        # 공격 관련 파라메터
        self.attack_startup: float = attack_startup
        self.attack_recovery: float = attack_recovery
        self.attack_animation: Any = attack_animation
        self.move_while_attack: bool = move_while_attack

        # 내부 타이머들
        self.attack_startup_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)
        self.attack_recovery_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)

        # 상태 추적
        self.detect_player: bool = False
        self.attack_possible: bool = False
        self.state: MobState = MobState.idle
        self.last_state: MobState = self.state
        self.alive: bool = True

    def get_damage(self, damage: float) -> None:
        """데미지를 적용한다. HP는 음수로 떨어지지 않도록 처리."""
        if self.alive:
            self.hp -= int(damage)
            assets.Sound.projectile_hit.play()

        if self.hp < 0:
            self.hp = 0

    def update(self, world: Any, dt: float) -> None:
        """
        몹 상태 업데이트 및 행동 처리.
        - 플레이어와의 거리 계산
        - 상태 전이(감지/공격/추격)
        - 이동, 콜라이더/애니메이션 업데이트
        """
        # 플레이어와의 거리 계산
        player_distance: float = utility.distance(
            self.x, self.y, world.player.x, world.player.y
        )
        self.detect_player = player_distance < self.view
        self.attack_possible = (
            player_distance < self.attack_distance
            if self.attack_distance is not None
            else False
        )

        # ---------- 상태 전이 로직 ----------
        if world.player.alive:
            # 감지 후 공격 준비 상태 진입
            if self.last_state in (MobState.idle, MobState.chase):
                if self.detect_player and self.attack_possible:
                    self.state = MobState.attack_startup
                    self.attack_startup_timer = utility.TimeKeeper(
                        duration=self.attack_startup
                    )

            # attack_again -> attack_startup 전환 처리
            if self.state == MobState.attack_again:
                self.state = MobState.attack_startup
                self.attack_startup_timer = utility.TimeKeeper(
                    duration=self.attack_startup
                )

            # 공격 준비 중 공격 가능 거리가 사라지면 idle로 복귀
            if self.state == MobState.attack_startup and not self.attack_possible:
                self.state = MobState.idle

            # 공격 준비 타이머 완료 시 실행 단계로 전이
            if (
                self.attack_startup_timer.is_finished()
                and self.state == MobState.attack_startup
            ):
                self.state = MobState.attack_execute

            # 공격 실행은 한 프레임 수행 후 recovery로 전이
            if (
                self.last_state == MobState.attack_execute
                and self.state == MobState.attack_execute
            ):
                self.state = MobState.attack_recovery
                self.attack_recovery_timer = utility.TimeKeeper(
                    duration=self.attack_recovery
                )

            # recovery 타이머 완료 후 다음 상태 결정
            if (
                self.state == MobState.attack_recovery
                and self.attack_recovery_timer.is_finished()
            ):
                if self.attack_possible:
                    self.state = MobState.attack_again
                elif self.detect_player:
                    self.state = MobState.chase
                else:
                    self.state = MobState.idle

            # idle에서 감지되면 chase로 전환
            if self.last_state == MobState.idle and not self.attack_possible:
                if self.detect_player:
                    self.state = MobState.chase
                else:
                    self.state = MobState.idle

            # ---------- 바이옴 기반 속도 결정 ----------
            mob_biome: biome.Biome = biome.get_biome(world, self.x, self.y)
            if mob_biome == biome.Biome.water:
                self.speed = self.speeds[1]
            elif mob_biome == biome.Biome.air:
                self.speed = self.speeds[2]
            else:
                self.speed = self.speeds[0]

            # ---------- 이동 처리 ----------
            move: bool = False
            if self.state == MobState.chase and not self.move_while_attack:
                move = True
            elif self.move_while_attack and self.detect_player:
                move = True

            if move:
                new_pos = pygame.Vector2(self.x, self.y).move_towards(
                    pygame.Vector2(world.player.x, world.player.y), self.speed * dt
                )
                self.x, self.y = new_pos.x, new_pos.y

                # 월드 경계 제한
                half_w = getattr(world, "width", 0) / 2
                half_h = getattr(world, "height", 0) / 2
                if self.x > half_w:
                    self.x = half_w
                if self.x < -half_w:
                    self.x = -half_w
                if self.y > half_h:
                    self.y = half_h
                if self.y < -half_h:
                    self.y = -half_h
        else:
            # 플레이어 사망 시에는 idle 상태
            self.state = MobState.idle

        # HP 및 공격 판정 처리
        self.update_hp(world)

        # ---------- 애니메이션 처리 ----------
        if self.attack_animation and self.state in (
            MobState.attack_startup,
            MobState.attack_execute,
            MobState.attack_recovery,
            MobState.attack_again,
        ):
            # 애니메이션의 update 결과를 이미지로 반영
            self.image = self.attack_animation.update()

        else:
            self.image = self.original_image

        # 플레이어의 상대 위치에 따라 좌우 반전
        if world.player.x > self.x and self.image:
            self.image = pygame.transform.flip(self.image, True, False)

        # 콜라이더 업데이트 (이미지 기반 또는 반지름 기반)
        if self.image:
            self.collider.update(self.x, self.y, self.image)
        else:
            self.collider.update(self.x, self.y, DEFAULT_COLLIDER_RADIUS)

        # 상태 백업
        self.last_state = self.state

    def update_hp(self, world: Any) -> None:
        """
        플레이어의 투사체와 충돌 검사 후 데미지 처리 및 파티클 생성.
        - 충돌 투사체를 모아 안전하게 제거
        - hp가 0 이하가 되면 alive 플래그를 False로 설정
        """
        attack_to_remove: List[Any] = []
        for attack in list(world.player_attack):
            collide_info = self.collider.collide(attack.collider)

            if collide_info:
                # 충돌 위치를 기준으로 파티클 발생
                world.shooter.shoot(
                    self.collider.rect.x + collide_info[0],
                    self.collider.rect.y + collide_info[1],
                    (200, 500),
                    0.99,
                    0.5,
                    assets.Image.hit_particle,
                    10,
                )
                self.get_damage(attack.damage)
                attack_to_remove.append(attack)

        # 충돌한 투사체 제거
        for attack in attack_to_remove:
            if type(attack) == Projectile:
                world.player_attack.remove(attack)

        if self.hp <= 0:
            self.alive = False


# -------------------
# 몹 종류들
# -------------------
class Burster(Mob):
    """산탄형 몹: 공격 시 다수의 투사체 생성"""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x,
            y,
            "burster",
            assets.Image.burster,
            1000,
            (450, 10, 500),
            100,
            500,
            1,
            2,
            attack_animation=utility.Animation(assets.Image.burster_attack_frames, 10),
        )

    def update(self, world: Any, dt: float) -> None:
        super().update(world, dt)
        if self.state == MobState.attack_execute:
            # 다수의 투사체 생성
            for i in range(120):
                world.mob_attack.append(
                    Projectile(
                        self.x,
                        self.y,
                        "burster_fire_ball",
                        1000,
                        i * 3,
                        assets.Image.fire_ball_image,
                        1,
                        500,
                    )
                )


class Biter(Mob):
    """근접형 몹: 공격 시 플레이어에게 직접 피해"""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x,
            y,
            "biter",
            assets.Image.biter,
            2000,
            (10, 500, 10),
            100,
            100,
            0,
            0.1,
            attack_animation=utility.Animation(assets.Image.biter_attack_frames, 10),
        )

    def update(self, world: Any, dt: float) -> None:
        super().update(world, dt)
        if self.state == MobState.attack_execute:
            world.player.get_damage(1)


class Flutterer(Mob):
    """돌격형 몹: 이동 중 공격을 수행"""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x,
            y,
            "flutterer",
            assets.Image.flutterer,
            3000,
            (10, 10, 1500),
            10,
            100,
            0,
            0.1,
            attack_animation=utility.Animation(
                assets.Image.flutterer_attack_frames, 10
            ),
            move_while_attack=True,
        )

    def update(self, world: Any, dt: float) -> None:
        super().update(world, dt)
        if self.state == MobState.attack_execute:
            world.player.get_damage(1)


class Plower(Mob):
    """충격파를 사용하는 몹"""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x,
            y,
            "plower",
            assets.Image.plower,
            2000,
            (150, 10, 300),
            100,
            800,
            0.5,
            1,
            attack_animation=utility.Animation(assets.Image.plower_attack_frames, 10),
        )

    def update(self, world: Any, dt: float) -> None:
        super().update(world, dt)
        if self.state == MobState.attack_execute:
            world.mob_attack.append(
                ShockWave(
                    self.x,
                    self.y,
                    "plower_shock_wave",
                    700,
                    assets.Image.shock_wave,
                    1,
                    800,
                )
            )


class BossSelfState(Enum):
    """보스 전용 공격 상태 정의"""

    projectile = 0
    wave = 1
    summon_minions = 2


class BossSelf(Mob):
    """보스: 여러 패턴을 순환하는 강력한 몹"""

    def __init__(self, x: float, y: float) -> None:
        super().__init__(
            x,
            y,
            "Self",
            None,
            float("inf"),
            (None, 0, 0),
            2000,
            None,
            0,
            None,
        )

        self.next_attack: BossSelfState = random.choice(
            [BossSelfState.projectile, BossSelfState.wave, BossSelfState.summon_minions]
        )

        self.start: bool = False
        self.attack_change_timer: utility.TimeKeeper = utility.TimeKeeper(
            duration=random.uniform(1, 10)
        )

    def update(self, world: Any, dt: float) -> None:
        # 보스가 시작 플래그가 켜져야 동작
        if self.start:
            # 공격 패턴 전환 타이머 체크
            if self.attack_change_timer.is_finished():
                self.next_attack = random.choice(
                    [
                        BossSelfState.projectile,
                        BossSelfState.wave,
                        BossSelfState.summon_minions,
                    ]
                )
                self.attack_change_timer = utility.TimeKeeper(
                    duration=random.uniform(1, 10)
                )

            # 패턴에 따른 능력치 설정
            if self.next_attack == BossSelfState.wave:
                self.attack_distance = 100
                self.speeds = (900, 0, 0)
                self.attack_recovery = 1
            elif self.next_attack == BossSelfState.projectile:
                self.attack_distance = 1000
                self.speeds = (400, 0, 0)
                self.attack_recovery = 0.5
            elif self.next_attack == BossSelfState.summon_minions:
                self.attack_distance = 10000
                self.speeds = (400, 0, 0)
                self.attack_recovery = 8

            super().update(world, dt)

            # 공격 실행 시 패턴별 동작
            if self.state == MobState.attack_execute:
                if self.next_attack == BossSelfState.projectile:
                    dx = world.player.x - self.x
                    dy = world.player.y - self.y
                    if dx == 0 and dy == 0:
                        angle = random.uniform(0, 360)
                    else:
                        angle = math.degrees(math.atan2(dy, dx))

                    for i in range(-2, 3):
                        world.mob_attack.append(
                            Projectile(
                                self.x,
                                self.y,
                                "boss_self_ball",
                                1000,
                                angle + i * 5,
                                assets.Image.boss_projectile,
                                5,
                                1000,
                            )
                        )

                elif self.next_attack == BossSelfState.wave:
                    world.mob_attack.append(
                        ShockWave(
                            self.x,
                            self.y,
                            "boss_self wave",
                            1000,
                            assets.Image.boss_wave,
                            2,
                            500,
                        )
                    )
                elif self.next_attack == BossSelfState.summon_minions:
                    # 미니언 소환
                    world.mob.append(Burster(self.x - BOSS_MINION_OFFSET, self.y))
                    world.mob.append(Biter(self.x + BOSS_MINION_OFFSET, self.y))
                    world.mob.append(Flutterer(self.x, self.y + BOSS_MINION_OFFSET))
                    world.mob.append(Plower(self.x, self.y - BOSS_MINION_OFFSET))

        # 보스가 살아있을 때/죽었을 때 지속 파티클 처리
        if self.alive:
            world.shooter.shoot(
                self.x, self.y, (0, 100), 1, 1, assets.Image.boss_smog, 1
            )
        else:
            world.shooter.shoot(
                self.x, self.y, (0, 1000), 1, 2, assets.Image.light, 5000
            )


class ShockWave(Entity):
    """충격파: 반지름이 증가하는 범위형 공격"""

    def __init__(
        self,
        x: float,
        y: float,
        name: str,
        vel: float,
        image: pygame.Surface,
        damage: float,
        wave_max_distance: float,
    ) -> None:
        super().__init__(x, y, image, name, center_pivot=True, do_not_arrange=True)

        self.origin_image: pygame.Surface = image
        self.vel: float = vel
        self.damage: float = damage
        self.wave_distance: float = 0.0
        self.wave_max_distance: float = wave_max_distance

        # 초기 이미지: 크기가 1 이상인 정수로 안전하게 설정
        init_size: int = max(1, int(self.wave_distance * 2))
        self.image = pygame.transform.scale(self.origin_image, (init_size, init_size))

        self.collider: utility.Collider = utility.Collider(
            self.x, self.y, 0, center_pivot=True
        )
        self.attack_speed: float = 0.1
        self.timer: utility.TimeKeeper = utility.TimeKeeper(self.attack_speed)
        self.alive: bool = True

    def update(self, dt: float) -> None:
        """충격파 확장 및 콜라이더 갱신"""
        self.wave_distance += self.vel * dt
        if self.wave_distance >= self.wave_max_distance:
            self.alive = False

        size: int = max(1, int(self.wave_distance * 2))
        self.image = pygame.transform.scale(self.origin_image, (size, size))

        self.collider.update(self.x, self.y, self.wave_distance)


class Projectile(Entity):
    """기본 투사체 클래스"""

    def __init__(
        self,
        x: float,
        y: float,
        name: str,
        vel: float,
        angle: float,
        image: Optional[pygame.Surface],
        damage: float,
        shoot_distance: float,
    ) -> None:
        # 발사 초기 좌표(사거리 검사용)
        self.origin_x: float = x
        self.origin_y: float = y
        self.vel: float = vel
        self.angle: float = angle
        self.damage: float = damage
        self.shoot_distance: float = shoot_distance

        # 이미지 회전
        rotated_image: Optional[pygame.Surface] = None
        rotated_image = (
            pygame.transform.rotate(image, 360 - self.angle) if image else None
        )

        super().__init__(x, y, rotated_image, name)

        # 콜라이더 초기화 (이미지 기반 또는 반지름 기반)
        if self.image:
            self.collider: utility.Collider = utility.Collider(
                self.x, self.y, self.image
            )
        else:
            self.collider: utility.Collider = utility.Collider(
                self.x, self.y, DEFAULT_COLLIDER_RADIUS
            )

        self.alive: bool = True

    def update(self, dt: float) -> None:
        """투사체 이동 및 사거리 초과 검사"""
        # 사거리 초과 시 제거
        if (
            utility.distance(self.x, self.y, self.origin_x, self.origin_y)
            > self.shoot_distance
        ):
            self.alive = False
            return

        vec = pygame.math.Vector2()
        vec.from_polar((self.vel, self.angle))  # in-place 변경
        self.x += vec.x * dt
        self.y += vec.y * dt

        # 콜라이더 갱신
        if self.image:
            self.collider.update(self.x, self.y, self.image)
        else:
            self.collider.update(self.x, self.y, DEFAULT_COLLIDER_RADIUS)


class InteractableEntity(Entity):
    """플레이어가 닿았을 때 상호작용 가능한 엔티티"""

    def __init__(
        self,
        x: float,
        y: float,
        image: Optional[pygame.Surface],
        name: str,
        collider_radius: float,
    ) -> None:
        super().__init__(x, y, image, name)
        # 안전하게 콜라이더 초기화
        self.collider: utility.Collider = utility.Collider(x, y, collider_radius)
