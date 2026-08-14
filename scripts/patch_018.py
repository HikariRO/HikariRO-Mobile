from pathlib import Path
import re, base64

root = Path('winlator/app')

# ---------------------------------------------------------------------------
# HikariRO Mobile 0.18
# - bypasses the exact box64rc copy step where 0.17 dies on Android 16
# - uses the approved launcher artwork supplied by the user
# - makes the visible JUGAR / DIAGNOSTICO / ARCHIVOS / AJUSTES / ACERCA DE
#   areas real Android controls without drawing duplicate UI on top
# - keeps the same artwork above XServer until the first real Wine window maps
# ---------------------------------------------------------------------------

build = root / 'app/build.gradle'
s = build.read_text(encoding='utf-8')
s = re.sub(r'versionCode\s+[^\n]+', 'versionCode Integer.parseInt("1800")', s, count=1)
s = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.18.0-beta")', s, count=1)
build.write_text(s, encoding='utf-8')

for rel in [
    'app/src/main/java/com/winlator/HikariDiagnostics.java',
    'app/src/main/java/com/winlator/HikariStartupDialog.java',
    'app/src/main/java/com/winlator/HikariLauncherActivity.java',
]:
    p = root / rel
    p.write_text(p.read_text(encoding='utf-8').replace('0.17', '0.18'), encoding='utf-8')

# Decode the approved launcher artwork from UTF-8 base64 chunks committed in
# assets/launcher018_parts. WebP keeps the APK small while remaining sharp.
parts = sorted(Path('assets/launcher018_parts').glob('*.txt'))
if not parts:
    raise RuntimeError('No launcher018_parts found')
raw = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
art = base64.b64decode(raw)
dest = root / 'app/src/main/res/drawable-nodpi/hikariro_launcher_018.webp'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(art)
print('0.18 launcher artwork bytes=', len(art))

# ---------------------------------------------------------------------------
# GuestProgramLauncherComponent: 0.17 trace ends inside copyDefaultBox64RCFile.
# Bypass that AssetManager copy. The RC file is optional because all required
# Box64 options are already supplied through EnvVars.
# ---------------------------------------------------------------------------
guest = root / 'app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java'
t = guest.read_text(encoding='utf-8')
old = '''                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC BEGIN");
                copyDefaultBox64RCFile();
                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC END");'''
new = '''                File hikariRcFile = new File(environment.getRootFS().getRootDir(), "/etc/config.box64rc");
                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC BYPASSED existing=" + hikariRcFile.isFile() + " size=" + (hikariRcFile.isFile() ? hikariRcFile.length() : 0));'''
if old not in t:
    raise RuntimeError('0.17 copyBox64RC instrumentation not found')
t = t.replace(old, new, 1)

old_rc = '''        File box64RCFile = new File(rootFS.getRootDir(), "/etc/config.box64rc");
        envVars.put("BOX64_RCFILE", box64RCFile.getPath());'''
new_rc = '''        File box64RCFile = new File(rootFS.getRootDir(), "/etc/config.box64rc");
        if (box64RCFile.isFile()) {
            envVars.put("BOX64_RCFILE", box64RCFile.getPath());
            HikariDiagnostics.record(context, "BOX64_RCFILE activo: " + box64RCFile.getPath() + " size=" + box64RCFile.length());
        }
        else {
            HikariDiagnostics.record(context, "BOX64_RCFILE omitido: config.box64rc no existe");
        }'''
if old_rc not in t:
    raise RuntimeError('BOX64_RCFILE block not found')
t = t.replace(old_rc, new_rc, 1)
guest.write_text(t, encoding='utf-8')

# ---------------------------------------------------------------------------
# Launcher UI. The approved image itself contains all visible UI. Transparent
# hitboxes are positioned using the source-image coordinate system (1672x941),
# so the visual result is exactly the supplied design.
# ---------------------------------------------------------------------------
launcher = root / 'app/src/main/java/com/winlator/HikariLauncherActivity.java'
t = launcher.read_text(encoding='utf-8')
if 'import android.app.AlertDialog;' not in t:
    t = t.replace('import android.content.Intent;\n', 'import android.content.Intent;\nimport android.app.AlertDialog;\nimport android.widget.Toast;\n', 1)

pattern = re.compile(r'    private void buildUi\(\) \{.*?\n    \}\n\n    private void refresh\(\)', re.S)
m = pattern.search(t)
if not m:
    raise RuntimeError('HikariLauncherActivity.buildUi() not found')

