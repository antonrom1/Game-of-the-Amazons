from PyQt5.QtCore import QObject, pyqtSignal


class MainThreadExecutor(QObject):
    shared = None
    _signal = pyqtSignal()

    def __init__(self):
        super(MainThreadExecutor, self).__init__()
        self._signal.connect(self._run)

    def run(self, f, *args, **kwargs):
        self.main_thread_func = f, args, kwargs
        self._signal.emit()

    def _run(self):
        if self.main_thread_func is None:
            return

        func, args, kwargs = self.main_thread_func
        self.main_thread_func = None

        func(*args, **kwargs)

    @classmethod
    def init_shared_executor(cls):
        if cls.shared is None:
            cls.shared = MainThreadExecutor()


MainThreadExecutor.init_shared_executor()
