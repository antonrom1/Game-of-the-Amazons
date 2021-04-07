"""
Prénom:     Anton
Nom:        ROMANOVA
Matricule:  521935
"""

class InvalidFormatError(SyntaxError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class InvalidPositionError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class InvalidActionError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