replacement = r'''    private void buildUi() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE);

        final FrameLayout frame = new FrameLayout(this);
        frame.setBackgroundColor(Color.rgb(2, 12, 35));

        // Blurred/cropped-looking fill is intentionally just the same sharp image
        // at low alpha behind the centered 16:9 artwork. It only fills extra-wide
        // side areas; the actual launcher remains unscaled and undistorted.
        ImageView fill = new ImageView(this);
        fill.setImageResource(R.drawable.hikariro_launcher_018);
        fill.setScaleType(ImageView.ScaleType.CENTER_CROP);
        fill.setAlpha(0.35f);
        frame.addView(fill, new FrameLayout.LayoutParams(-1, -1));

        ImageView background = new ImageView(this);
        background.setImageResource(R.drawable.hikariro_launcher_018);
        background.setScaleType(ImageView.ScaleType.FIT_CENTER);
        background.setAdjustViewBounds(false);
        frame.addView(background, new FrameLayout.LayoutParams(-1, -1));

        // Hidden compatibility widgets used by the existing install/update code.
        status = new TextView(this);
        status.setVisibility(View.GONE);
        frame.addView(status, new FrameLayout.LayoutParams(1, 1));
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setVisibility(View.GONE);
        frame.addView(progress, new FrameLayout.LayoutParams(1, 1));

        action = createLauncherHitbox(frame, "Jugar");
        diagnosticAction = createLauncherHitbox(frame, "Diagnóstico");
        Button filesButton = createLauncherHitbox(frame, "Archivos");
        Button settingsButton = createLauncherHitbox(frame, "Ajustes");
        Button aboutButton = createLauncherHitbox(frame, "Acerca de");

        diagnosticAction.setOnClickListener(v -> copyLastDiagnostic());
        filesButton.setOnClickListener(v -> showClientFiles());
        settingsButton.setOnClickListener(v -> showHikariSettings());
        aboutButton.setOnClickListener(v -> showAboutHikari());

        setContentView(frame);
        frame.post(() -> {
            placeOverArtwork(frame, action,            623, 682, 427, 111);
            placeOverArtwork(frame, diagnosticAction, 389, 829, 203,  60);
            placeOverArtwork(frame, filesButton,      614, 829, 203,  60);
            placeOverArtwork(frame, settingsButton,   838, 829, 203,  60);
            placeOverArtwork(frame, aboutButton,     1062, 829, 204,  60);
        });
    }

    private Button createLauncherHitbox(FrameLayout frame, String description) {
        Button b = new Button(this);
        b.setText("");
        b.setContentDescription(description);
        b.setBackgroundColor(Color.TRANSPARENT);
        b.setAlpha(0.02f);
        b.setPadding(0, 0, 0, 0);
        frame.addView(b, new FrameLayout.LayoutParams(1, 1));
        return b;
    }

    private void placeOverArtwork(FrameLayout frame, View view, int x, int y, int w, int h) {
        float scale = Math.min(frame.getWidth() / 1672.0f, frame.getHeight() / 941.0f);
        float imageW = 1672.0f * scale;
        float imageH = 941.0f * scale;
        float left = (frame.getWidth() - imageW) / 2.0f;
        float top = (frame.getHeight() - imageH) / 2.0f;
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
            Math.max(1, Math.round(w * scale)), Math.max(1, Math.round(h * scale)));
        lp.leftMargin = Math.round(left + x * scale);
        lp.topMargin = Math.round(top + y * scale);
        view.setLayoutParams(lp);
    }

    private void showClientFiles() {
        new AlertDialog.Builder(this)
            .setTitle("Archivos de HikariRO")
            .setMessage("Cliente instalado en:\n" + storageDir().getAbsolutePath() + "/HikariRO\n\nAndroid protege esta carpeta privada. El gestor interno de archivos se añadirá más adelante.")
            .setPositiveButton("Aceptar", null)
            .show();
    }

    private void showHikariSettings() {
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(this);
        boolean enabled = prefs.getBoolean("hikari_compat_mode", true);
        String[] values = {"Modo compatible Mali (recomendado)", "Modo rendimiento"};
        new AlertDialog.Builder(this)
            .setTitle("Ajustes gráficos")
            .setSingleChoiceItems(values, enabled ? 0 : 1, (dialog, which) -> {
                prefs.edit().putBoolean("hikari_compat_mode", which == 0).apply();
                dialog.dismiss();
                Toast.makeText(this, which == 0 ? "Modo compatible activado" : "Modo rendimiento activado", Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("Cancelar", null)
            .show();
    }

    private void showAboutHikari() {
        new AlertDialog.Builder(this)
            .setTitle("HikariRO Mobile 0.18")
            .setMessage("HikariRO Mobile\nAndroid 16 / ARM64\nBox64 + Wine\n\nhttps://hikariro.com")
            .setPositiveButton("Aceptar", null)
            .show();
    }

    private void refresh()'''

