from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2400")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.24.0-component-diagnostics")', value, count=1)
build.write_text(value, encoding="utf-8")

xenv = root / "app/src/main/java/com/winlator/xenvironment/XEnvironment.java"
value = xenv.read_text(encoding="utf-8")
if "import com.winlator.HikariDiagnostics;" not in value:
    value = value.replace("import com.winlator.core.FileUtils;", "import com.winlator.core.FileUtils;\nimport com.winlator.HikariDiagnostics;", 1)
old = '''    public void startEnvironmentComponents() {
        FileUtils.clear(getTmpDir());
        for (EnvironmentComponent environmentComponent : this) environmentComponent.start();
    }'''
new = '''    public void startEnvironmentComponents() {
        HikariDiagnostics.record(context, "XENV TMP CLEAR BEGIN: " + getTmpDir().getAbsolutePath());
        FileUtils.clear(getTmpDir());
        HikariDiagnostics.record(context, "XENV TMP CLEAR END");
        int index = 0;
        for (EnvironmentComponent environmentComponent : this) {
            index++;
            String name = environmentComponent.getClass().getSimpleName();
            HikariDiagnostics.record(context, "COMPONENT START #" + index + ": " + name);
            try {
                environmentComponent.start();
                HikariDiagnostics.record(context, "COMPONENT OK #" + index + ": " + name);
            }
            catch (Throwable error) {
                HikariDiagnostics.record(context, "COMPONENT ERROR #" + index + ": " + name + " -> " + error.getClass().getName() + ": " + error.getMessage());
                for (StackTraceElement frame : error.getStackTrace()) {
                    HikariDiagnostics.record(context, "  at " + frame.toString());
                }
                throw error;
            }
        }
    }'''
if old not in value:
    raise RuntimeError("XEnvironment.startEnvironmentComponents was not found")
xenv.write_text(value.replace(old, new, 1), encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.24", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.24", value)
        path.write_text(value, encoding="utf-8")

print("0.24 component diagnostics applied")
