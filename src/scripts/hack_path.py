import sys
from pathlib import Path

p = Path(__file__).parent.parent


def hack_path():
    sys.path.insert(0, str(p))
