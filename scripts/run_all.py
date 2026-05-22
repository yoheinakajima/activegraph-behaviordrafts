import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviordrafts.harness import run_experiments

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--llm", action="store_true")
    args = p.parse_args()
    run_experiments(use_llm=args.llm)
    print("done")
