from pathlib import Path
# Executed after patch_018.py by workflows that glob patch_*.py alphabetically.
import subprocess
subprocess.check_call(['python3','scripts/patch_018_core_final.py'])
subprocess.check_call(['python3','scripts/patch_018_launcher.py'])
print('0.18 final patches chained')
