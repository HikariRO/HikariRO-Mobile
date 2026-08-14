from pathlib import Path
import re
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
root = Path('winlator/app')

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
    p.write_text(p.read_text(encoding='utf-8').replace('0.16', '0.17'), encoding='utf-8')

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
                    HikariDiagnostics.record(hikariContext, "GPL WATCHDOG 1.2s state=" + hikariThread.getState());
                    for (StackTraceElement e : hikariThread.getStackTrace()) HikariDiagnostics.record(hikariContext, "  GPL at " + e.toString());
                }
                Thread.sleep(2800);
                if (hikariStartInProgress) {
                    HikariDiagnostics.record(hikariContext, "GPL WATCHDOG 4.0s state=" + hikariThread.getState());
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
            if (ex instanceof RuntimeException) throw (RuntimeException)ex;
            if (ex instanceof Error) throw (Error)ex;
            throw new RuntimeException(ex);
        } finally {
            hikariStartInProgress = false;
            HikariDiagnostics.record(hikariContext, "GPL START finally");
        }
    }'''
if old not in t:
    raise RuntimeError('GuestProgramLauncherComponent.start() esperado no encontrado')
t = t.replace(old, new, 1)
guest.write_text(t, encoding='utf-8')

xserver = root / 'app/src/main/java/com/winlator/XServerDisplayActivity.java'
t = xserver.read_text(encoding='utf-8')
needle = '        super.onCreate(savedInstanceState);'
if needle in t and 'HIKARI defaultUncaughtExceptionHandler installed' not in t:
    t = t.replace(needle, needle + '''
        final Thread.UncaughtExceptionHandler hikariPreviousHandler = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, throwable) -> {
            try {
                HikariDiagnostics.record(this, "UNCAUGHT thread=" + thread.getName() + " " + throwable.getClass().getName() + ": " + String.valueOf(throwable.getMessage()));
                for (StackTraceElement e : throwable.getStackTrace()) HikariDiagnostics.record(this, "  UNCAUGHT at " + e.toString());
            } catch (Throwable ignored) {}
            if (hikariPreviousHandler != null) hikariPreviousHandler.uncaughtException(thread, throwable);
        });
        HikariDiagnostics.record(this, "HIKARI defaultUncaughtExceptionHandler installed");''', 1)

# Patch existing lifecycle methods instead of adding duplicates.
t = t.replace('''    @Override
    public void onResume() {
        super.onResume();''', '''    @Override
    public void onResume() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onResume finishing=" + isFinishing());
        super.onResume();''', 1)
t = t.replace('''    @Override
    public void onPause() {
        super.onPause();''', '''    @Override
    public void onPause() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onPause finishing=" + isFinishing() + " changingConfig=" + isChangingConfigurations());
        super.onPause();''', 1)
t = t.replace('''    @Override
    protected void onDestroy() {
        winHandler.stop();''', '''    @Override
    protected void onDestroy() {
        HikariDiagnostics.record(this, "HIKARI lifecycle onDestroy finishing=" + isFinishing() + " changingConfig=" + isChangingConfigurations());
        HikariDiagnostics.processes(this);
        winHandler.stop();''', 1)
xserver.write_text(t, encoding='utf-8')

# Single full-screen background, no top/bottom bands and no Android distortion.
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
# Preserve ratio and fill the whole display by crop rather than stretch.
sharp = ImageOps.fit(scenic, (2560, 1440), method=Image.Resampling.LANCZOS, centering=(0.5, 0.48))
sharp = sharp.filter(ImageFilter.UnsharpMask(radius=0.7, percent=115, threshold=2))
soft = sharp.filter(ImageFilter.GaussianBlur(2.2))
out = Image.blend(soft, sharp, 0.82)
out = ImageEnhance.Color(out).enhance(1.06)
out = ImageEnhance.Contrast(out).enhance(1.03)
dest.parent.mkdir(parents=True, exist_ok=True)
out.save(dest, 'PNG', optimize=True)

for rel in ['app/src/main/java/com/winlator/HikariLauncherActivity.java','app/src/main/java/com/winlator/HikariStartupDialog.java']:
    p = root / rel
    z = p.read_text(encoding='utf-8')
    z = z.replace('ImageView.ScaleType.FIT_XY', 'ImageView.ScaleType.CENTER_CROP')
    z = z.replace('ImageView.ScaleType.FIT_CENTER', 'ImageView.ScaleType.CENTER_CROP')
    z = z.replace('background.setAdjustViewBounds(true);', 'background.setAdjustViewBounds(false);')
    p.write_text(z, encoding='utf-8')

print('0.17 patch applied: deep GPL diagnostics + lifecycle logging + single fullscreen background')
