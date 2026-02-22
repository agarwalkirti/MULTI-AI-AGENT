#application entry point — it starts both backend (FastAPI) and frontend (Streamlit).
# subprocess Used to run external commands from Python. You use it to launch: uvicorn (backend server),streamlit (frontend UI),
# Equivalent to running these in terminal: "uvicorn app.backend.api:app --host 127.0.0.1 --port 9999 , streamlit run app/frontend/ui.py"
# threading : Allows running multiple tasks concurrently. Here: Backend runs in a separate thread,Frontend runs in main thread
# Without threading: Backend would block execution, Frontend would never start
# Run using : python -m app.main means: Treat app as a package, Add project root to sys.path, Resolve imports correctly, Without -m, Python runs it like a script and breaks package imports.

import subprocess
import threading
import time
import requests
from dotenv import load_dotenv
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
import os

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = "9999"
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/health"
#BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/docs"

# Start Backend (Uvicorn)
def run_backend():
    try:
        logger.info("Starting backend service...")

        subprocess.run(
            [
                "uvicorn",
                "app.backend.api:app",
                "--host",
                BACKEND_HOST,
                "--port",
                BACKEND_PORT,
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        logger.exception("Backend process crashed.")
        raise CustomException("Failed to start backend", e)

    except Exception as e:
        logger.exception("Unexpected backend error.")
        raise CustomException("Unexpected backend failure", e)

# Wait Until Backend is Ready
def wait_for_backend(timeout=15):
    logger.info("Waiting for backend to become ready...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(BACKEND_URL)
            if response.status_code == 200:
                logger.info("Backend is ready.")
                return
        except requests.ConnectionError:
            time.sleep(1)

    raise CustomException("Backend did not start within expected time.")

# Start Frontend (Streamlit)
def run_frontend():
    try:
        logger.info("Starting frontend service...")

        #path issue resolution
        project_root = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(project_root)
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root

        subprocess.run(
            ["streamlit", "run", "app/frontend/ui.py"],
            check=True,
            cwd=project_root,
            env=env
        )

    except subprocess.CalledProcessError as e:
        logger.exception("Frontend process crashed.")
        raise CustomException("Failed to start frontend", e)

    except Exception as e:
        logger.exception("Unexpected frontend error.")
        raise CustomException("Unexpected frontend failure", e)

# Main Execution
if __name__ == "__main__":
    try:
        # Start backend in daemon thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()

        # Wait until backend is healthy
        wait_for_backend()

        # Start frontend in main thread
        run_frontend()

    except CustomException as e:
        logger.exception(f"Startup failure: {str(e)}")

    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user.")
