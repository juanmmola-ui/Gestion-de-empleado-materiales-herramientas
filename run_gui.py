import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path
import uvicorn

if getattr(sys, "frozen", False):
    _log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GestionPanol"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = open(_log_dir / "gestion_panol.log", "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = _log_file
    if sys.stderr is None:
        sys.stderr = _log_file

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

HOST = "127.0.0.1"


def _buscar_puerto_libre(host: str = HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


PORT = _buscar_puerto_libre()
API_URL = f"http://{HOST}:{PORT}"
os.environ["GESTION_PANOL_API_URL"] = API_URL

from app.main import app as fastapi_app
from frontend.app import MainWindow


def _iniciar_servidor():
    config = uvicorn.Config(
        fastapi_app,
        host=HOST,
        port=PORT,
        reload=False,
        loop="asyncio",
        http="h11",
        ws="none",
        log_config=None,
    )
    server = uvicorn.Server(config)
    try:
        server.run()
    except SystemExit:
        pass


def _esperar_api(timeout: float = 15.0) -> bool:
    inicio = time.time()
    url = f"{API_URL}/openapi.json"
    while time.time() - inicio < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


if __name__ == "__main__":
    hilo_api = threading.Thread(target=_iniciar_servidor, name="FastAPIThread", daemon=True)
    hilo_api.start()

    if not _esperar_api():
        raise RuntimeError(f"El servidor FastAPI no respondió en {API_URL} al iniciar.")

    win = MainWindow()
    win.mainloop()