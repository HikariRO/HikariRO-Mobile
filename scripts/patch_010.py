from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("10")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.10.0-beta")', text, count=1)
build.write_text(text, encoding="utf-8")

diagnostics = root / "app/src/main/java/com/winlator/HikariDiagnostics.java"
text = diagnostics.read_text(encoding="utf-8")
for old in ("Inicio del diagnóstico 0.7", "Inicio del diagnóstico 0.8", "Inicio del diagnóstico 0.9"):
    text = text.replace(old, "Inicio del diagnóstico 0.10")
diagnostics.write_text(text, encoding="utf-8")

startup = root / "app/src/main/java/com/winlator/HikariStartupDialog.java"
text = startup.read_text(encoding="utf-8")
for old in ("HikariRO Mobile 0.7\\n", "HikariRO Mobile 0.8\\n", "HikariRO Mobile 0.9\\n"):
    text = text.replace(old, "HikariRO Mobile 0.10\\n")
startup.write_text(text, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
text = guest.read_text(encoding="utf-8")
old = '        String command = rootDir+"/usr/local/bin/box64 "+guestExecutable;'
new = '''        File box64File = new File(rootDir, "/usr/local/bin/box64");
        String[] loaderCandidates = {
            "/usr/lib/ld-linux-aarch64.so.1",
            "/lib/ld-linux-aarch64.so.1",
            "/lib64/ld-linux-aarch64.so.1",
            "/usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1",
            "/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1"
        };
        File nativeLoader = null;
        for (String candidate : loaderCandidates) {
            File test = new File(rootDir, candidate);
            HikariDiagnostics.record(environment.getContext(), "Loader candidato: " + test.getAbsolutePath() + " exists=" + test.isFile() + " size=" + (test.isFile() ? test.length() : 0));
            if (nativeLoader == null && test.isFile()) nativeLoader = test;
        }

        String command;
        if (nativeLoader != null) {
            nativeLoader.setReadable(true, false);
            nativeLoader.setExecutable(true, false);
            String libraryPath = rootDir+"/usr/lib:"+rootDir+"/lib:"+rootDir+"/usr/lib/aarch64-linux-gnu:"+rootDir+"/lib/aarch64-linux-gnu";
            command = nativeLoader.getAbsolutePath()+" --library-path "+libraryPath+" "+box64File.getAbsolutePath()+" "+guestExecutable;
            HikariDiagnostics.record(environment.getContext(), "Box64 se lanzará mediante loader explícito: " + nativeLoader.getAbsolutePath());
        }
        else {
            command = box64File.getAbsolutePath()+" "+guestExecutable;
            HikariDiagnostics.record(environment.getContext(), "No se encontró loader ARM64 en rootfs; usando ejecución directa");
        }'''
if old not in text:
    raise RuntimeError("No se encontró la construcción original del comando Box64")
text = text.replace(old, new, 1)
guest.write_text(text, encoding="utf-8")

xserver = root / "app/src/main/java/com/winlator/XServerDisplayActivity.java"
text = xserver.read_text(encoding="utf-8")
text = text.replace("Box64 solicitado; verificando proceso y esperando la ventana del juego", "Box64 preparado; iniciando Wine y esperando la ventana del juego")
xserver.write_text(text, encoding="utf-8")
