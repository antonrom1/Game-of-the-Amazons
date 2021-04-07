from PyQt5.QtCore import QObject, pyqtSignal


class MainThreadExecutor(QObject):
    """Permet d'exécuter des fonctions dans le thread principal à l'aide des signals de Qt"""
    shared = None
    _signal = pyqtSignal()

    def __init__(self):
        super(MainThreadExecutor, self).__init__()
        self.main_thread_functions = []
        self._signal.connect(self._run)

    @classmethod
    def init_shared_executor(cls):
        """Initialise l'instance partagée de MainThreadExecutor"""
        if cls.shared is None:
            cls.shared = MainThreadExecutor()

    def run(self, f, *args, **kwargs):
        """Exécute la fonction f avec les tous les arguments donnés"""
        self.main_thread_functions.append((f, args, kwargs))
        self._signal.emit()

    def _run(self):
        # exécute les fonctions qui sont dans la file déjà dans le main thread
        while self.main_thread_functions:
            func, args, kwargs = self.main_thread_functions.pop(0)
            try:
                func(*args, **kwargs)
            except RuntimeError:
                continue


MainThreadExecutor.init_shared_executor()  # permet d'initialiser l'instance partagée (shared) de MainThreadExecutor
