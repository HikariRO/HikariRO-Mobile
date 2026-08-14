from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2300")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.23.0-box64-reexec")', value, count=1)
build.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
value = guest.read_text(encoding="utf-8")

# Revert 0.21/0.22 Wine-specific launch manipulation. Wine must receive the
# original Winlator command; the actual issue is Box64 re-exec, not Wine paths.
start = value.find('        String launchExecutable = guestExecutable;')
end = value.find('        String command;', start)
if start < 0 or end < 0:
    raise RuntimeError("Wine launch manipulation block was not found")
value = value[:start] + '        String launchExecutable = guestExecutable;\n\n' + value[end:]

old = '''            String libraryPath = rootDir+"/usr/lib:"+rootDir+"/lib:"+rootDir+"/usr/lib/aarch64-linux-gnu:"+rootDir+"/lib/aarch64-linux-gnu";
            command = nativeLoader.getAbsolutePath()+" --library-path "+libraryPath+" "+box64File.getAbsolutePath()+" "+launchExecutable;
            HikariDiagnostics.record(environment.getContext(), "Box64 se lanzará mediante loader explícito: " + nativeLoader.getAbsolutePath());'''
new = '''            String libraryPath = rootDir+"/usr/lib:"+rootDir+"/lib:"+rootDir+"/usr/lib/aarch64-linux-gnu:"+rootDir+"/lib/aarch64-linux-gnu";
            File box64Wrapper = new File(rootDir, "/usr/local/bin/box64-android-wrapper");
            String wrapperScript = "#!/system/bin/sh\\nexec \\"" + nativeLoader.getAbsolutePath() +
                "\\" --argv0 \\"" + box64Wrapper.getAbsolutePath() +
                "\\" --library-path \\"" + libraryPath +
                "\\" \\"" + box64File.getAbsolutePath() + "\\" \\"$@\\"\\n";
            if (!FileUtils.writeString(box64Wrapper, wrapperScript)) {
                throw new RuntimeException("No se pudo crear box64-android-wrapper");
            }
            box64Wrapper.setReadable(true, false);
            box64Wrapper.setExecutable(true, false);
            command = nativeLoader.getAbsolutePath()+" --argv0 "+box64Wrapper.getAbsolutePath()+" --library-path "+libraryPath+" "+box64File.getAbsolutePath()+" "+launchExecutable;
            HikariDiagnostics.record(environment.getContext(), "Box64 loader inicial: " + nativeLoader.getAbsolutePath());
            HikariDiagnostics.record(environment.getContext(), "Box64 reexec wrapper: " + box64Wrapper.getAbsolutePath() + " exists=" + box64Wrapper.isFile() + " exec=" + box64Wrapper.canExecute() + " size=" + box64Wrapper.length());'''
if old not in value:
    raise RuntimeError("Explicit ARM64 loader block was not found")
value = value.replace(old, new, 1)
guest.write_text(value, encoding="utf-8")

for rel in (
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
):
    path = root / rel
    if path.exists():
        value = path.read_text(encoding="utf-8")
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.23", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.23", value)
        path.write_text(value, encoding="utf-8")

print("0.23 Box64 Android re-exec wrapper applied; normal Wine command restored")
