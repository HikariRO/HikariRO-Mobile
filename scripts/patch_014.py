from pathlib import Path
import re
from PIL import Image

root = Path('winlator/app')
build = root / 'app/build.gradle'
text = build.read_text(encoding='utf-8')
text = re.sub(r'versionCode\s+[^\n]+', 'versionCode Integer.parseInt("14")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.14.0-beta")', text, count=1)
build.write_text(text, encoding='utf-8')

for rel in [
    'app/src/main/java/com/winlator/HikariDiagnostics.java',
    'app/src/main/java/com/winlator/HikariStartupDialog.java',
    'app/src/main/java/com/winlator/HikariLauncherActivity.java',
]:
    p = root / rel
    p.write_text(p.read_text(encoding='utf-8').replace('0.13', '0.14'), encoding='utf-8')

guest = root / 'app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java'
text = guest.read_text(encoding='utf-8')
old = '''            launchExecutable = "wine cmd /c \\\"E: && cd \\\\HikariRO && raghikari.exe\\\"";'''
new = '''            File wine64 = new File(rootDir, rootFS.getWinePath()+"/bin/wine64");
            File wine64Preloader = new File(rootDir, rootFS.getWinePath()+"/bin/wine64-preloader");
            File winePreloader = new File(rootDir, rootFS.getWinePath()+"/bin/wine-preloader");
            HikariDiagnostics.record(environment.getContext(), "wine64=" + wine64.getAbsolutePath() + " exists=" + wine64.isFile() + " size=" + (wine64.isFile() ? wine64.length() : 0));
            HikariDiagnostics.record(environment.getContext(), "wine64-preloader=" + wine64Preloader.getAbsolutePath() + " exists=" + wine64Preloader.isFile());
            HikariDiagnostics.record(environment.getContext(), "wine-preloader=" + winePreloader.getAbsolutePath() + " exists=" + winePreloader.isFile());
            File selectedWineLoader = wine64.isFile() ? wine64 : wineBinary;
            launchExecutable = selectedWineLoader.getAbsolutePath() + " cmd /c \\\"E: && cd \\\\HikariRO && raghikari.exe\\\"";
            HikariDiagnostics.record(environment.getContext(), "Wine loader seleccionado=" + selectedWineLoader.getAbsolutePath());'''
if old not in text:
    raise RuntimeError('No se encontro launchExecutable de 0.13')
text = text.replace(old, new, 1)
guest.write_text(text, encoding='utf-8')

img_path = root / 'app/src/main/res/drawable-nodpi/hikariro_launcher_background.png'
img = Image.open(img_path).convert('RGB')
w, h = img.size
last = 0
sample_width = min(320, w)
for y in range(h):
    row = img.crop((0, y, w, y + 1)).resize((sample_width, 1))
    pixels = list(row.getdata())
    bright = sum(1 for r,g,b in pixels if max(r,g,b) > 35 and (r+g+b) > 90)
    if bright >= max(3, len(pixels) // 20):
        last = y
crop_bottom = min(h, max(180, last + 1))
scenic = img.crop((0, 0, w, crop_bottom)).resize((1920, 1080), Image.Resampling.LANCZOS)
scenic.save(img_path, 'PNG', optimize=True)
print('0.14 background:', (w,h), 'crop_bottom=', crop_bottom, '->', scenic.size)

for rel in [
    'app/src/main/java/com/winlator/HikariLauncherActivity.java',
    'app/src/main/java/com/winlator/HikariStartupDialog.java',
]:
    p = root / rel
    s = p.read_text(encoding='utf-8')
    s = s.replace('ImageView.ScaleType.FIT_CENTER', 'ImageView.ScaleType.CENTER_CROP')
    s = s.replace('shade.setBackgroundColor(0x22030b1d);', 'shade.setBackgroundColor(0x22000000);')
    p.write_text(s, encoding='utf-8')
