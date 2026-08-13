from pathlib import Path
import shutil
import re

root = Path("winlator/app")


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected text not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


build = root / "app/build.gradle"
replace(build, "applicationId 'com.winlator'", "applicationId 'com.hikariro.mobile'")
build_text = build.read_text(encoding="utf-8")
build_text = re.sub(r"versionCode\s+\d+", "versionCode 7", build_text, count=1)
build_text = re.sub(r'versionName\s+"[^"]+"', 'versionName "0.7.0-beta"', build_text, count=1)
if "pickFirst '**/*.so'" not in build_text:
    build_text = build_text.replace(
        "android {",
        "android {\n    packagingOptions {\n        pickFirst '**/*.so'\n    }",
        1,
    )
build.write_text(build_text, encoding="utf-8")

app_utils = root / "app/src/main/java/com/winlator/core/AppUtils.java"
replace(
    app_utils,
    'public static final String INTERNAL_STORAGE = "/data/data/com.winlator/storage";',
    'public static final String INTERNAL_STORAGE = "/data/data/com.hikariro.mobile/storage";',
)

installer = root / "app/src/main/java/com/winlator/xenvironment/RootFSInstaller.java"
replace(installer, "import com.winlator.MainActivity;\n", "")
replace(installer, "install(final MainActivity activity)", "install(final AppCompatActivity activity)")
replace(installer, "installIfNeeded(final MainActivity activity)", "installIfNeeded(final AppCompatActivity activity)")

manifest = root / "app/src/main/AndroidManifest.xml"
replace(manifest, 'android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/hikariro_mobile_icon"')
replace(
    manifest,
    '<activity android:name="com.winlator.MainActivity"',
    '<activity android:name="com.winlator.HikariLauncherActivity"',
)
replace(
    manifest,
    'android:screenOrientation="sensor"\n            android:configChanges=',
    'android:screenOrientation="sensorLandscape"\n            android:configChanges=',
)
marker = "        <activity android:name=\"com.winlator.XServerDisplayActivity\""
replace(
    manifest,
    marker,
    '        <activity android:name="com.winlator.MainActivity"\n'
    '            android:theme="@style/AppThemeDark"\n'
    '            android:exported="false" />\n\n'
    + marker,
)

strings = root / "app/src/main/res/values/strings.xml"
text = strings.read_text(encoding="utf-8")
start = text.find('<string name="app_name">')
end = text.find("</string>", start)
if start < 0 or end < 0:
    raise RuntimeError("app_name was not found")
strings.write_text(
    text[:start] + '<string name="app_name">HikariRO Mobile' + text[end:],
    encoding="utf-8",
)

launcher_src = Path("mobile/HikariLauncherActivity.java")
launcher_dst = root / "app/src/main/java/com/winlator/HikariLauncherActivity.java"
launcher_dst.write_text(launcher_src.read_text(encoding="utf-8"), encoding="utf-8")

startup_src = Path("mobile/HikariStartupDialog.java")
startup_dst = root / "app/src/main/java/com/winlator/HikariStartupDialog.java"
startup_dst.write_text(startup_src.read_text(encoding="utf-8"), encoding="utf-8")

diagnostics_src = Path("mobile/HikariDiagnostics.java")
diagnostics_dst = root / "app/src/main/java/com/winlator/HikariDiagnostics.java"
diagnostics_dst.write_text(diagnostics_src.read_text(encoding="utf-8"), encoding="utf-8")

icon_src = Path("assets/hikariro-mobile-icon.png")
icon_dst = root / "app/src/main/res/drawable-nodpi/hikariro_mobile_icon.png"
icon_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(icon_src, icon_dst)

background_src = Path("assets/hikariro-launcher-background.png")
background_dst = root / "app/src/main/res/drawable-nodpi/hikariro_launcher_background.png"
shutil.copyfile(background_src, background_dst)

