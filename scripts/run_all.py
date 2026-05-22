import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from behaviordrafts.harness import run_experiments
from behaviordrafts.llm_author import llm_available

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--llm", action="store_true")
    args = p.parse_args()
    if args.llm and not llm_available():
        print("Skipping --llm run: OPENAI_API_KEY is not set.")
        sys.exit(0)
    run_experiments(use_llm=args.llm)
    print("done")
