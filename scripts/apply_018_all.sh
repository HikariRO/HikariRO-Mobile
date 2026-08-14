#!/usr/bin/env bash
set -euo pipefail
python3 scripts/patch_018.py
python3 scripts/patch_018_core_final.py
python3 scripts/patch_018_launcher.py
