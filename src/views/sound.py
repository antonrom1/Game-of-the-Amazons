from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from pygame import mixer
from src.const import PIECE_SLIDE_SFX, ARROW_SFX, SOUNDTRACK, RICKROLL


class AmazonsSoundDelegate:
    """Protocole pour les observateurs de AmazonsSound"""

    def music_started_playing(self):
        """Est appelé lorsque la musique est allumée"""
        raise NotImplemented

    def music_stopped_playing(self):
        """Est appelé lorsque la musique est coupée"""
        raise NotImplemented


class AmazonsSound:
    shared = None

    def __init__(self):
        mixer.init()

        self._piece_move_sfx = mixer.Sound(PIECE_SLIDE_SFX)
        self._arrow_shoot_sfx = mixer.Sound(ARROW_SFX)
        self._soundtrack = mixer.music.load(RICKROLL)

        self.__is_music_playing = False

        self.delegates = []

    @classmethod
    def init_shared(cls):
        """Initialise l'instance globale AmazonsSound.shared"""
        if cls.shared is None:
            cls.shared = cls()

    def play_piece_move_sfx(self):
        """Joue l'effet sonore du mouvement de reine"""
        self._piece_move_sfx.play()

    def play_arrow_sfx(self):
        """Joue l'effet sonore du tir de flèche"""
        self._arrow_shoot_sfx.play()

    def play_music(self):
        """Met la musique"""
        self.__is_music_playing = True
        mixer.music.play(-1)
        for delegate in self.delegates:
            delegate.music_started_playing()

    def stop_music(self):
        """Arrête la musique"""
        self.__is_music_playing = False
        mixer.music.stop()
        for delegate in self.delegates:
            delegate.music_stopped_playing()

    @property
    def is_music_playing(self):
        """Renvoie si la musique joue ou pas (bool)"""
        return self.__is_music_playing

    def add_delegate(self, delegate: AmazonsSoundDelegate):
        """Ajoute un observateur à la liste d'observateurs"""
        self.delegates.append(delegate)

    def remove_delegate(self, delegate: AmazonsSoundDelegate) -> bool:
        """
        Supprime l'observateur delegate de la liste des observateurs et renvoie si l'observateur était dans la liste
        d'observateurs
        """
        try:
            self.delegates.remove(delegate)
        except ValueError:
            return False
        else:
            return True


# initialise l'instance globale de AmazonsSound
AmazonsSound.init_shared()
