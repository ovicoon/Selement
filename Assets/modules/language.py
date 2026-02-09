# language.py
"""
다국어 지원을 위한 언어 모듈
- 모든 텍스트는 키 기반으로 관리
- 런타임 언어 변경 가능
"""

from enum import Enum
from typing import Dict, List, Optional
import sys
from tkinter import messagebox
import pygame

if __name__ == "__main__":
    messagebox.showwarning(
        "Run Error",
        "This module is not meant to be run directly.\nPlease run the main game script instead.",
    )
    sys.exit()
else:
    from . import utility


# =========================
# 언어 Enum
# =========================
class Language(Enum):
    """지원하는 언어 정의"""

    KOREAN = "KOREAN"
    ENGLISH = "ENGLISH"


# =========================
# 텍스트 키 Enum
# =========================
class LineKey(Enum):
    """대사 키 정의"""

    INTRO = "INTRO"
    BEFORE_BOSS = "BEFORE_BOSS"
    AFTER_BOSS = "AFTER_BOSS"
    NORMAL_ENDING = "NORMAL_ENDING"
    EASTER_EGG_ENDING = "EASTER_EGG_ENDING"


class TextKey(Enum):
    """텍스트 키 정의"""

    INPUT_NAME = "INPUT_NAME"
    PLAY = "PLAY"
    EXIT = "EXIT"
    CONTROLS = "CONTROLS"
    DEVELOPED_BY = "DEVELOPED_BY"
    ESC_TO_EXIT = "ESC_TO_EXIT"
    CREDIT = "CREDIT"
    KEY_CONTROLS = "KEY_CONTROLS"
    DEBUG_INFO = "DEBUG_INFO"
    ERR_WHILE_DEBUG = "ERR_WHILE_DEBUG"
    GAME_OVER = "GAME_OVER"


