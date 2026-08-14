from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2100")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.21.0-wine-loader")', value, count=1)
build.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
value = guest.read_text(encoding="utf-8")
marker = '''        String command;
        if (nativeLoader != null) {'''
insertion = '''        String launchExecutable = guestExecutable;
        File wineRealLoader = new File(rootDir, rootFS.getWinePath()+"/lib/wine/x86_64-unix/wine");
        HikariDiagnostics.record(environment.getContext(), "Wine loader real: " + wineRealLoader.getAbsolutePath() + " exists=" + wineRealLoader.isFile() + " size=" + (wineRealLoader.isFile() ? wineRealLoader.length() : 0));
        if (guestExecutable.startsWith("wine ") && wineRealLoader.isFile()) {
            launchExecutable = wineRealLoader.getAbsolutePath() + guestExecutable.substring(4);
            HikariDiagnostics.record(environment.getContext(), "Wine wrapper sustituido; comando WinHandler conservado: " + launchExecutable);
        }

        String command;
        if (nativeLoader != null) {'''
if marker not in value:
    raise RuntimeError("ARM64 loader command marker was not found")
value = value.replace(marker, insertion, 1)
value = value.replace('+" "+guestExecutable;', '+" "+launchExecutable;', 1)
value = value.replace('box64File.getAbsolutePath()+" "+guestExecutable;', 'box64File.getAbsolutePath()+" "+launchExecutable;', 1)
guest.write_text(value, encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.21", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.21", value)
        path.write_text(value, encoding="utf-8")

print("0.21 real Wine loader applied; explorer and WinHandler arguments preserved")
