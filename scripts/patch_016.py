from pathlib import Path
import re
import shutil

from PIL import Image, ImageFilter

root = Path("winlator/app")

# Version metadata.
build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("1600")', text, count=1)
text = re.sub(r"versionName\s+[^\n]+", 'versionName String.valueOf("0.16.0-beta")', text, count=1)
build.write_text(text, encoding="utf-8")

for rel in [
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
]:
    p = root / rel
    s = p.read_text(encoding="utf-8")
    s = s.replace("0.15.1", "0.16")
    s = s.replace("0.15 loader Wine real habilitado", "0.16 loader Wine real habilitado")
    p.write_text(s, encoding="utf-8")

# Instrument every XEnvironment component so a crash before GuestProgramLauncher
# tells us exactly which service fails on the device.
xenv = root / "app/src/main/java/com/winlator/xenvironment/XEnvironment.java"
s = xenv.read_text(encoding="utf-8")
if "import com.winlator.HikariDiagnostics;" not in s:
    s = s.replace(
        "import com.winlator.core.FileUtils;",
        "import com.winlator.core.FileUtils;\nimport com.winlator.HikariDiagnostics;",
        1,
    )
old = '''    public void startEnvironmentComponents() {
        FileUtils.clear(getTmpDir());
        for (EnvironmentComponent environmentComponent : this) environmentComponent.start();
    }'''
new = '''    public void startEnvironmentComponents() {
        FileUtils.clear(getTmpDir());
        int index = 0;
        for (EnvironmentComponent environmentComponent : this) {
            index++;
            String name = environmentComponent.getClass().getSimpleName();
            HikariDiagnostics.record(context, "COMPONENT START #" + index + ": " + name);
            try {
                environmentComponent.start();
                HikariDiagnostics.record(context, "COMPONENT OK #" + index + ": " + name);
            }
            catch (Throwable t) {
                HikariDiagnostics.record(context, "COMPONENT FAIL #" + index + ": " + name + " -> " + t.getClass().getName() + ": " + String.valueOf(t.getMessage()));
                StackTraceElement[] trace = t.getStackTrace();
                for (int i = 0; i < trace.length && i < 24; i++) {
                    HikariDiagnostics.record(context, "  at " + trace[i].toString());
                }
                Throwable cause = t.getCause();
                if (cause != null) {
                    HikariDiagnostics.record(context, "CAUSE: " + cause.getClass().getName() + ": " + String.valueOf(cause.getMessage()));
                }
                if (t instanceof RuntimeException) throw (RuntimeException)t;
                if (t instanceof Error) throw (Error)t;
                throw new RuntimeException(t);
            }
        }
    }'''
if old not in s:
    raise RuntimeError("No se encontro startEnvironmentComponents original")
s = s.replace(old, new, 1)
xenv.write_text(s, encoding="utf-8")

# Rebuild the background from the original repository asset instead of the
# stretched 0.14 derivative. Preserve aspect ratio and use high-quality Lanczos
# scaling + a restrained unsharp mask. No non-uniform stretching is performed.
source = Path("assets/hikariro-launcher-background.png")
dest = root / "app/src/main/res/drawable-nodpi/hikariro_launcher_background.png"
if not source.is_file():
    raise RuntimeError("Falta assets/hikariro-launcher-background.png")
img = Image.open(source).convert("RGB")

# The original asset is already almost exactly 16:9. Crop only the tiny excess
# required to reach exact 16:9, then upscale uniformly to 2560x1440.
w, h = img.size
target_ratio = 16 / 9
ratio = w / h
if ratio > target_ratio:
    new_w = round(h * target_ratio)
    left = (w - new_w) // 2
    img = img.crop((left, 0, left + new_w, h))
elif ratio < target_ratio:
    new_h = round(w / target_ratio)
    top = (h - new_h) // 2
    img = img.crop((0, top, w, top + new_h))

img = img.resize((2560, 1440), Image.Resampling.LANCZOS)
img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=115, threshold=3))
dest.parent.mkdir(parents=True, exist_ok=True)
img.save(dest, "PNG", optimize=True)

# Ensure ImageViews preserve aspect ratio; CENTER_CROP fills the screen without
# deforming the image. The background itself is now exact 16:9, so crop is tiny.
for rel in [
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
]:
    p = root / rel
    s = p.read_text(encoding="utf-8")
    s = s.replace("ImageView.ScaleType.FIT_XY", "ImageView.ScaleType.CENTER_CROP")
    s = s.replace("ImageView.ScaleType.FIT_CENTER", "ImageView.ScaleType.CENTER_CROP")
    s = s.replace("background.setAdjustViewBounds(true);", "background.setAdjustViewBounds(false);")
    p.write_text(s, encoding="utf-8")

print("0.16 patch applied: per-component crash diagnostics + 2560x1440 crisp background")
