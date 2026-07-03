"""Launch the bundled Streamlit application on Windows."""

from pathlib import Path
import sys

from dotenv import load_dotenv
from streamlit.web import cli as streamlit_cli


def bundled_path(filename: str) -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / filename


load_dotenv(bundled_path(".env"), override=False)

# Keep this import after loading the bundled environment and make application
# imports visible to PyInstaller.
import main  # noqa: E402,F401


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        str(bundled_path("main.py")),
        "--global.developmentMode=false",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(streamlit_cli.main())
