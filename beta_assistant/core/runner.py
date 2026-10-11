"""Asynchronous command execution worker with streaming output and privilege elevation."""

import os
import pty
import select
import subprocess
import threading
from typing import List, Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal


def can_run_sudo_non_interactive() -> bool:
    """Check if passwordless sudo is available."""
    try:
        res = subprocess.run(
            ["sudo", "-n", "true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return res.returncode == 0
    except Exception:
        return False


class ProcessWorker(QThread):
    """Worker thread running a subprocess and streaming its output in real-time."""

    line_output = pyqtSignal(str, bool)  # text, is_error
    finished = pyqtSignal(int, str)      # returncode, message
    started = pyqtSignal(str)            # command string

    def __init__(self, command: List[str], as_root: bool = False, cwd: Optional[str] = None):
        super().__init__()
        self.raw_command = command
        self.as_root = as_root
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

    def build_command(self) -> List[str]:
        if not self.as_root:
            return self.raw_command

        # If already root, run directly
        if os.geteuid() == 0:
            return self.raw_command

        # If passwordless sudo works, use sudo
        if can_run_sudo_non_interactive():
            return ["sudo"] + self.raw_command

        # Otherwise check if pkexec is available for GUI auth prompt
        if os.path.exists("/usr/bin/pkexec"):
            return ["pkexec"] + self.raw_command

        # Fallback to standard sudo
        return ["sudo"] + self.raw_command

    def cancel(self):
        """Cancel the running process."""
        self._is_cancelled = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def run(self):
        cmd = self.build_command()
        cmd_str = " ".join(cmd)
        self.started.emit(cmd_str)

        try:
            # Set environment for non-interactive apt commands
            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"
            env["PYTHONUNBUFFERED"] = "1"

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
                env=env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            def stream_pipe(pipe, is_err):
                try:
                    for line in iter(pipe.readline, ''):
                        if self._is_cancelled:
                            break
                        clean_line = line.rstrip('\r\n')
                        if clean_line:
                            self.line_output.emit(clean_line, is_err)
                except Exception:
                    pass
                finally:
                    pipe.close()

            # Start reading stdout and stderr concurrently
            t_out = threading.Thread(target=stream_pipe, args=(self.process.stdout, False))
            t_err = threading.Thread(target=stream_pipe, args=(self.process.stderr, True))
            t_out.daemon = True
            t_err.daemon = True
            t_out.start()
            t_err.start()

            # Wait for completion
            return_code = self.process.wait()
            t_out.join(timeout=2)
            t_err.join(timeout=2)

            if self._is_cancelled:
                self.finished.emit(-1, "Process cancelled by user.")
            elif return_code == 0:
                self.finished.emit(0, "Process completed successfully.")
            else:
                self.finished.emit(return_code, f"Process failed with exit code {return_code}.")

        except Exception as ex:
            self.line_output.emit(f"Error executing command: {ex}", True)
            self.finished.emit(1, str(ex))
