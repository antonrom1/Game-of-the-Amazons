import random
from abc import ABCMeta, abstractmethod
from const import *
from exceptions import *
from action import Action
import time
import matrix
from copy import deepcopy


class Player(metaclass=ABCMeta):
    """
    Classe abstraite représentant un joueur quelconque.

    Attributes:
        board (Board): le plateau de jeu sur lequel le joueur va effectuer ses actions
        player_id (int): l'id du joueur
    """

    def __init__(self, board, player_id):
        self.board = board
        self.player_id = player_id

    @abstractmethod
    def _play(self):
        pass

    def play(self):
        """
        Détermine l'action à effectuer et la joue sur le plateau
        """
        action = self._play()
        self.board.act(action)

    @property
    def other_player_id(self):
        """
        int: l'id du joueur adverse
        """
        return PLAYER_2 if self.player_id == PLAYER_1 else PLAYER_1


class HumanPlayer(Player):
    """
    Spécialisation de Player représentant un joueur humain
    """

    def __init__(self, board, player_id):
        super().__init__(board, player_id)

    def _play(self):
        """
        Récupère l'action désirée via stdin

        Returns:
            Action: l'action récupérée sur stdin
        """
        valid = False
        joueur = WHITE if self.player_id == 1 else BLACK

        while not valid:
            coup = input(MESSAGE_COUP.format('1' if self.player_id == PLAYER_1 else '2'))
            if coup.count('>') != 2:
                print(ERREUR_COUP)
                continue
            try:
                action = Action(*coup.split('>'), self.player_id)
                valid = self.board.is_valid_action(action)
            except InvalidActionError:
                continue
        return action


class MinimaxNode:
    def __init__(self, action=None, score=None):
        self.__score = score
        self.__action = action
        self.__children = []

    @property
    def score(self):
        return self.__score

    @score.setter
    def score(self, value):
        self.__score = value

    @property
    def action(self):
        return self.__action

    @action.setter
    def action(self, value):
        self.__action = value

    @property
    def children(self):
        return self.__children

    def __repr__(self):
        return f"Score: {self.score}, action: {self.action}, children: {self.children}"

