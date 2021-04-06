from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from pygame import mixer
from src.const import PIECE_SLIDE_SFX, ARROW_SFX, SOUNDTRACK, RICKROLL


class AmazonsSoundDelegate:
    def music_started_playing(self):
        raise NotImplemented

    def music_stopped_playing(self):
        raise NotImplemented


class AmazonsSound:
    shared = None

    def __init__(self):
        mixer.init()
        print()
        self._piece_move_sfx = mixer.Sound(PIECE_SLIDE_SFX)
        self._arrow_shoot_sfx = mixer.Sound(ARROW_SFX)
        self._soundtrack = mixer.music.load(RICKROLL)
        self.__is_music_playing = False

        self.delegates = []

    @classmethod
    def init_shared(cls):
        if cls.shared is None:
            cls.shared = cls()

    def play_piece_move_sfx(self):
        self._piece_move_sfx.play()

    def play_arrow_sfx(self):
        self._arrow_shoot_sfx.play()

    def play_music(self):
        self.__is_music_playing = True
        mixer.music.play(-1)
        for delegate in self.delegates:
            delegate.music_started_playing()

    def stop_music(self):
        self.__is_music_playing = False
        mixer.music.stop()
        for delegate in self.delegates:
            delegate.music_stopped_playing()

    @property
    def is_music_playing(self):
        return self.__is_music_playing

    def add_delegate(self, delegate: AmazonsSoundDelegate):
        self.delegates.append(delegate)

    def remove_delegate(self, delegate: AmazonsSoundDelegate) -> bool:
        try:
            self.delegates.remove(delegate)
        except ValueError:
            return False
        else:
            return True


AmazonsSound.init_shared()
