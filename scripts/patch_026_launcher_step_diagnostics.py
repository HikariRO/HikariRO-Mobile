from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
value = build.read_text(encoding="utf-8")
value = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("2600")', value, count=1)
value = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.26.0-launcher-step-diagnostics")', value, count=1)
build.write_text(value, encoding="utf-8")

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
value = guest.read_text(encoding="utf-8")
old = '''    @Override
    public void start() {
        synchronized (lock) {
            stop();
            extractBox64File();
            copyDefaultBox64RCFile();
            HikariDiagnostics.record(environment.getContext(), "Solicitando proceso Box64");
            pid = execGuestProgram();
            HikariDiagnostics.record(environment.getContext(), "PID devuelto por Box64: " + pid);
        }
    }'''
new = '''    @Override
    public void start() {
        Context context = environment.getContext();
        HikariDiagnostics.record(context, "GPL START: esperando lock; pid=" + pid);
        synchronized (lock) {
            HikariDiagnostics.record(context, "GPL LOCK adquirido; pid=" + pid);
            HikariDiagnostics.record(context, "GPL STOP BEGIN");
            stop();
            HikariDiagnostics.record(context, "GPL STOP END; pid=" + pid);
            HikariDiagnostics.record(context, "GPL EXTRACT BOX64 BEGIN");
            extractBox64File();
            HikariDiagnostics.record(context, "GPL EXTRACT BOX64 END");
            HikariDiagnostics.record(context, "GPL COPY BOX64RC BEGIN");
            copyDefaultBox64RCFile();
            HikariDiagnostics.record(context, "GPL COPY BOX64RC END");
            HikariDiagnostics.record(context, "GPL EXEC BEGIN: guest=" + guestExecutable);
            pid = execGuestProgram();
            HikariDiagnostics.record(context, "GPL EXEC END: pid=" + pid);
        }
        HikariDiagnostics.record(context, "GPL START END");
    }'''
if old not in value:
    raise RuntimeError("GuestProgramLauncherComponent.start from 0.25 was not found")
value = value.replace(old, new, 1)

old = '''    private int execGuestProgram() {
        RootFS rootFS = environment.getRootFS();
        File rootDir = rootFS.getRootDir();

        EnvVars envVars = new EnvVars();
        addBox64EnvVars(envVars);
        LocaleHelper.setEnvVars(envVars);'''
new = '''    private int execGuestProgram() {
        Context context = environment.getContext();
        HikariDiagnostics.record(context, "GPL EXEC: obteniendo RootFS");
        RootFS rootFS = environment.getRootFS();
        File rootDir = rootFS.getRootDir();
        HikariDiagnostics.record(context, "GPL EXEC: root=" + rootDir.getAbsolutePath());

        EnvVars envVars = new EnvVars();
        HikariDiagnostics.record(context, "GPL EXEC: Box64 env BEGIN");
        addBox64EnvVars(envVars);
        HikariDiagnostics.record(context, "GPL EXEC: Box64 env END");
        LocaleHelper.setEnvVars(envVars);
        HikariDiagnostics.record(context, "GPL EXEC: locale env END");'''
if old not in value:
    raise RuntimeError("execGuestProgram prologue from 0.25 was not found")
value = value.replace(old, new, 1)

old = '''        if (this.envVars != null) envVars.putAll(this.envVars);

        File shmDir = new File(rootDir, "/tmp/shm");
        if (!shmDir.isDirectory()) shmDir.mkdirs();'''
new = '''        if (this.envVars != null) envVars.putAll(this.envVars);
        HikariDiagnostics.record(context, "GPL EXEC: entorno completo; PATH=" + envVars.get("PATH"));

        File shmDir = new File(rootDir, "/tmp/shm");
        HikariDiagnostics.record(context, "GPL EXEC: SHM BEGIN; path=" + shmDir.getAbsolutePath());
        if (!shmDir.isDirectory()) {
            boolean created = shmDir.mkdirs();
            HikariDiagnostics.record(context, "GPL EXEC: SHM mkdirs=" + created);
        }
        HikariDiagnostics.record(context, "GPL EXEC: SHM END; dir=" + shmDir.isDirectory());'''
if old not in value:
    raise RuntimeError("SHM setup from 0.25 was not found")
value = value.replace(old, new, 1)

old = '''        return ProcessHelper.exec(command, envVars, rootDir, (status) -> {'''
new = '''        HikariDiagnostics.record(context, "GPL EXEC: ProcessHelper BEGIN");
        HikariDiagnostics.record(context, "GPL COMMAND: " + command);
        int launchedPid = ProcessHelper.exec(command, envVars, rootDir, (status) -> {'''
if old not in value:
    raise RuntimeError("ProcessHelper.exec call from 0.25 was not found")
value = value.replace(old, new, 1)

old = '''            if (terminationCallback != null) terminationCallback.call(status);
        });
    }'''
new = '''            HikariDiagnostics.record(context, "GPL CALLBACK: status=" + status);
            if (terminationCallback != null) terminationCallback.call(status);
        });
        HikariDiagnostics.record(context, "GPL EXEC: ProcessHelper END; pid=" + launchedPid);
        return launchedPid;
    }'''
if old not in value:
    raise RuntimeError("ProcessHelper.exec return tail from 0.25 was not found")
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
        value = re.sub(r"HikariRO Mobile 0\.(?:[0-9]+)(?:\.[0-9]+)?", "HikariRO Mobile 0.26", value)
        value = re.sub(r"Inicio del diagnóstico 0\.(?:[0-9]+)(?:\.[0-9]+)?", "Inicio del diagnóstico 0.26", value)
        path.write_text(value, encoding="utf-8")

print("0.26 GuestProgramLauncher step diagnostics applied")