# =========================
# 언어 데이터
# =========================
LANGUAGE_DATA: Dict[Language, Dict[LineKey, List[str]]] = {
    Language.KOREAN: {
        LineKey.INTRO: [
            "내 이름은 {username}.",
            "딱히 특별한것도 없는 인간이다.",
            "그냥 조용히 살고 싶었는데...",
            "어쩌다 이곳에 왔을까...",
            "어떻게 다시 돌아가지...",
            "우선 이 세계를 살펴봐야 겠다.",
            "... ...",
            "그러고 보니...",
            "그때 희미하게 본 하늘색 물체...",
            "그건 뭐였을까?",
        ],
        LineKey.BEFORE_BOSS: [
            "하늘색 물체: 용케도 왔군",
            "하늘색 물체: 나는 너다.",
            "나: ???",
            "하늘색 물체: 하나 물어보지",
            "하늘색 물체: 너의 삶의 이유는 뭐지?",
            "나: 그건 됐고, 이곳에서 나가게 해줘",
            "하늘색 물체: 이곳에서 나가고 싶은가?",
            "하늘색 물체: 그렇다면...",
            "하늘색 물체: 나를 쓰러뜨려보아라!",
        ],
        LineKey.AFTER_BOSS: [
            "목소리: 하하하하!",
            "나: 뭐지? 아직 살아있는건가?",
            "목소리: 하하하하!",
            "목소리: 쓰러뜨릴수 있을거라 생각했나?",
            "목소리: 너가 있는한 나는 존재한다.",
            "목소리: 너는 아직 모든 원소를 모른다.",
            "나: 어째서?",
            "목소리: 아직도 모르는가?",
            "목소리: 5번째 원소가 존재하기 때문이지",
            "나: 뭐라고?!",
            "목소리: 그 원소의 이름은 셀레먼트이지.",
            "목소리: selement... 아직도 모르는가?",
            "목소리: self element 라는 뜻이지.",
            "목소리: 너가 아직 손에 넣지 못한건 뭐지?",
            "나: 내가.. 손에넣지 못한.. 것?",
            "나: ...나 아닐까",
            "목소리: 하하하하!",
            "목소리: 그럼 이제 답을 알았는가?",
            "나: 내가 사는 이유?",
            "목소리: 부디 깨달았길 바란다.",
            "목소리: 너에게 Selement 를 주지.",
            "목소리: 기억해라! Selement 없이는",
            "목소리: 아무도 강한 힘을 사용하지 못한다.",
            "목소리: 너도 강한 힘을 갖고 있다.",
            "목소리: 너가 누군지 깨닫는다면..",
            "목소리: 그 힘을 사용할수 있을 것이다!",
            "나: 나..라고?",
            "목소리: 부디 너만의 길을 찾기를!",
            "나: 어? 왜 갈것처럼 이야기해?",
            "목소리: 나는 가지 않아",
            "목소리: 너 안에 있을거니까",
        ],
        LineKey.NORMAL_ENDING: [
            "내 이름은 {username}.",
            "딱히 특별한것도 없어보이지만",
            "딱히 평범할것도 없다.",
            "어젯밤의 꿈은 나를 일깨워 주었다",
            "어쩌다 그곳에 갔는지는 모르지만",
            "확실한것은 알았다.",
            "나는 나라는 걸",
            "그리고 나를 깨닫는것이 중요하다는걸",
            "(띠리리링!)",
            "알람이다. 매일 듣는.",
            "오늘은 평범하지만 평범하지 않다.",
            "그것이 나를, 나의 Selement 를 이룰테니",
            "어? 뭐야 늦잠잤잖아?",
            "안녕, 지금은 급할것 같고, 다음에 다시 보자!",
            "The End",
        ],
        LineKey.EASTER_EGG_ENDING: [
            "내 이름은 {username}.",
            "딱히 특별한것도 없어보이지만",
            "딱히 평범할것도 없다.",
            "어젯밤의 꿈은 나를 일깨워 주었다",
            "어쩌다 그곳에 갔는지는 모르지만",
            "확실한것은 알았다.",
            "나는 나라는 걸",
            "그리고 나를 깨닫는것이 중요하다는걸",
            "(띠리리링!)",
            "알람이다. 매일 듣는.",
            "오늘은 평범하지만 평범하지 않다.",
            "그것이 나를, 나의 Selement 를 이룰테니",
            "어? 뭐야 늦잠잤잖아?",
            "안녕, 지금은 급할것 같고, 다음에 다시 보자!",
            "The End?",
            "...",
            "그나저나...",
            "내가 모은 원소들은 어디에 간거지?",
            "100개씩이나 모았는데...",
            "The End",
        ],
        TextKey.INPUT_NAME: ["유저 이름을 입력하세요"],
        TextKey.PLAY: ["플레이"],
        TextKey.EXIT: ["종료"],
        TextKey.CONTROLS: ["조작법"],
        TextKey.DEVELOPED_BY: ["크레딧"],
        TextKey.CREDIT: ["제작: 오승훈\n감사합니다."],
        TextKey.KEY_CONTROLS: [
            "이동: W,A,S,D\n원소 충전: F\n일반공격: 좌클릭\n특수공격: 우클릭\n스킬 변경: 마우스 휠 스크롤\n대사 넘기기: 엔터 키\n디버그: F12 키"
        ],
        TextKey.ESC_TO_EXIT: ["esc 키를 눌러서 복귀"],
        TextKey.DEBUG_INFO: [
            "좌표",
            "fps",
            "바이옴",
            "청크",
            "속도",
            "로드된 엔티티",
            "cpu 이름",
            "cpu 사용량",
            "ram 사용량",
            "플레이어 방어력",
            "플레이어 HP",
        ],
        TextKey.ERR_WHILE_DEBUG: ["디버그 정보 로드 중 오류 발생"],
        TextKey.GAME_OVER: ["게임 오버!"],
    },
    Language.ENGLISH: {
        LineKey.INTRO: [
            "My name is {username}.",
            "I'm just an ordinary person.",
            "Nothing special about me.",
            "I just wanted a quiet life...",
            "So how did I end up here?",
            "How do I get back?",
            "For now, I should explore this world.",
            "... ...",
            "Come to think of it...",
            "That faint cyan-colored object...",
            "What was it?",
        ],
        LineKey.BEFORE_BOSS: [
            "Cyan Figure: So, you made it.",
            "Cyan Figure: I am you.",
            "Me: ...What?",
            "Cyan Figure: Let me ask you.",
            "Cyan Figure: Why do you live?",
            "Me: I don't care. Let me leave.",
            "Cyan Figure: You wish to escape?",
            "Cyan Figure: Then...",
            "Cyan Figure: Defeat me.",
        ],
        LineKey.AFTER_BOSS: [
            "Voice: Hahahaha!",
            "Me: What...? Still alive?",
            "Voice: Hahahaha!",
            "Voice: Did you think you could win?",
            "Voice: As long as you exist, I do.",
            "Voice: You know nothing of elements.",
            "Me: Why?",
            "Voice: Still confused?",
            "Voice: A fifth element exists.",
            "Me: The fifth... element?",
            "Voice: Its name is Selement.",
            "Voice: Selement... understand?",
            "Voice: It means 'Self Element'.",
            "Voice: What do you lack?",
            "Me: What I lack...?",
            "Me: ...Myself?",
            "Voice: Hahahaha!",
            "Voice: Now you see?",
            "Me: The reason I live?",
            "Voice: I hope so.",
            "Voice: I grant you Selement.",
            "Voice: Remember this.",
            "Voice: No Selement, No power.",
            "Voice: You have great power.",
            "Voice: Know who you are...",
            "Voice: And use it.",
            "Me: Me...?",
            "Voice: Find your own path.",
            "Me: Wait—are you leaving?",
            "Voice: I am not.",
            "Voice: I remain within you.",
        ],
        LineKey.NORMAL_ENDING: [
            "My name is {username}.",
            "I may not seem special.",
            "But I am not ordinary.",
            "Last night's dream awakened me.",
            "I don't know why I was there.",
            "But one thing is clear.",
            "I am myself.",
            "Understanding myself matters.",
            "(Beep—Beep!)",
            "My alarm. Same as always.",
            "Today feels ordinary, yet new.",
            "It shapes who I am—my Selement.",
            "What—I'm late?!",
            "Sorry, no time. See you again!",
            "The End",
        ],
        LineKey.EASTER_EGG_ENDING: [
            "My name is {username}.",
            "I may not seem special.",
            "But I am not ordinary.",
            "Last night's dream awakened me.",
            "I don't know why I was there.",
            "But one thing is clear.",
            "I am myself.",
            "Understanding myself matters.",
            "(Beep—Beep!)",
            "My alarm. Same as always.",
            "Today feels ordinary, yet new.",
            "It shapes who I am—my Selement.",
            "What—I'm late?!",
            "Sorry, no time. See you again!",
            "The End?",
            "...",
            "By the way...",
            "Where did my elements go?",
            "I had over a hundred...",
            "The End",
        ],
        TextKey.INPUT_NAME: ["Please enter username"],
        TextKey.PLAY: ["Play"],
        TextKey.EXIT: ["exit"],
        TextKey.CONTROLS: ["ctrls"],
        TextKey.DEVELOPED_BY: ["credit"],
        TextKey.CREDIT: ["Created by: Brayden Seung-hoon Oh\nThank you."],
        TextKey.KEY_CONTROLS: [
            "Move: W,A,S,D\nElement Charge: F\nNormal Attack: Left Click\nSpecial Attack: Right Click\nSkill Change: Mouse Wheel Scroll\nSkip Dialogue: Enter Key\nDebug: F12 Key"
        ],
        TextKey.ESC_TO_EXIT: ["Press esc to return"],
        TextKey.DEBUG_INFO: [
            "coords",
            "fps",
            "biome",
            "chunk",
            "speed",
            "loaded entities",
            "cpu name",
            "cpu usage",
            "ram usage",
            "player defense",
            "player HP",
        ],
        TextKey.ERR_WHILE_DEBUG: ["Error occurred while loading debug info"],
        TextKey.GAME_OVER: ["Game Over!"],
    },
}


# =========================
# Language Manager
# =========================
class LanguageManager:
    """언어 관리 클래스"""

    def __init__(self, language: Language):
        self.language = language

    def set_language(self, language: Language) -> None:
        self.language = language

    def get(self, key: LineKey, **kwargs) -> List[str]:
        lines = LANGUAGE_DATA[self.language][key]
        return [line.format(**kwargs) for line in lines]


def check_line_length(
    max_length: int, font: pygame.freetype.Font, check_key: Optional[LineKey] = None
) -> str:
    """모든 언어의 모든 대사가 특정 길이 이하인지 확인하는 함수(개발용)"""
    for lang, texts in LANGUAGE_DATA.items():
        for key, lines in texts.items():
            for line in lines:
                if check_key == None or type(key) == type(check_key):
                    if utility.str_to_surface(line, font).get_width() > max_length:
                        print(
                            f"Language {lang.name}, {key.name} exceeds max length: {line}"
                        )
