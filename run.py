"""Start everything with one command:  .venv/bin/python run.py

Starts the backend if it is not already running, opens the app, and stops what it started.
"""
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
URL = "http://localhost:8080/api/v1/devices"
WINDOWS = platform.system() == "Windows"


def backend_up():
    try:
        urlopen(URL, timeout=2).close()
        return True
    except OSError:
        return False


def java_home():
    """JAVA_HOME if set, otherwise try to find JDK 25 on a Mac."""
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]
    for path in ("/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home",
                 "/usr/local/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home"):
        if Path(path).exists():
            return path
    return None


def start_backend():
    env = dict(os.environ)
    if java_home():
        env["JAVA_HOME"] = java_home()
    folder = ROOT / "cp317-backend"
    command = [str(folder / "mvnw.cmd"), "-q", "spring-boot:run"] if WINDOWS else ["sh", "mvnw", "-q", "spring-boot:run"]
    log = open(ROOT / "backend.log", "w")
    # its own process group, so Java is stopped together with Maven
    return subprocess.Popen(command, cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=not WINDOWS)


def stop(process):
    if process.poll() is not None:
        return
    if WINDOWS:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        os.killpg(process.pid, signal.SIGTERM)


def main():
    backend = None
    try:
        if not backend_up():
            print("Starting the backend (the first time can take a few minutes)...")
            backend = start_backend()
            deadline = time.time() + 300
            while not backend_up():
                if backend.poll() is not None or time.time() > deadline:
                    raise SystemExit("The backend did not start. See backend.log. Is JDK 25 installed?")
                time.sleep(1)
        subprocess.run([sys.executable, str(ROOT / "main" / "main.py")])
    finally:
        if backend:
            stop(backend)


if __name__ == "__main__":
    main()
