from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2500")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.25.0-box64-visible-trace")', value, count=1)
build.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
value = guest.read_text(encoding="utf-8")
old = 'envVars.put("BOX64_TRACE_FILE", traceDir+"/box64-%pid.txt");'
if old not in value:
    raise RuntimeError("BOX64 trace-file redirection was not found")
value = value.replace(old, 'envVars.put("BOX64_TRACE_FILE", "stderr");', 1)
guest.write_text(value, encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.25", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.25", value)
        path.write_text(value, encoding="utf-8")

print("0.25 Box64 trace redirected to visible stderr diagnostics")
