# player.py
"""
플레이어 정의 모듈
"""

from enum import Enum
import pygame
import math
import random
import sys
from typing import Any, Optional, Tuple, List
from tkinter import messagebox

# 파일 단독 실행 방지
if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import utility
    from . import assets
    from . import entities
    from . import biome


# -----------------------
# 상수 정의
# -----------------------
INITIAL_MAX_SPEED: int = 500
PLAYER_DRAG_FACTOR: float = 0.1
WATER_SPEED_FACTOR: float = 0.5
AIR_SPEED_FACTOR: float = 10.0

DEFENCE_DURATION: float = 10
INVINCIBLE_AVOID_DURATION: float = 2

SPEED_UP_DURATION: float = 10
SPEED_UP_FACTOR: float = 2

LEAD_OF_WIND_DURATION: float = 10
LEAD_OF_WIND_SPEED: float = 200

INITIAL_PLAYER_VIEW: int = 540
DECREASED_PLAYER_VIEW: int = 400
PLAYER_VIEW_IMAGE_SIZE: Tuple[int, int] = (3080, 3080)

DEFAULT_COLLIDER_RADIUS: int = 32  # 플레이어 콜라이더 반지름


# -----------------------
# 공격 타입 Enum
# -----------------------
class attack_type(Enum):
    """공격 타입 Enum"""

    fire = 0
    water = 1
    dirt = 2
    air = 3
    selement = 4  # (특수 원소)


