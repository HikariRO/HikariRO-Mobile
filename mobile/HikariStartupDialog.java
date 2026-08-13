package com.winlator;

import android.app.Activity;
import android.app.Dialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.ScrollView;
import android.widget.FrameLayout;

import androidx.preference.PreferenceManager;

import com.winlator.core.PreloaderDialog;

import java.util.Locale;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;

/** HikariRO-branded startup surface with elapsed time, timeout and diagnostics. */
public class HikariStartupDialog extends PreloaderDialog {
    private final Activity activity;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Dialog dialog;
    private TextView title;
    private TextView stage;
    private TextView elapsed;
    private LinearLayout timeoutActions;
    private long startedAt;
    private String currentStage = "Preparando el entorno";

    private final Runnable ticker = new Runnable() {
        @Override public void run() {
            if (dialog == null || !dialog.isShowing()) return;
            long seconds = Math.max(0, (System.currentTimeMillis() - startedAt) / 1000L);
            elapsed.setText(String.format(Locale.getDefault(), "Tiempo transcurrido: %d:%02d", seconds / 60, seconds % 60));
            if (seconds >= 120) {
                title.setText("El inicio está tardando demasiado");
                stage.setText(currentStage + "\nPulsa Copiar diagnóstico para revisar el punto exacto del fallo. El modo compatible solo afecta a problemas gráficos.");
                timeoutActions.setVisibility(View.VISIBLE);
            }
            handler.postDelayed(this, 1000L);
        }
    };

    public HikariStartupDialog(Activity activity) {
        super(activity);
        this.activity = activity;
    }

    @Override public synchronized void show(int textResId) {
        activity.runOnUiThread(() -> {
            if (dialog == null) create();
            title.setText(textResId == R.string.starting_up ? "Iniciando HikariRO" : activity.getString(textResId));
            currentStage = "Preparando Wine y Box64";
            stage.setText(currentStage);
            timeoutActions.setVisibility(View.VISIBLE);
            startedAt = System.currentTimeMillis();
            if (!dialog.isShowing()) dialog.show();
            handler.removeCallbacks(ticker);
            handler.post(ticker);
        });
    }

    public void setStageOnUiThread(String value) {
        currentStage = value;
        activity.runOnUiThread(() -> { if (stage != null) stage.setText(value); });
    }

    @Override public synchronized void close() {
        handler.removeCallbacks(ticker);
        if (dialog != null) dialog.dismiss();
    }

    @Override public void closeOnUiThread() { activity.runOnUiThread(this::close); }

    @Override public boolean isShowing() { return dialog != null && dialog.isShowing(); }

    private void create() {
        dialog = new Dialog(activity, android.R.style.Theme_Black_NoTitleBar_Fullscreen);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        dialog.setCancelable(false);

        FrameLayout frame = new FrameLayout(activity);
        frame.setBackgroundColor(Color.TRANSPARENT);

        ImageView background = new ImageView(activity);
        background.setImageResource(R.drawable.hikariro_launcher_background);
        background.setScaleType(ImageView.ScaleType.CENTER_CROP);
        background.setAdjustViewBounds(false);
        background.setAlpha(1.0f);
        frame.addView(background, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ));

        // Only a light tint: the previous combination of opaque surfaces hid the artwork.
        View shade = new View(activity);
        shade.setBackgroundColor(0x33030b1d);
        frame.addView(shade, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(48), dp(18), dp(48), dp(18));
        root.setBackgroundColor(Color.TRANSPARENT);

        ImageView logo = new ImageView(activity);
        logo.setImageResource(R.drawable.hikariro_mobile_icon);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        root.addView(logo, new LinearLayout.LayoutParams(dp(118), dp(118)));

        title = label(26, 0xffffffff);
        title.setGravity(Gravity.CENTER);
        root.addView(title, margins(-1, -2, 4, 8));

        ProgressBar spinner = new ProgressBar(activity);
        spinner.setIndeterminate(true);
        root.addView(spinner, margins(dp(44), dp(44), 0, 8));

