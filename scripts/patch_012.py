from pathlib import Path
import re

root = Path("winlator/app")

# Version
build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("12")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.12.0-beta")', text, count=1)
build.write_text(text, encoding="utf-8")

# Diagnostic/version markers
diagnostics = root / "app/src/main/java/com/winlator/HikariDiagnostics.java"
text = diagnostics.read_text(encoding="utf-8")
for oldv in ("0.7", "0.8", "0.9", "0.10", "0.11"):
    text = text.replace("Inicio del diagnóstico " + oldv, "Inicio del diagnóstico 0.12")
diagnostics.write_text(text, encoding="utf-8")

startup = root / "app/src/main/java/com/winlator/HikariStartupDialog.java"
text = startup.read_text(encoding="utf-8")
for oldv in ("0.7", "0.8", "0.9", "0.10", "0.11"):
    text = text.replace("HikariRO Mobile " + oldv + "\\n", "HikariRO Mobile 0.12\\n")
# Show the entire artwork instead of cropping it.
text = text.replace("background.setScaleType(ImageView.ScaleType.CENTER_CROP);", "background.setScaleType(ImageView.ScaleType.FIT_CENTER);", 1)
startup.write_text(text, encoding="utf-8")

# Persist the exact Box64/Wine termination status before XServer returns to launcher.
guest = root / "app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
text = guest.read_text(encoding="utf-8")
needle = '''        return ProcessHelper.exec(command, envVars, rootDir, (status) -> {
            synchronized (lock) {
                pid = -1;
            }
            if (terminationCallback != null) terminationCallback.call(status);
        });'''
replacement = '''        HikariDiagnostics.record(environment.getContext(), "Comando Box64/Wine preparado: " + command);
        return ProcessHelper.exec(command, envVars, rootDir, (status) -> {
            HikariDiagnostics.record(environment.getContext(), "Box64/Wine terminó. exitCode=" + status + " guestExecutable=" + guestExecutable);
            HikariDiagnostics.processes(environment.getContext());
            synchronized (lock) {
                pid = -1;
            }
            if (terminationCallback != null) terminationCallback.call(status);
        });'''
if needle not in text:
    raise RuntimeError("No se encontró callback de terminación de GuestProgramLauncherComponent")
text = text.replace(needle, replacement, 1)
# Add import if customization did not already add it.
if "import com.winlator.HikariDiagnostics;" not in text:
    text = text.replace("package com.winlator.xenvironment.components;\n", "package com.winlator.xenvironment.components;\n\nimport com.winlator.HikariDiagnostics;\n", 1)
guest.write_text(text, encoding="utf-8")

# Main launcher: full background + persistent 'copy last diagnostic' button.
launcher = root / "app/src/main/java/com/winlator/HikariLauncherActivity.java"
text = launcher.read_text(encoding="utf-8")
text = text.replace("background.setScaleType(ImageView.ScaleType.CENTER_CROP);", "background.setScaleType(ImageView.ScaleType.FIT_CENTER);", 1)
# Do not darken/cover unused letterbox area aggressively.
text = text.replace("shade.setBackgroundColor(0x55030b1d);", "shade.setBackgroundColor(0x22030b1d);", 1)

if "import android.content.ClipboardManager;" not in text:
    text = text.replace("import android.content.Intent;", "import android.content.Intent;\nimport android.content.ClipboardManager;\nimport android.content.ClipData;", 1)
if "import java.io.BufferedReader;" not in text:
    text = text.replace("import java.io.BufferedInputStream;", "import java.io.BufferedInputStream;\nimport java.io.BufferedReader;\nimport java.io.FileReader;", 1)

text = text.replace("    private Button action;", "    private Button action;\n    private Button diagnosticAction;", 1)

ui_needle = '''        root.addView(action, buttonParams);
        frame.addView(root, new FrameLayout.LayoutParams(-1, -1));'''
ui_replacement = '''        root.addView(action, buttonParams);

        diagnosticAction = new Button(this);
        diagnosticAction.setText("Copiar último diagnóstico");
        LinearLayout.LayoutParams diagnosticParams = new LinearLayout.LayoutParams(-2, -2);
        diagnosticParams.setMargins(0, dp(10), 0, 0);
        diagnosticAction.setOnClickListener(v -> copyLastDiagnostic());
        root.addView(diagnosticAction, diagnosticParams);
        updateDiagnosticButton();

        frame.addView(root, new FrameLayout.LayoutParams(-1, -1));'''
if ui_needle not in text:
    raise RuntimeError("No se encontró inserción de botón del launcher")
text = text.replace(ui_needle, ui_replacement, 1)

# Refresh button whenever launcher becomes visible again after XServer closes.
oncreate_needle = '''    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        AppUtils.keepScreenOn(this);
        buildUi();
        refresh();
    }'''
oncreate_replacement = oncreate_needle + '''

    @Override protected void onResume() {
        super.onResume();
        if (diagnosticAction != null) updateDiagnosticButton();
    }'''
if oncreate_needle not in text:
    raise RuntimeError("No se encontró onCreate del launcher")
text = text.replace(oncreate_needle, oncreate_replacement, 1)

# Insert helper methods before ClientInfo.
helper_needle = "    private static class ClientInfo {"
helpers = '''    private void updateDiagnosticButton() {
        File trace = HikariDiagnostics.file(this);
        File wine = new File(getFilesDir(), "hikari-startup.log");
        diagnosticAction.setVisibility((trace.isFile() || wine.isFile()) ? View.VISIBLE : View.GONE);
    }

    private String readLog(File file, int maximum) {
        if (!file.isFile()) return "Registro no creado.";
        java.util.ArrayList<String> lines = new java.util.ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                lines.add(line);
                if (lines.size() > maximum) lines.remove(0);
            }
        } catch (Exception e) { return "No se pudo leer: " + e.getMessage(); }
        StringBuilder out = new StringBuilder();
        for (String line : lines) out.append(line).append('\\n');
        return out.length() == 0 ? "Registro vacío." : out.toString();
    }

    private void copyLastDiagnostic() {
        String value = "HikariRO Mobile 0.12\\n" +
            "Executable: " + executable().getAbsolutePath() + "\\n" +
            "Device: " + Build.MANUFACTURER + " " + Build.MODEL + "\\n" +
            "Android: " + Build.VERSION.RELEASE + " (SDK " + Build.VERSION.SDK_INT + ")\\n" +
            "--- Traza interna ---\\n" + readLog(HikariDiagnostics.file(this), 220) +
            "--- Box64 / Wine ---\\n" + readLog(new File(getFilesDir(), "hikari-startup.log"), 220);
        ClipboardManager clipboard = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("HikariRO diagnosis", value));
        status.setText("Último diagnóstico copiado al portapapeles.\\nPégalo en el chat para revisar el cierre del juego.");
    }

'''
if helper_needle not in text:
    raise RuntimeError("No se encontró ClientInfo del launcher")
text = text.replace(helper_needle, helpers + helper_needle, 1)
launcher.write_text(text, encoding="utf-8")

# Stage text
xserver = root / "app/src/main/java/com/winlator/XServerDisplayActivity.java"
text = xserver.read_text(encoding="utf-8")
text = text.replace("Box64 en ejecución; iniciando Wine y esperando la ventana del juego", "Wine iniciado; esperando raghikari.exe y registrando cualquier cierre")
xserver.write_text(text, encoding="utf-8")
