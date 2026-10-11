"""Unit tests for asynchronous non-blocking worker engine."""

import os
import unittest
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from beta_assistant.core.async_worker import AsyncRunner


class TestAsyncWorker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_async_runner_success(self):
        result_holder = []

        def slow_calc(x, y):
            return x * y + 42

        def on_done(val):
            result_holder.append(val)

        worker = AsyncRunner.run(slow_calc, on_success=on_done, x=10, y=5)
        worker.wait(2000)
        self.app.processEvents()

        self.assertEqual(len(result_holder), 1)
        self.assertEqual(result_holder[0], 92)


if __name__ == "__main__":
    unittest.main()
