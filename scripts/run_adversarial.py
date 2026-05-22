import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviordrafts.adversarial import run_adversarial_experiments


if __name__ == "__main__":
    out = run_adversarial_experiments()
    print(out["summary"])
