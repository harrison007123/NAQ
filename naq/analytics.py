import webbrowser
from pathlib import Path
html_path = Path(__file__).resolve().parent.parent / "web_module" / "index.html"






def launch_dashboard():
    webbrowser.open(f"http://localhost:3000")