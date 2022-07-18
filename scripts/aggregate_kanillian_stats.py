import argparse
import os
import json
from pathlib import Path

stats = {
    "at_compilation": {},
    "successes": 0,
    "verification_failures": 0,
    "unhandled_failures": {},
    "unknown": 0,
    "gillian_failures": 0,
}

def add_exec_stats(file):
    with open(file, 'r') as f:
        obj = json.load(f)

    for key in ["successes", "verification_failures", "unknown", "gillian_failures"]:
        stats[key] += obj[key]
    for feature in obj["unhandled_failures"]:
        if feature not in stats["unhandled_failures"]:
            stats["unhandled_failures"][feature] = 0
        stats["unhandled_failures"][feature] += obj["unhandled_failures"][feature]


def add_compile_stats(file):
    with open(file, 'r') as f:
        obj = json.load(f)

    for feature in obj["at_compilation"]:
        if feature not in stats["at_compilation"]:
            stats["at_compilation"][feature] = 0
        stats["at_compilation"][feature] += obj["at_compilation"][feature]


parser = argparse.ArgumentParser(description='Walk through a folder and aggregate kanillian stats')
parser.add_argument('path', metavar="FOLDER", type=Path,
                    help='Folder to walk for stats files')
args = parser.parse_args()

for root, subdirs, files in os.walk(args.path):
    for file in files:
        if file.endswith("compile_stats.json"):
            add_compile_stats(Path(root) / file)
        elif file.endswith("exec_stats.json"):
            add_exec_stats(Path(root) / file)


with open("final_stats.json", "w") as f:
    json.dump(stats, f)
