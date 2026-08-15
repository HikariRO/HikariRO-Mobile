from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2200")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.22.0-wine-preloader")', value, count=1)
build.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
value = guest.read_text(encoding="utf-8")
old = '''        if (guestExecutable.startsWith("wine ") && wineRealLoader.isFile()) {
            launchExecutable = wineRealLoader.getAbsolutePath() + guestExecutable.substring(4);
            HikariDiagnostics.record(environment.getContext(), "Wine wrapper sustituido; comando WinHandler conservado: " + launchExecutable);
        }'''
new = '''        File winePreloader = new File(rootDir, rootFS.getWinePath()+"/lib/wine/x86_64-unix/wine-preloader");
        HikariDiagnostics.record(environment.getContext(), "Wine preloader real: " + winePreloader.getAbsolutePath() + " exists=" + winePreloader.isFile() + " size=" + (winePreloader.isFile() ? winePreloader.length() : 0));
        if (guestExecutable.startsWith("wine ") && winePreloader.isFile() && wineRealLoader.isFile()) {
            launchExecutable = winePreloader.getAbsolutePath() + " " + wineRealLoader.getAbsolutePath() + guestExecutable.substring(4);
            HikariDiagnostics.record(environment.getContext(), "Cadena Wine preparada (preloader -> loader -> WinHandler): " + launchExecutable);
        }'''
if old not in value:
    raise RuntimeError("0.21 Wine loader block was not found")
guest.write_text(value.replace(old, new, 1), encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.22", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.22", value)
        path.write_text(value, encoding="utf-8")

print("0.22 Wine preloader chain applied")
