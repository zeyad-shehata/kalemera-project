import sys
from pathlib import Path

# Add project root and backend directory to sys.path so app modules can be imported
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import the FastAPI application instance
from app.main import app
