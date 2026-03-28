import subprocess
import sys

from agentic_trader import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "agentic_trader", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
