"""
run_scope_eval.py
═════════════════════════════════════════════════════════════════════════════════
Accuracy check for the Phase 3 scope gate (scope.classify_scope).

Loads scope_eval_dataset.json (query → expected label), classifies each query,
and reports overall + per-category accuracy. Fast — uses the lightweight model,
no SQL generation or DB access.

Usage:
    python run_scope_eval.py
═════════════════════════════════════════════════════════════════════════════════
"""
import json
import os
from collections import defaultdict

from scope import classify_scope

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "scope_eval_dataset.json")


def main():
    dataset = json.load(open(DATASET_PATH))
    total = len(dataset)
    passed = 0
    per_cat = defaultdict(lambda: [0, 0])  # expected -> [correct, count]

    print("\n" + "═" * 80)
    print("  🧭  SCOPE GATE EVALUATION")
    print("═" * 80)

    for item in dataset:
        q, exp = item["query"], item["expected"]
        got = classify_scope(q)["scope"]
        ok = got == exp
        passed += ok
        per_cat[exp][0] += ok
        per_cat[exp][1] += 1
        print(f"  {'✅' if ok else '❌'} got={got:11} exp={exp:11} | {q}")

    print("─" * 80)
    print(f"  Accuracy: {passed}/{total}  ({passed / total * 100:.1f}%)")
    print("  Per category:")
    for cat, (c, n) in sorted(per_cat.items()):
        print(f"    {cat:12} {c}/{n}")
    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
