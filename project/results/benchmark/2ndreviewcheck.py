import json
data = json.load(open("c:/Users/rhith/Downloads/llm-diff-bugfinder/project/results/benchmark/benchmark_bugs.json"))
bad = [b for b in data if "Unknown" in b["minimized_counterexample"] or b["raw_counterexample"].strip() == "Given: (),"]
print(f"{len(bad)} / {len(data)} entries have no real counterexample")