xserver = root / "app/src/main/java/com/winlator/XServerDisplayActivity.java"
replace(
    xserver,
    "final PreloaderDialog preloaderDialog = new PreloaderDialog(this);",
    "final HikariStartupDialog preloaderDialog = new HikariStartupDialog(this);",
)
replace(
    xserver,
    "setupWineSystemFiles();\n                extractGraphicsDriverFiles();\n                changeWineAudioDriver();",
    'preloaderDialog.setStageOnUiThread("Preparando archivos de Wine");\n'
    "                setupWineSystemFiles();\n"
    '                preloaderDialog.setStageOnUiThread("Inicializando el controlador gráfico");\n'
    "                extractGraphicsDriverFiles();\n"
    '                preloaderDialog.setStageOnUiThread("Configurando el audio");\n'
    "                changeWineAudioDriver();",
)
replace(
    xserver,
    "            setupXEnvironment();",
    '            preloaderDialog.setStageOnUiThread("Construyendo el entorno X11");\n'
    '            HikariDiagnostics.record(this, "Entrando en setupXEnvironment");\n'
    "            setupXEnvironment(preloaderDialog);",
)
replace(xserver, "private void setupXEnvironment() {", "private void setupXEnvironment(HikariStartupDialog preloaderDialog) {")
replace(
    xserver,
    "        environment = new XEnvironment(this, rootFS);",
    '        preloaderDialog.setStageOnUiThread("Creando servicios X11 y memoria compartida");\n'
    '        HikariDiagnostics.record(this, "Creando XEnvironment");\n'
    "        environment = new XEnvironment(this, rootFS);",
)
replace(
    xserver,
    "        environment.addComponent(new NetworkInfoUpdateComponent());\n\n        if (audioDriver.equals(AudioDrivers.ALSA)) {",
    "        environment.addComponent(new NetworkInfoUpdateComponent());\n\n"
    '        preloaderDialog.setStageOnUiThread("Configurando el servicio de audio");\n'
    '        HikariDiagnostics.record(this, "Configurando audio: " + audioDriver);\n'
    "        if (audioDriver.equals(AudioDrivers.ALSA)) {",
)
replace(
    xserver,
    "        if (graphicsDriver[0].equals(GraphicsDrivers.VORTEK)) {",
    '        preloaderDialog.setStageOnUiThread("Creando el renderizador gráfico compatible");\n'
    '        HikariDiagnostics.record(this, "Gráficos: " + graphicsDriver[0] + "," + graphicsDriver[1]);\n'
    "        if (graphicsDriver[0].equals(GraphicsDrivers.VORTEK)) {",
    )
replace(
    xserver,
    "        environment.startEnvironmentComponents();",
    '        preloaderDialog.setStageOnUiThread("Iniciando servicios y Box64");\n'
    '        HikariDiagnostics.record(this, "Antes de startEnvironmentComponents");\n'
    "        environment.startEnvironmentComponents();\n"
    '        HikariDiagnostics.record(this, "Después de startEnvironmentComponents");\n'
    '        HikariDiagnostics.processes(this);\n'
    '        preloaderDialog.setStageOnUiThread("Box64 iniciado; esperando la ventana del juego");',
)

guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
replace(guest, "import com.winlator.box64.Box64Preset;", "import com.winlator.box64.Box64Preset;\nimport com.winlator.HikariDiagnostics;")
replace(
    guest,
    "            pid = execGuestProgram();",
    '            HikariDiagnostics.record(environment.getContext(), "Solicitando proceso Box64");\n'
    "            pid = execGuestProgram();\n"
    '            HikariDiagnostics.record(environment.getContext(), "PID devuelto por Box64: " + pid);',
)

process_helper = root / "app/src/main/java/com/winlator/core/ProcessHelper.java"
replace(process_helper, "import com.winlator.MainActivity;", "import com.winlator.MainActivity;\nimport com.winlator.HikariDiagnostics;")
replace(
    process_helper,
    '            Field pidField = process.getClass().getDeclaredField("pid");\n'
    '            pidField.setAccessible(true);\n'
    '            pid = pidField.getInt(process);\n'
    '            pidField.setAccessible(false);',
    '            pid = (int)process.pid();',
)
replace(
    process_helper,
    "        catch (Exception e) {}\n        return pid;",
    '        catch (Exception e) {\n'
    '            HikariDiagnostics.record("ProcessHelper: " + e.getClass().getName() + ": " + e.getMessage());\n'
    '        }\n'
    '        return pid;',
)