        stage = label(18, 0xffdce8ff);
        stage.setGravity(Gravity.CENTER);
        root.addView(stage, margins(-1, -2, 0, 4));

        elapsed = label(15, 0xff8fa8cf);
        elapsed.setGravity(Gravity.CENTER);
        root.addView(elapsed, margins(-1, -2, 0, 8));

        timeoutActions = new LinearLayout(activity);
        timeoutActions.setOrientation(LinearLayout.HORIZONTAL);
        timeoutActions.setGravity(Gravity.CENTER);
        timeoutActions.setVisibility(View.VISIBLE);

        Button retry = new Button(activity);
        retry.setText("Reintentar");
        retry.setOnClickListener(v -> activity.recreate());
        timeoutActions.addView(retry);

        Button compatible = new Button(activity);
        compatible.setText("Modo compatible");
        compatible.setOnClickListener(v -> {
            SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(activity);
            preferences.edit().putBoolean("hikari_compat_mode", true).apply();
            activity.finish();
        });
        timeoutActions.addView(compatible);

        Button diagnostic = new Button(activity);
        diagnostic.setText("Copiar diagnóstico");
        diagnostic.setOnClickListener(v -> copyDiagnostic());
        timeoutActions.addView(diagnostic);
        root.addView(timeoutActions, new LinearLayout.LayoutParams(-1, -2));

        ScrollView scroll = new ScrollView(activity);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.TRANSPARENT);
        scroll.addView(root, new ScrollView.LayoutParams(-1, -1));
        frame.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        dialog.setContentView(frame);

        Window window = dialog.getWindow();
        if (window != null) {
            window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            window.setDimAmount(0f);
            window.setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT);
        }
    }

    private void copyDiagnostic() {
        String value = "HikariRO Mobile 0.8\n" +
            "Stage: " + currentStage + "\n" +
            "Executable: " + activity.getIntent().getStringExtra("exec_path") + "\n" +
            "Compatible mode: " + activity.getIntent().getBooleanExtra("hikari_compat_mode", true) + "\n" +
            "Device: " + Build.MANUFACTURER + " " + Build.MODEL + "\n" +
            "Android: " + Build.VERSION.RELEASE + " (SDK " + Build.VERSION.SDK_INT + ")\n" +
            "ABI: " + String.join(",", Build.SUPPORTED_ABIS) + "\n" +
            "--- Traza interna ---\n" + readLastLogLines(new File(activity.getFilesDir(), "hikari-trace.log"), 160) +
            "--- Box64 / Wine ---\n" + readLastLogLines(new File(activity.getFilesDir(), "hikari-startup.log"), 120);
        ClipboardManager clipboard = (ClipboardManager)activity.getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("HikariRO diagnosis", value));
        stage.setText(currentStage + "\nDiagnóstico copiado al portapapeles.");
    }

    private String readLastLogLines(File log, int maximum) {
        if (!log.isFile()) return "No se creó el registro de inicio.";
        ArrayList<String> lines = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(log))) {
            String line;
            while ((line = reader.readLine()) != null) {
                lines.add(line);
                if (lines.size() > maximum) lines.remove(0);
            }
        } catch (Exception e) { return "No se pudo leer el registro: " + e.getMessage(); }
        StringBuilder result = new StringBuilder();
        for (String line : lines) result.append(line).append('\n');
        return result.length() == 0 ? "Registro vacío." : result.toString();
    }

    private TextView label(float size, int color) {
        TextView view = new TextView(activity);
        view.setTextSize(size);
        view.setTextColor(color);
        return view;
    }

    private LinearLayout.LayoutParams margins(int width, int height, int top, int bottom) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(width, height);
        params.setMargins(0, dp(top), 0, dp(bottom));
        return params;
    }

    private int dp(int value) { return (int)(value * activity.getResources().getDisplayMetrics().density + 0.5f); }
}
