"""Generic non-blocking asynchronous task execution with lifetime tracking."""

import sys
import threading
from typing import Callable, Any, Optional, Set
from PyQt6.QtCore import QThread, pyqtSignal, QObject


class WorkerThread(QThread):
    """Executes a callable in a background thread and emits results safely."""

    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    finished_task = pyqtSignal()

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return
            res = self.func(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.result_ready.emit(res)
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
        finally:
            self.finished_task.emit()


class AsyncRunner(QObject):
    """Orchestrates background tasks while keeping references alive until completion."""

    _active_workers: Set[WorkerThread] = set()
    _lock = threading.Lock()

    @classmethod
    def run(cls, func: Callable, on_success: Optional[Callable[[Any], None]] = None,
            on_error: Optional[Callable[[str], None]] = None,
            on_finish: Optional[Callable[[], None]] = None,
            *args, **kwargs) -> WorkerThread:
        worker = WorkerThread(func, *args, **kwargs)

        with cls._lock:
            cls._active_workers.add(worker)

        def _on_worker_completed():
            with cls._lock:
                cls._active_workers.discard(worker)
            if on_finish:
                try:
                    on_finish()
                except Exception:
                    pass

        if on_success:
            worker.result_ready.connect(on_success)
        if on_error:
            worker.error_occurred.connect(on_error)

        worker.finished_task.connect(_on_worker_completed)
        worker.start()
        return worker

    @classmethod
    def stop_all(cls):
        """Cancel and join all active background workers on shutdown."""
        with cls._lock:
            workers = list(cls._active_workers)
            for w in workers:
                try:
                    w.cancel()
                    w.wait(400)
                except Exception:
                    pass
            cls._active_workers.clear()
