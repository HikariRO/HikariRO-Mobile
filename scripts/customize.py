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
build_text = re.sub(r"versionCode\s+\d+", "versionCode 4", build_text, count=1)
build_text = re.sub(r'versionName\s+"[^"]+"', 'versionName "0.4.0-beta"', build_text, count=1)
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

icon_src = Path("assets/hikariro-mobile-icon.png")
icon_dst = root / "app/src/main/res/drawable-nodpi/hikariro_mobile_icon.png"
icon_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(icon_src, icon_dst)

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
    '            preloaderDialog.setStageOnUiThread("Iniciando Box64 y raghikari.exe");\n'
    "            setupXEnvironment();",
)
