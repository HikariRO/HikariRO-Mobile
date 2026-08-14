from pathlib import Path
import re

root = Path('winlator/app')

# Version metadata.
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
    t = p.read_text(encoding='utf-8').replace('0.17', '0.18')
    p.write_text(t, encoding='utf-8')

# The 0.17 trace proved the process disappears while executing
# copyDefaultBox64RCFile(), before execGuestProgram() is ever reached.
# Box64 does not require a config.box64rc file to launch, so bypass the asset
# copy completely. Existing config files are left untouched.
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

# Only advertise BOX64_RCFILE when the file actually exists. Box64 will use its
# internal/default settings otherwise.
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

# The PNG is correctly decoded in 0.17, but XServerView is an opaque rendering
# surface and paints over the activity background with its own blue clear color.
# Put the Hikari artwork ABOVE XServerView while waiting for the first actual
# Wine/game window, then remove it as soon as a renderable X11 window maps.
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
        hikariWaitingBackground.setImageResource(R.drawable.hikariro_launcher_background);
        hikariWaitingBackground.setScaleType(ImageView.ScaleType.CENTER_CROP);
        hikariWaitingBackground.setAdjustViewBounds(false);
        hikariWaitingBackground.setBackgroundColor(android.graphics.Color.TRANSPARENT);
        rootView.addView(hikariWaitingBackground, new FrameLayout.LayoutParams(-1, -1));
        HikariDiagnostics.record(this, "Fondo X11 overlay instalado sobre XServerView");

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

xserver.write_text(t, encoding='utf-8')

print('0.18 patch applied: bypass box64rc asset copy + artwork overlay above XServerView')
