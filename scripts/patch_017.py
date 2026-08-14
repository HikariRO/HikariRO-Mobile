from pathlib import Path
import re
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
root = Path('winlator/app')

# Version
build = root / 'app/build.gradle'
s = build.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+[^\n]+', 'versionCode Integer.parseInt("1700")', s, count=1)
s = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.17.0-beta")', s, count=1)
build.write_text(s, encoding='utf-8')

for rel in [
    'app/src/main/java/com/winlator/HikariDiagnostics.java',
    'app/src/main/java/com/winlator/HikariStartupDialog.java',
    'app/src/main/java/com/winlator/HikariLauncherActivity.java',
]:
    p = root / rel
    t = p.read_text(encoding='utf-8').replace('0.16', '0.17')
    p.write_text(t, encoding='utf-8')

# Deep instrumentation inside GuestProgramLauncherComponent.start().
guest = root / 'app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java'
t = guest.read_text(encoding='utf-8')
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
new = '''    private volatile boolean hikariStartInProgress = false;

    @Override
    public void start() {
        final Context hikariContext = environment.getContext();
        final Thread hikariThread = Thread.currentThread();
        HikariDiagnostics.record(hikariContext, "GPL START enter thread=" + hikariThread.getName() + " id=" + hikariThread.getId());
        hikariStartInProgress = true;
        Thread watchdog = new Thread(() -> {
            try {
                Thread.sleep(1200);
                if (hikariStartInProgress) {
                    HikariDiagnostics.record(hikariContext, "GPL WATCHDOG 1.2s: start() sigue activo state=" + hikariThread.getState());
                    for (StackTraceElement e : hikariThread.getStackTrace()) HikariDiagnostics.record(hikariContext, "  GPL at " + e.toString());
                }
                Thread.sleep(2800);
                if (hikariStartInProgress) {
                    HikariDiagnostics.record(hikariContext, "GPL WATCHDOG 4.0s: start() sigue activo state=" + hikariThread.getState());
                    for (StackTraceElement e : hikariThread.getStackTrace()) HikariDiagnostics.record(hikariContext, "  GPL at " + e.toString());
                    HikariDiagnostics.processes(hikariContext);
                }
            } catch (Throwable ignored) {}
        }, "Hikari-GPL-Watchdog");
        watchdog.setDaemon(true);
        watchdog.start();
        try {
            HikariDiagnostics.record(hikariContext, "GPL antes de synchronized(lock)");
            synchronized (lock) {
                HikariDiagnostics.record(hikariContext, "GPL lock adquirido");
                HikariDiagnostics.record(hikariContext, "GPL STEP stop BEGIN");
                stop();
                HikariDiagnostics.record(hikariContext, "GPL STEP stop END");
                HikariDiagnostics.record(hikariContext, "GPL STEP extractBox64 BEGIN");
                extractBox64File();
                HikariDiagnostics.record(hikariContext, "GPL STEP extractBox64 END");
                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC BEGIN");
                copyDefaultBox64RCFile();
                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC END");
                HikariDiagnostics.record(hikariContext, "GPL STEP execGuestProgram BEGIN guest=" + guestExecutable);
                pid = execGuestProgram();
                HikariDiagnostics.record(hikariContext, "GPL STEP execGuestProgram END pid=" + pid);
            }
            HikariDiagnostics.record(hikariContext, "GPL START normal END");
        } catch (Throwable ex) {
            HikariDiagnostics.record(hikariContext, "GPL THROWABLE " + ex.getClass().getName() + ": " + String.valueOf(ex.getMessage()));
            for (StackTraceElement e : ex.getStackTrace()) HikariDiagnostics.record(hikariContext, "  GPL exception at " + e.toString());
            throw ex;
        } finally {
            hikariStartInProgress = false;
            HikariDiagnostics.record(hikariContext, "GPL START finally");
        }
    }'''
if old not in t:
    raise RuntimeError('GuestProgramLauncherComponent.start() esperado no encontrado')
t = t.replace(old, new, 1)
guest.write_text(t, encoding='utf-8')

