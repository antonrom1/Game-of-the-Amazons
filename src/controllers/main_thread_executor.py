from PyQt5.QtCore import QObject, pyqtSignal


class MainThreadExecutor(QObject):
    shared = None
    _signal = pyqtSignal()

    @classmethod
    def init_shared_executor(cls):
        if cls.shared is None:
            cls.shared = MainThreadExecutor()

    def __init__(self):
        super(MainThreadExecutor, self).__init__()
        self.main_thread_functions = []
        self._signal.connect(self._run)

    def run(self, f, *args, **kwargs):
        self.main_thread_functions.append((f, args, kwargs))
        self._signal.emit()

    def _run(self):
        while self.main_thread_functions:
            func, args, kwargs = self.main_thread_functions.pop(0)
            try:
                func(*args, **kwargs)
            except RuntimeError:
                continue


MainThreadExecutor.init_shared_executor()
