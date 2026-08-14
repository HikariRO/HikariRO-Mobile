from pathlib import Path
import re

from PIL import Image, ImageFilter, ImageFile, ImageOps, ImageEnhance, ImageDraw

ImageFile.LOAD_TRUNCATED_IMAGES = True

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

# Build a sharp 16:9 composition from the useful scenic part of the source.
# The original PNG contains a wide panorama only at the top and a large black
# lower area. Instead of stretching that panorama vertically, keep it crisp,
# mirror it at the bottom and bridge both with a dark-blue gradient. This fills
# the screen intentionally without deformation and keeps the central UI legible.
source = Path("assets/hikariro-launcher-background.png")
dest = root / "app/src/main/res/drawable-nodpi/hikariro_launcher_background.png"
if not source.is_file():
    raise RuntimeError("Falta assets/hikariro-launcher-background.png")
img = Image.open(source).convert("RGB")
w, h = img.size

# The previous build detected the actual scenic content in the first ~180 rows.
# Re-detect conservatively to survive future source changes.
last = 0
sample_width = min(420, w)
for y in range(h):
    row = img.crop((0, y, w, y + 1)).resize((sample_width, 1))
    pixels = list(row.getdata())
    bright = sum(1 for r, g, b in pixels if max(r, g, b) > 35 and (r + g + b) > 90)
    if bright >= max(4, len(pixels) // 24):
        last = y
scenic_h = min(h, max(180, last + 1))
scenic = img.crop((0, 0, w, scenic_h))

# Uniform horizontal scaling only; aspect ratio is preserved.
target_w, target_h = 2560, 1440
scale = target_w / scenic.width
strip_h = max(260, round(scenic.height * scale))
scenic = scenic.resize((target_w, strip_h), Image.Resampling.LANCZOS)
scenic = scenic.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=2))

canvas = Image.new("RGB", (target_w, target_h), (5, 13, 31))
canvas.paste(scenic, (0, 0))

bottom = ImageOps.flip(scenic)
bottom = ImageEnhance.Brightness(bottom).enhance(0.58)
canvas.paste(bottom, (0, target_h - strip_h))

# Dark navy gradient through the center, sampled to blend with both strips.
draw = ImageDraw.Draw(canvas)
start_y = strip_h
end_y = target_h - strip_h
for y in range(start_y, end_y):
    t = (y - start_y) / max(1, end_y - start_y - 1)
    # Slightly brighter near the panorama edges, darkest in the middle.
    edge = abs(t - 0.5) * 2.0
    r = int(5 + 7 * edge)
    g = int(13 + 13 * edge)
    b = int(31 + 24 * edge)
    draw.line((0, y, target_w, y), fill=(r, g, b))

# Very subtle vignette on the edges for better text contrast without blurring art.
overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
for i in range(90):
    alpha = int(70 * (1 - i / 90))
    od.rectangle((i, i, target_w - 1 - i, target_h - 1 - i), outline=(0, 0, 0, alpha))
canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

dest.parent.mkdir(parents=True, exist_ok=True)
canvas.save(dest, "PNG", optimize=True)

# Preserve aspect ratio in Android. Exact 16:9 background + CENTER_CROP means no stretch.
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

print("0.16 patch applied: per-component crash diagnostics + crisp non-stretched 2560x1440 background")
