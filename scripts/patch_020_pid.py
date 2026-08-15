from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2000")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.20.0-pid-fix")', value, count=1)
build.write_text(value, encoding="utf-8")

process_helper = root / "app/src/main/java/com/winlator/core/ProcessHelper.java"
value = process_helper.read_text(encoding="utf-8")
old = '''            java.lang.reflect.Method pidMethod = java.lang.Process.class.getMethod("pid");
            pid = ((Long)pidMethod.invoke(process)).intValue();'''
new = '''            HikariDiagnostics.record("Process implementation: " + process.getClass().getName());
            Class<?> pidClass = process.getClass();
            Field pidField = null;
            while (pidClass != null && pidField == null) {
                try {
                    pidField = pidClass.getDeclaredField("pid");
                }
                catch (NoSuchFieldException ignored) {
                    pidClass = pidClass.getSuperclass();
                }
            }
            if (pidField == null) throw new NoSuchFieldException("pid");
            pidField.setAccessible(true);
            pid = pidField.getInt(process);
            pidField.setAccessible(false);
            HikariDiagnostics.record("PID Android obtenido por reflexión: " + pid);'''
if old not in value:
    raise RuntimeError("Android Process.pid() block was not found")
process_helper.write_text(value.replace(old, new, 1), encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.20", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.20", value)
        path.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
guest_value = guest.read_text(encoding="utf-8")
for forbidden in ("direct Wine launch habilitado", "x86_64-unix/wine cmd /c", "launchExecutable"):
    if forbidden in guest_value:
        raise RuntimeError(f"Forbidden legacy launcher patch: {forbidden}")

print("0.20 PID fix applied; normal Winlator Wine launch preserved")