# -----------------------
# Player 클래스
# -----------------------
class Player:
    """
    플레이어 클래스
    책임:
      - 이동, 공격, 원소 충전
      - 상태(버프/디버프) 처리
      - 월드와의 상호작용 (포탈, selement)
    """

    def __init__(self, x: float, y: float) -> None:
        # 위치/이동
        self.x: float = x
        self.y: float = y
        self.velocity: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        self.max_speed: float = INITIAL_MAX_SPEED

        # 카메라
        self.cam: utility.Camera = utility.Camera(self.x, self.y)

        # 체력/방어
        self.hp: float = 100
        self.max_hp: float = 100
        self.defence: float = 0
        self.alive: bool = True

        # 효과 타이머
        self.defence_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)
        self.invincible_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)
        self.speed_up_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)
        self.lead_of_wind_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)

        # 엔딩 관련
        self.closest_portal: Optional[Tuple[Any, float]] = None
        self.ending: bool = False
        self.ended: bool = False
        self.easter_egg_ending: bool = False

        # 플레이어 뷰
        self.player_view: int = INITIAL_PLAYER_VIEW
        self.last_player_view: int = self.player_view
        self.player_view_image: pygame.Surface = pygame.transform.scale(
            assets.Image.player_view,
            (
                int(PLAYER_VIEW_IMAGE_SIZE[0] * self.player_view / INITIAL_PLAYER_VIEW),
                int(PLAYER_VIEW_IMAGE_SIZE[1] * self.player_view / INITIAL_PLAYER_VIEW),
            ),
        )

        # 충돌체
        self.collider: utility.Collider = utility.Collider(
            self.x, self.y, DEFAULT_COLLIDER_RADIUS
        )

        # 원소(자원) 관련
        self.element_charge_speed: float = 0.1
        self.element_max: int = 100
        self.element_charge_timer: utility.TimeKeeper = utility.TimeKeeper(duration=0)
        self.charging: bool = False

        self.fire: int = 0
        self.water: int = 0
        self.dirt: int = 0
        self.air: int = 0
        self.selement: int = 0  # '셀레먼트' 카운트

        # 선택 공격 타입 (기본: fire)
        self.selected_attack_code: int = 0
        self.selected_attack: attack_type = attack_type(self.selected_attack_code)

        # 내부: 현재 바이옴 (업데이트 시 설정)
        self.player_biome: Optional[biome.Biome] = None

    # --------------------
    # 프레임 업데이트 엔트리
    # --------------------
    def update(self, world: Any, keys: Any, pygame_event: List[Any], dt: float) -> None:
        """
        한 프레임 동안 플레이어 상태를 업데이트
        순서:
         - 원소 충전 (가능 시)
         - 공격 선택/실행
         - 효과 적용
         - 이동 처리
         - 피격 처리, 사망 검사
         - 월드 상호작용
        """
        # 현재 바이옴
        self.player_biome = biome.get_biome(world, self.x, self.y)

        if self.alive:
            # 원소 충전
            self._charge_element(keys)

            # 공격 타입 선택 및 공격(충전 중에는 공격 불가)
            self._select_attack_type(pygame_event)
            self._attack(pygame_event, world)

        # 모든 프레임에서 효과 적용 (버프/디버프 등)
        self._apply_effect(world, dt)

        # 이동 (충전 중이면 이동 제한)
        self._handle_player_movement(keys, dt, world, player_move=not self.charging)

        # 피격 처리
        self._update_hp(world)

        # 사망 처리
        if self.hp <= 0:
            self._game_over()

        # 월드와의 상호작용 (포탈/셀레먼트)
        self._interact(world)

    # --------------------
    # 데미지 / HP 처리
    # --------------------
    def get_damage(self, damage: float) -> None:
        """
        플레이어가 피해를 입었을 때 처리
        - 방어력 반영
        - 카메라 흔들림 + 히트 사운드 재생
        """
        if self.alive:
            if not self.defence == 100:
                self.hp -= damage * ((100 - self.defence) / 100)
                self.cam.shake(0.1, 10)
                assets.Sound.player_hit.play()

        if self.hp < 0:
            self.hp = 0

    def _update_hp(self, world: Any) -> None:
        """
        몬스터 공격 리스트(world.mob_attack)와 충돌 검사하여 HP 갱신
        - 타이머가 있는 공격은 타이머 완료 시 데미지 적용
        - Projectile 타입은 충돌 시 제거
        """
        attack_to_remove: List[Any] = []
        for attack in list(world.mob_attack):
            collided = attack.collider.collide(self.collider)

            if collided:
                if hasattr(attack, "timer"):
                    if attack.timer.is_finished():
                        self.get_damage(attack.damage)
                        attack_to_remove.append(attack)
                        attack.timer.reset()

                else:
                    self.get_damage(attack.damage)
                    attack_to_remove.append(attack)

        for attack in attack_to_remove:
            if isinstance(attack, entities.Projectile):
                world.mob_attack.remove(attack)

    # --------------------
    # 이동 처리
    # --------------------
    def _handle_player_movement(
        self, keys: Any, dt: float, world: Any, player_move: bool = True
    ) -> None:
        """
        플레이어 이동 처리
        - WASD 입력
        - 바이옴(물/공기)에 따른 속도 보정
        - 공중에서는 감속(드래그) 로직 적용
        - 월드 경계 제한 및 카메라/콜라이더 업데이트
        """
        move: bool = False
        player_velocity: pygame.math.Vector2 = pygame.math.Vector2(0, 0)

        # 공중일 경우 드래그 적용, 아닐 경우 관성 초기화
        if self.player_biome != biome.Biome.air:
            self.velocity = pygame.math.Vector2(0, 0)
        else:
            if self.velocity.length() > 0:
                drag_force = self.velocity.normalize() * PLAYER_DRAG_FACTOR * dt
            else:
                drag_force = pygame.math.Vector2(0, 0)
            if self.velocity.length() <= drag_force.length():
                self.velocity = pygame.math.Vector2(0, 0)
            else:
                self.velocity -= drag_force

        # 바이옴 기반 속도 선택
        if self.player_biome == biome.Biome.water:
            speed: float = self.max_speed * WATER_SPEED_FACTOR
        elif self.player_biome == biome.Biome.air:
            speed = self.max_speed * AIR_SPEED_FACTOR
        else:
            speed = self.max_speed

        # 입력 처리 (WASD)
        if keys[pygame.K_w]:
            move = True
            player_velocity.y -= 1
        if keys[pygame.K_s]:
            move = True
            player_velocity.y += 1
        if keys[pygame.K_a]:
            move = True
            player_velocity.x -= 1
        if keys[pygame.K_d]:
            move = True
            player_velocity.x += 1

        # 정규화 및 속도 적용
        if move and player_velocity.length() != 0:
            player_velocity = player_velocity.normalize() * speed * dt

        if self.alive and player_move:
            if self.player_biome != biome.Biome.air:
                self.velocity += player_velocity
            else:
                # 공중에서는 추가 감속 적용
                self.velocity += player_velocity * PLAYER_DRAG_FACTOR * dt

        # 최종 속도 제한
        if self.velocity.length() > speed * dt:
            self.velocity = self.velocity.normalize() * speed * dt

        # 위치 업데이트
        self.x += self.velocity.x
        self.y += self.velocity.y

        # 월드 범위 제한
        try:
            self.x = max(-world.width / 2, min(self.x, world.width / 2))
            self.y = max(-world.height / 2, min(self.y, world.height / 2))
        except Exception:
            # world에 width/height가 없는 경우 무시
            pass

        # 콜라이더 및 카메라 갱신 (안전 호출)
        self.collider.update(self.x, self.y, 32)
        self.cam.update_position(self.x, self.y, dt)

    # --------------------
    # 원소 충전
    # --------------------
    def _charge_element(self, keys: Any) -> None:
        """
        F 키를 눌러 현재 바이옴에 맞는 원소를 충전
        - fifth_biome(특수 바이옴)에서는 모든 원소를 동시에 충전
        """
        self.charging = False
        if keys[pygame.K_f]:
            self.charging = True
            if self.element_charge_timer.is_finished():
                if (
                    self.player_biome == biome.Biome.fire
                    and self.fire < self.element_max
                ):
                    self.fire += 1
                elif (
                    self.player_biome == biome.Biome.water
                    and self.water < self.element_max
                ):
                    self.water += 1
                elif (
                    self.player_biome == biome.Biome.dirt
                    and self.dirt < self.element_max
                ):
                    self.dirt += 1
                elif (
                    self.player_biome == biome.Biome.air and self.air < self.element_max
                ):
                    self.air += 1
                elif self.player_biome == biome.Biome.fifth_biome:
                    if self.fire < self.element_max:
                        self.fire += 1
                    if self.water < self.element_max:
                        self.water += 1
                    if self.dirt < self.element_max:
                        self.dirt += 1
                    if self.air < self.element_max:
                        self.air += 1

                # 타이머 재설정
                self.element_charge_timer = utility.TimeKeeper(
                    duration=self.element_charge_speed
                )

    # --------------------
    # 공격 타입 선택 (마우스 휠)
    # --------------------
    def _select_attack_type(self, pygame_event: List[Any]) -> None:
        """
        마우스 휠 이벤트로 공격 타입 선택
        - selement(셀레먼트)가 0이면 0..3(4종류)로 순환
        - selement > 0이면 0..4(5종류)로 순환
        """
        for event in pygame_event:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.selected_attack_code -= 1
                elif event.button == 5:
                    self.selected_attack_code += 1

        modulo = 5 if self.selement > 0 else 4
        if modulo <= 0:
            modulo = 4
        self.selected_attack_code %= modulo
        self.selected_attack = attack_type(self.selected_attack_code)

    # --------------------
    # 공격 처리 (좌/우 클릭)
    # --------------------
    def _attack(self, pygame_event: List[Any], world: Any) -> None:
        """
        마우스 입력에 따라 공격 실행
        - 좌클릭: 일반 공격
        - 우클릭: 특수 공격
        충전 중이면 공격 불가
        """
        mouse_btn: Optional[int] = None
        for event in pygame_event:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):
                    mouse_btn = event.button

        if self.charging:
            return

        if mouse_btn == 1:
            self._handle_left_click(world)
        elif mouse_btn == 3:
            self._handle_right_click(world)

    def _handle_left_click(self, world: Any) -> None:
        """좌클릭 일반 공격 처리 (자원 감소/효과)"""
        if self.selected_attack == attack_type.fire and self.fire >= 1:
            self.fire -= 1
            self._shoot_projectile(
                world, "player_fire_ball", 500, assets.Image.fire_ball_image, 10, 1000
            )
            assets.Sound.projectile_shoot.play()
        elif self.selected_attack == attack_type.dirt and self.dirt >= 5:
            self.dirt -= 5
            self.defence_timer = utility.TimeKeeper(duration=DEFENCE_DURATION)
            assets.Sound.skill_use.play()
        elif (
            self.selected_attack == attack_type.water
            and self.water >= 5
            and self.hp < self.max_hp
        ):
            self.water -= 5
            self.hp += 1
            world.shooter.shoot(
                self.x,
                self.y,
                (200, 400),
                0.9,
                1,
                assets.Image.recovery_particle,
                20,
            )
            assets.Sound.skill_use.play()
        elif self.selected_attack == attack_type.air and self.air >= 1:
            self.air -= 5
            self.speed_up_timer = utility.TimeKeeper(duration=SPEED_UP_DURATION)
            assets.Sound.skill_use.play()
        elif self.selected_attack == attack_type.selement and self.selement >= 1:
            # 셀레먼트를 사용하면 엔딩 트리거
            self.ended = True
            self.easter_egg_ending = False
            assets.Sound.earn_selement.play()

    def _handle_right_click(self, world: Any) -> None:
        """우클릭 특수 공격 처리 (자원 체크/효과 적용)"""
        if (
            self.selected_attack == attack_type.fire
            and self.fire >= 5
            and self.dirt >= 1
        ):
            self.fire -= 5
            self.dirt -= 1
            self._shoot_projectile(
                world, "player_magma_arrow", 1000, assets.Image.magma_arrow, 90, 2000
            )
            assets.Sound.projectile_shoot.play()
        elif (
            self.selected_attack == attack_type.dirt
            and self.dirt >= 10
            and self.fire >= 1
            and self.air >= 1
            and self.water >= 1
        ):
            self.dirt -= 10
            self.fire -= 1
            self.water -= 1
            self.air -= 1
            self.invincible_timer = utility.TimeKeeper(
                duration=INVINCIBLE_AVOID_DURATION
            )
            assets.Sound.skill_use.play()
        elif (
            self.selected_attack == attack_type.water
            and self.water >= 100
            and self.dirt >= 50
            and self.air >= 50
            and self.fire >= 50
            and self.hp != self.max_hp
        ):
            self.water -= 100
            self.dirt -= 50
            self.fire -= 50
            self.air -= 50
            self.hp = self.max_hp
            world.shooter.shoot(
                self.x,
                self.y,
                (200, 400),
                0.9,
                1,
                assets.Image.recovery_particle,
                20,
            )
            assets.Sound.skill_use.play()
        elif (
            self.selected_attack == attack_type.air
            and self.air >= 30
            and self.fire >= 10
            and self.water >= 10
            and self.dirt >= 10
        ):
            # 가장 가까운 포탈 탐색 및 이동 효과 준비
            self._find_closest_portal(world)
            if self.closest_portal is not None:
                # 포탈 존재 시만 자원 차감 및 소리 재생
                self.air -= 30
                self.fire -= 10
                self.water -= 10
                self.dirt -= 10
                self.lead_of_wind_timer = utility.TimeKeeper(
                    duration=LEAD_OF_WIND_DURATION
                )
                assets.Sound.skill_use.play()

        elif (
            self.selected_attack == attack_type.selement
            and self.selement >= 1
            and self.fire >= 100
            and self.water >= 100
            and self.dirt >= 100
            and self.air >= 100
        ):
            # 이스터에그 엔딩 트리거
            self.fire -= 100
            self.water -= 100
            self.dirt -= 100
            self.air -= 100
            self.ended = True
            self.easter_egg_ending = True
            assets.Sound.earn_selement.play()

    # --------------------
    # 투사체 생성 보조
    # --------------------
    def _shoot_projectile(
        self,
        world: Any,
        name: str,
        speed: float,
        image: Optional[pygame.Surface],
        damage: float,
        lifetime: float,
    ) -> None:
        """
        투사체를 생성하여 발사
        - 마우스 위치(화면 중심 기준)를 사용해 각도 계산
        """

        mouse_pos = utility.Screen.get_scaled_mouse_pos(pygame.mouse.get_pos())
        dx = mouse_pos[0] - (utility.Screen.target_width // 2)
        dy = mouse_pos[1] - (utility.Screen.target_height // 2)

        if dx == 0 and dy == 0:
            angle: float = random.uniform(0, 360)
        else:
            angle = math.degrees(math.atan2(dy, dx))

            world.player_attack.append(
                entities.Projectile(
                    self.x, self.y, name, speed, angle, image, damage, lifetime
                )
            )

    # --------------------
    # 포탈 탐색
    # --------------------
    def _find_closest_portal(self, world: Any) -> None:
        """월드에서 가장 가까운 portal 엔티티를 찾아 저장"""
        portals: List[Tuple[Any, float]] = []
        for entity in world.entities:
            if getattr(entity, "name", None) == "portal":
                portals.append(
                    (entity, utility.distance(self.x, self.y, entity.x, entity.y))
                )
        if not portals:
            self.closest_portal = None
            return

        # 최소 거리의 portal 선택
        self.closest_portal = min(portals, key=lambda p: p[1])

    # --------------------
    # 효과 적용 (버프/디버프)
    # --------------------
    def _apply_effect(self, world: Any, dt: float) -> None:
        """
        각종 상태 효과 처리:
        - 무적/방어에 따른 방어력 및 시각 효과
        - 속도 증가가 적용되면 속도 보정
        - 물속에 들어가면 시야 감소
        - 바람의 인도(포탈로 이동) 처리
        """
        # 무적(우선) / 방어 / 기본 방어력 설정
        if not self.invincible_timer.is_finished():
            self.defence = 100
            world.entities.append(
                entities.Entity(
                    self.x,
                    self.y,
                    assets.Image.super_shield,
                    "super_shield",
                    center_pivot=True,
                    do_not_arrange=True,
                )
            )
        elif not self.defence_timer.is_finished():
            self.defence = 35
            world.entities.append(
                entities.Entity(
                    self.x,
                    self.y,
                    assets.Image.shield,
                    "shield",
                    center_pivot=True,
                    do_not_arrange=True,
                )
            )
        else:
            self.defence = 0

        # 체력 상한 적용
        if self.hp > self.max_hp:
            self.hp = self.max_hp

        if self.player_biome == biome.Biome.water:
            # 물속에 있을 때 시야 감소
            self.player_view = DECREASED_PLAYER_VIEW
        else:
            self.player_view = INITIAL_PLAYER_VIEW

        # 속도 증가 적용
        if not self.speed_up_timer.is_finished():
            self.max_speed = INITIAL_MAX_SPEED * SPEED_UP_FACTOR
        else:
            self.max_speed = INITIAL_MAX_SPEED

        # 플레이어 뷰 이미지 갱신 (정수 크기 사용)
        if self.player_view != self.last_player_view:
            self.player_view_image = pygame.transform.scale(
                assets.Image.player_view,
                (
                    int(
                        PLAYER_VIEW_IMAGE_SIZE[0]
                        * self.player_view
                        / INITIAL_PLAYER_VIEW
                    ),
                    int(
                        PLAYER_VIEW_IMAGE_SIZE[1]
                        * self.player_view
                        / INITIAL_PLAYER_VIEW
                    ),
                ),
            )

            self.last_player_view = self.player_view

        # 바람의 인도 (포탈 쪽으로 이동)
        if (
            not self.lead_of_wind_timer.is_finished()
            and self.closest_portal is not None
        ):
            target = pygame.math.Vector2(
                self.closest_portal[0].x, self.closest_portal[0].y
            )
            wind_force = pygame.math.Vector2(self.x, self.y).move_towards(
                target, LEAD_OF_WIND_SPEED * dt
            )
            self.x, self.y = wind_force.x, wind_force.y

    # --------------------
    # 월드와의 상호작용
    # --------------------
    def _interact(self, world: Any) -> None:
        """
        포탈 또는 셀레먼트(Selement) 등과 충돌 시 상호작용 처리
        - portal: 충돌 시 ending 플래그 설정
        - selement: 충돌 시 셀레먼트 카운트 증가 및 제거 대상에 추가
        """
        entity_to_remove: List[Any] = []
        for entity in list(world.entities):
            name = getattr(entity, "name", None)
            if name == "portal":
                if self.collider.collide(entity.collider):
                    self.ending = True
                    assets.Sound.portal_enter.play()

            elif name == "selement":
                if self.collider.collide(entity.collider):
                    self.selement += 1
                    entity_to_remove.append(entity)
                    assets.Sound.earn_selement.play()

        for entity in entity_to_remove:
            if hasattr(world, "static_objects") and entity in world.static_objects:
                world.static_objects.remove(entity)

    # --------------------
    # 게임 오버
    # --------------------
    def _game_over(self) -> None:
        """
        플레이어 사망 시 처리
        - 게임 오버 사운드 재생(중복 재생 방지)
        - alive 상태를 False로 설정
        """
        if self.alive:
            assets.Sound.game_over.play()
        self.alive = False