# Lifecycle + uncaught exception logging for the XServer activity.
xserver = root / 'app/src/main/java/com/winlator/XServerDisplayActivity.java'
t = xserver.read_text(encoding='utf-8')
needle = '        super.onCreate(savedInstanceState);'
if needle in t and 'HIKARI defaultUncaughtExceptionHandler installed' not in t:
    repl = needle + '''
        final Thread.UncaughtExceptionHandler hikariPreviousHandler = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, throwable) -> {
            try {
                HikariDiagnostics.record(this, "UNCAUGHT thread=" + thread.getName() + " " + throwable.getClass().getName() + ": " + String.valueOf(throwable.getMessage()));
                for (StackTraceElement e : throwable.getStackTrace()) HikariDiagnostics.record(this, "  UNCAUGHT at " + e.toString());
            } catch (Throwable ignored) {}
            if (hikariPreviousHandler != null) hikariPreviousHandler.uncaughtException(thread, throwable);
        });
        HikariDiagnostics.record(this, "HIKARI defaultUncaughtExceptionHandler installed");'''
    t = t.replace(needle, repl, 1)

# Insert lifecycle markers before final class brace.
if 'HIKARI lifecycle onDestroy' not in t:
    insert = '''
    @Override
    protected void onPause() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onPause finishing=" + isFinishing() + " changingConfig=" + isChangingConfigurations());
        super.onPause();
    }

    @Override
    protected void onStop() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onStop finishing=" + isFinishing() + " changingConfig=" + isChangingConfigurations());
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onDestroy finishing=" + isFinishing() + " changingConfig=" + isChangingConfigurations());
        HikariDiagnostics.processes(this);
        super.onDestroy();
    }
'''
    pos = t.rfind('\n}')
    if pos < 0: raise RuntimeError('No se encontro cierre XServerDisplayActivity')
    t = t[:pos] + insert + t[pos:]
xserver.write_text(t, encoding='utf-8')

# Replace the previous banded background with a single full-screen composition.
# We preserve aspect ratio: build a softly enlarged scenic field, then overlay a
# sharper central crop. This avoids the obvious top/bottom strips from 0.16.
source = Path('assets/hikariro-launcher-background.png')
dest = root / 'app/src/main/res/drawable-nodpi/hikariro_launcher_background.png'
img = Image.open(source).convert('RGB')
w, h = img.size
last = 0
for y in range(h):
    row = img.crop((0, y, w, y + 1)).resize((320, 1))
    px = list(row.getdata())
    if sum(1 for r,g,b in px if max(r,g,b) > 35 and r+g+b > 90) >= 12:
        last = y
scenic = img.crop((0, 0, w, max(180, last + 1)))
# Background layer: preserve ratio, fill 16:9, blur only enough to hide upscale artifacts.
bg = ImageOps.fit(scenic, (2560, 1440), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
bg = bg.filter(ImageFilter.GaussianBlur(5))
bg = ImageEnhance.Contrast(bg).enhance(1.05)
bg = ImageEnhance.Color(bg).enhance(1.08)
# Crisp overlay using the same crop and a gentle sharpening pass.
sharp = ImageOps.fit(scenic, (2560, 1440), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
sharp = sharp.filter(ImageFilter.UnsharpMask(radius=0.8, percent=115, threshold=2))
# Blend 70% sharp image over the softened base for a coherent single scene.
out = Image.blend(bg, sharp, 0.70)
dest.parent.mkdir(parents=True, exist_ok=True)
out.save(dest, 'PNG', optimize=True)

for rel in ['app/src/main/java/com/winlator/HikariLauncherActivity.java','app/src/main/java/com/winlator/HikariStartupDialog.java']:
    p = root / rel
    z = p.read_text(encoding='utf-8')
    z = z.replace('ImageView.ScaleType.FIT_XY', 'ImageView.ScaleType.CENTER_CROP')
    z = z.replace('ImageView.ScaleType.FIT_CENTER', 'ImageView.ScaleType.CENTER_CROP')
    z = z.replace('background.setAdjustViewBounds(true);', 'background.setAdjustViewBounds(false);')
    p.write_text(z, encoding='utf-8')

print('0.17 patch applied: deep GPL diagnostics, activity lifecycle logging, fullscreen background')
