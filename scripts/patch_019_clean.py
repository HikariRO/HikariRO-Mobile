from pathlib import Path
import re


root = Path("winlator/app")

# 0.19 deliberately keeps Winlator's normal Wine/WinHandler launch path.
# Only the ARM64 Android loader workaround from patch_010.py is applied before
# this script. The direct Wine-loader experiments from 0.13-0.18 are excluded.
build = root / "app/build.gradle"
text_value = build.read_text(encoding="utf-8")
text_value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("1900")', text_value, count=1)
text_value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.19.0-clean")', text_value, count=1)
build.write_text(text_value, encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.19", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.19", value)
        path.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
guest_text = guest.read_text(encoding="utf-8")
for forbidden in (
    "direct Wine launch habilitado",
    "x86_64-unix/wine cmd /c",
    "launchExecutable",
):
    if forbidden in guest_text:
        raise RuntimeError(f"0.19 clean build contains forbidden legacy launcher patch: {forbidden}")

if "guestExecutable" not in guest_text:
    raise RuntimeError("Winlator normal guest launch path was not found")

print("0.19 clean patch applied; normal Winlator Wine launch preserved")
