from pathlib import Path

wf = Path('winlator/app/.github/workflows/build-apk.yml')
# This script is intentionally a marker used by the outer repository workflow.
# The actual patches are applied from HikariRO-Mobile/scripts by build-apk.yml.
print('HikariRO Mobile 0.18 finalize marker')