t = t[:m.start()] + replacement + t[m.end():]
# Keep the visible diagnostic button functional even before the first crash log.
t = re.sub(r'diagnosticAction\.setVisibility\([^;]+\);', 'diagnosticAction.setVisibility(View.VISIBLE);', t)
launcher.write_text(t, encoding='utf-8')

# ---------------------------------------------------------------------------
# XServer waiting screen. XServerView is opaque, so put the same artwork above
# it until the first actual renderable Wine/X11 window appears.
# ---------------------------------------------------------------------------
xserver = root / 'app/src/main/java/com/winlator/XServerDisplayActivity.java'
t = xserver.read_text(encoding='utf-8')
if 'import android.widget.ImageView;' not in t:
    t = t.replace('import android.widget.FrameLayout;\n', 'import android.widget.FrameLayout;\nimport android.widget.ImageView;\n', 1)

field_needle = '    private XServerView xServerView;'
if field_needle not in t:
    raise RuntimeError('xServerView field not found')
t = t.replace(field_needle, field_needle + '\n    private ImageView hikariWaitingBackground;', 1)

ui_needle = '''        xServer.setRenderer(renderer);
        rootView.addView(xServerView);

        globalCursorSpeed = preferences.getFloat("cursor_speed", 1.0f);'''
ui_repl = '''        xServer.setRenderer(renderer);
        rootView.addView(xServerView);

        hikariWaitingBackground = new ImageView(this);
        hikariWaitingBackground.setImageResource(R.drawable.hikariro_launcher_018);
        hikariWaitingBackground.setScaleType(ImageView.ScaleType.CENTER_CROP);
        hikariWaitingBackground.setAdjustViewBounds(false);
        rootView.addView(hikariWaitingBackground, new FrameLayout.LayoutParams(-1, -1));
        HikariDiagnostics.record(this, "0.18 fondo X11 overlay instalado");

        globalCursorSpeed = preferences.getFloat("cursor_speed", 1.0f);'''
if ui_needle not in t:
    raise RuntimeError('setupUI XServerView insertion point not found')
t = t.replace(ui_needle, ui_repl, 1)

map_needle = '''                if (!flags[0] && window.isRenderable() && !window.getClassName().isEmpty()) {
                    xServerView.getRenderer().setCursorVisible(true);
                    preloaderDialog.closeOnUiThread();
                    flags[0] = true;
                }'''
map_repl = '''                if (!flags[0] && window.isRenderable() && !window.getClassName().isEmpty()) {
                    HikariDiagnostics.record(XServerDisplayActivity.this, "Primera ventana X11 renderizable: class=" + window.getClassName() + " id=" + window.id);
                    runOnUiThread(() -> {
                        if (hikariWaitingBackground != null) {
                            android.view.ViewParent parent = hikariWaitingBackground.getParent();
                            if (parent instanceof android.view.ViewGroup) ((android.view.ViewGroup)parent).removeView(hikariWaitingBackground);
                            hikariWaitingBackground = null;
                        }
                    });
                    xServerView.getRenderer().setCursorVisible(true);
                    preloaderDialog.closeOnUiThread();
                    flags[0] = true;
                }'''
if map_needle not in t:
    raise RuntimeError('onMapWindow first-window block not found')
t = t.replace(map_needle, map_repl, 1)

# If Wine finally starts but exits immediately, keep the display alive for five
# seconds and persist the exit status instead of instantly bouncing to JUGAR.
cb_old = 'guestProgramLauncherComponent.setTerminationCallback((status) -> exit());'
cb_new = '''guestProgramLauncherComponent.setTerminationCallback((status) -> {
            HikariDiagnostics.record(this, "0.18 Guest termination status=" + status);
            new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(this::exit, 5000L);
        });'''
if cb_old in t:
    t = t.replace(cb_old, cb_new, 1)

xserver.write_text(t, encoding='utf-8')

print('0.18 patch applied: approved launcher + box64rc bypass + X11 waiting artwork')
