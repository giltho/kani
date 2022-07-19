import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser(description='Walk through a folder clean all artifacts of tests')
parser.add_argument('path', metavar="FOLDER", type=Path,
                    help='Folder to walk for stats files')
args = parser.parse_args()

counter = 0

for root, subdirs, files in os.walk(args.path):
    for file in files:
        if file.endswith(".json") or file.endswith(".rlib") or file.endswith(".gil") or file.endswith(
                ".out") or file.endswith(".cbmc_output") or file.endswith(".stdout") or file.endswith(".for-main"):
            os.remove(Path(root) / file)
            counter += 1

print(f"CLEANED {counter} files")
