import os
import sys
import logging
import subprocess
import threading
import webbrowser
import time
import requests

LOGGING = False

script_dir = os.path.dirname(os.path.abspath(__file__))

if LOGGING:
    log_file = os.path.join(script_dir, "server_log.txt")
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("Script started.")
else:
    logging.disable(logging.CRITICAL)

backend_proc = None
frontend_proc = None


def wait_for_service(url, interval=0.2, timeout=30):
    """Ping a given URL until a successful HTTP response is received."""
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        if time.time() - start_time > timeout:
            print(f"Timeout: Service at {url} did not start within {timeout} seconds.")
            return False
        time.sleep(interval)


def start_backend():
    """Start the backend using the virtual environment inside /backend."""
    global backend_proc
    backend_path = os.path.join(script_dir, "backend")

    if os.name == "nt":
        venv_python = os.path.join(backend_path, "venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(backend_path, "venv", "bin", "python")

    if not os.path.exists(venv_python):
        print("Error: backend/venv Python not found.")
        sys.exit(1)

    backend_log = open(os.path.join(script_dir, "backend_log.txt"), "w") if LOGGING else subprocess.DEVNULL

    backend_cmd = [venv_python, "-m", "uvicorn", "main:app", "--port", "50005"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=backend_path,
        stdout=backend_log,
        stderr=backend_log
    )

    print("Starting backend...")
    if wait_for_service("http://localhost:50005/docs"):
        print("Backend is up.")
    else:
        print("Backend failed to start.")
        sys.exit(1)


def start_frontend():
    """Start the frontend using npm run start."""
    global frontend_proc
    frontend_path = os.path.join(script_dir, "frontend")

    frontend_log = open(os.path.join(script_dir, "frontend_log.txt"), "w") if LOGGING else subprocess.DEVNULL

    if os.name == "nt":
        frontend_cmd = "npm run start"
    else:
        frontend_cmd = ["npm", "run", "start"]

    print("Starting frontend...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_path,
        shell=True if os.name == "nt" else False,
        stdout=frontend_log,
        stderr=frontend_log
    )

    if wait_for_service("http://localhost:50004/"):
        print("Frontend is up.")
    else:
        print("Frontend failed to start.")
        sys.exit(1)


def stop_servers():
    """Stop backend and frontend gracefully."""
    global backend_proc, frontend_proc
    print("Stopping servers...")

    try:
        if frontend_proc:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=5)
            print("Frontend stopped.")
        if backend_proc:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
            print("Backend stopped.")
    except Exception as e:
        print(f"Error stopping servers: {e}")

    if os.name == "nt":
        force_kill_ports()


def force_kill_ports():
    """Forcefully kill processes on ports 50004 and 50005 (Windows only)."""
    ports = [50004, 50005]
    for port in ports:
        try:
            cmd = f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /PID %a /F'
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            pass


def main():
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.start()
    backend_thread.join()

    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.start()
    frontend_thread.join()

    print("Opening dashboard...")
    webbrowser.open("http://localhost:50004")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_servers()
        print("Servers stopped. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
