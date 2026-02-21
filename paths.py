from pathlib import Path
import json

def build_tree(path):
    if path.is_dir():
        return {path.name: [build_tree(p) for p in sorted(path.iterdir())]}
    else:
        return path.name

root = Path.cwd()  # start from current folder
tree = build_tree(root)

# Write to JSON file
with open("tree.json", "w", encoding="utf-8") as f:
    json.dump(tree, f, indent=2, ensure_ascii=False)

print("Tree saved to tree.json")