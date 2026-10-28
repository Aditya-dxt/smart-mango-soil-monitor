import os, sys
from pathlib import Path
os.environ["MANGO_AUTOSTART"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
