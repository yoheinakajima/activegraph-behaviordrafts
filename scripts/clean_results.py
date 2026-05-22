from pathlib import Path

for p in Path("results").glob("*"):
    if p.name != ".gitkeep":
        p.unlink()
print("cleaned")
