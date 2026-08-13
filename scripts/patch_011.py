from pathlib import Path
import re
from PIL import Image

root = Path("winlator/app")

build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("11")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.11.0-beta")', text, count=1)
build.write_text(text, encoding="utf-8")

# Strip metadata from the generated background resource. Some Android decoders fail on the original PNG metadata.
bg = root / "app/src/main/res/drawable-nodpi/hikariro_launcher_background.png"
img = Image.open(bg).convert("RGB")
img.save(bg, format="PNG", optimize=False)

# Fix Android Process PID retrieval. java.lang.Process.pid() is not available on this Android runtime.
process_helper = root / "app/src/main/java/com/winlator/core/ProcessHelper.java"
text = process_helper.read_text(encoding="utf-8")
old = '''            java.lang.reflect.Method pidMethod = java.lang.Process.class.getMethod("pid");
            pid = ((Long)pidMethod.invoke(process)).intValue();'''
new = '''            HikariDiagnostics.record("Process implementation: " + process.getClass().getName());
            Class<?> pidClass = process.getClass();
            Field pidField = null;
            while (pidClass != null && pidField == null) {
                try { pidField = pidClass.getDeclaredField("pid"); }
                catch (NoSuchFieldException ignored) { pidClass = pidClass.getSuperclass(); }
            }
            if (pidField == null) throw new NoSuchFieldException("pid");
            pidField.setAccessible(true);
            pid = pidField.getInt(process);
            pidField.setAccessible(false);
            HikariDiagnostics.record("PID Android obtenido por reflexión: " + pid);'''
if old not in text:
    raise RuntimeError("No se encontró el bloque Process.pid() de la 0.10")
text = text.replace(old, new, 1)
process_helper.write_text(text, encoding="utf-8")

# 0.11 diagnostic/version markers and background diagnostics.
diagnostics = root / "app/src/main/java/com/winlator/HikariDiagnostics.java"
text = diagnostics.read_text(encoding="utf-8")
for oldv in ("0.7", "0.8", "0.9", "0.10"):
    text = text.replace("Inicio del diagnóstico " + oldv, "Inicio del diagnóstico 0.11")
diagnostics.write_text(text, encoding="utf-8")

startup = root / "app/src/main/java/com/winlator/HikariStartupDialog.java"
text = startup.read_text(encoding="utf-8")
for oldv in ("0.7", "0.8", "0.9", "0.10"):
    text = text.replace("HikariRO Mobile " + oldv + "\\n", "HikariRO Mobile 0.11\\n")
text = text.replace(
'''        background.setImageResource(R.drawable.hikariro_launcher_background);
        background.setScaleType(ImageView.ScaleType.CENTER_CROP);''',
'''        background.setImageResource(R.drawable.hikariro_launcher_background);
        background.setScaleType(ImageView.ScaleType.CENTER_CROP);
        if (background.getDrawable() != null) {
            HikariDiagnostics.record(activity, "Fondo cargado: " + background.getDrawable().getIntrinsicWidth() + "x" + background.getDrawable().getIntrinsicHeight());
        } else {
            HikariDiagnostics.record(activity, "Fondo NO cargado: drawable=null");
        }''', 1)
# Remove the tint completely while diagnosing the black background.
text = text.replace('shade.setBackgroundColor(0x33030b1d);', 'shade.setBackgroundColor(Color.TRANSPARENT);', 1)
startup.write_text(text, encoding="utf-8")

xserver = root / "app/src/main/java/com/winlator/XServerDisplayActivity.java"
text = xserver.read_text(encoding="utf-8")
text = text.replace("Box64 preparado; iniciando Wine y esperando la ventana del juego", "Box64 en ejecución; iniciando Wine y esperando la ventana del juego")
xserver.write_text(text, encoding="utf-8")
