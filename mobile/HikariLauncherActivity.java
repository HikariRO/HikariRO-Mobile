package com.winlator;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.StatFs;
import android.content.SharedPreferences;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.preference.PreferenceManager;

import com.winlator.box64.Box64Preset;
import com.winlator.container.Container;
import com.winlator.container.ContainerManager;
import com.winlator.core.AppUtils;
import com.winlator.xenvironment.RootFS;
import com.winlator.xenvironment.RootFSInstaller;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.concurrent.Executors;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class HikariLauncherActivity extends AppCompatActivity {
    private static final String MANIFEST_URL = "https://hikariro.com/download/mobile/mobile.json";
    private static final String CLIENT_URL = "https://hikariro.com/download/mobile/HikariRO%20Full.zip";
    private static final long CLIENT_ZIP_SIZE = 4820383759L;
    private static final long REQUIRED_FREE_BYTES = 15L * 1024L * 1024L * 1024L;
    private static final String EXE = "raghikari.exe";
    private ClientInfo client = new ClientInfo("legacy-20260812", CLIENT_URL, CLIENT_ZIP_SIZE, "");

    private TextView status;
    private ProgressBar progress;
    private Button action;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        AppUtils.keepScreenOn(this);
        buildUi();
        refresh();
    }

    private File storageDir() { return new File(AppUtils.INTERNAL_STORAGE); }
    private File gameDir() { return new File(storageDir(), "HikariRO"); }
    private File executable() { return new File(gameDir(), EXE); }
    private File archive() { return new File(getExternalFilesDir(null), "HikariRO-Full.zip.part"); }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(48, 32, 48, 32);
        root.setBackgroundColor(Color.rgb(18, 18, 24));

        TextView title = new TextView(this);
        title.setText("HikariRO Mobile");
        title.setTextColor(Color.WHITE);
        title.setTextSize(30);
        title.setGravity(Gravity.CENTER);
        root.addView(title, new LinearLayout.LayoutParams(-1, -2));

        status = new TextView(this);
        status.setTextColor(Color.LTGRAY);
        status.setTextSize(17);
        status.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams statusParams = new LinearLayout.LayoutParams(-1, -2);
        statusParams.setMargins(0, 28, 0, 24);
        root.addView(status, statusParams);

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        root.addView(progress, new LinearLayout.LayoutParams(-1, -2));

        action = new Button(this);
        LinearLayout.LayoutParams buttonParams = new LinearLayout.LayoutParams(-2, -2);
        buttonParams.setMargins(0, 28, 0, 0);
        root.addView(action, buttonParams);
        setContentView(root);
    }

    private void refresh() {
        if (executable().isFile()) {
            progress.setVisibility(View.GONE);
            status.setText("Cliente instalado. Pulsa Jugar para iniciar HikariRO.");
            action.setText("Jugar");
            action.setOnClickListener(v -> prepareAndLaunch());
            checkForUpdates();
        } else {
            progress.setVisibility(View.VISIBLE);
            status.setText("La primera instalación descargará aproximadamente 4,5 GB.\nSe recomiendan 15 GB libres y conexión Wi-Fi.");
            action.setText(archive().exists() ? "Continuar instalación" : "Instalar");
            action.setOnClickListener(v -> install());
        }
    }

    private void install() {
        action.setEnabled(false);
        if (new StatFs(getFilesDir().getPath()).getAvailableBytes() < REQUIRED_FREE_BYTES && !archive().exists()) {
            fail("No hay espacio suficiente. Libera al menos 15 GB e inténtalo de nuevo.");
            return;
        }
        RootFSInstaller.installIfNeeded(this);
        Executors.newSingleThreadExecutor().execute(() -> {
            try {
                client = fetchClientInfo();
                download();
                extract();
                PreferenceManager.getDefaultSharedPreferences(this).edit().putString("hikari_client_version", client.version).apply();
                archive().delete();
                runOnUiThread(() -> { action.setEnabled(true); refresh(); });
            } catch (Exception e) {
                fail("La instalación no pudo completarse: " + e.getMessage());
            }
        });
    }

    private void download() throws Exception {
        File part = archive();
        File parent = part.getParentFile();
        if (parent != null) parent.mkdirs();
        long existing = part.isFile() ? part.length() : 0;
        if (existing > client.size) { part.delete(); existing = 0; }
        while (existing < client.size) {
            final long offset = existing;
            update("Descargando cliente " + client.version + "…", (int)(offset * 1000L / client.size));
            HttpURLConnection connection = (HttpURLConnection)new URL(client.url).openConnection();
            connection.setConnectTimeout(30000);
            connection.setReadTimeout(30000);
            if (offset > 0) connection.setRequestProperty("Range", "bytes=" + offset + "-");
            int code = connection.getResponseCode();
            if (offset > 0 && code != 206) { part.delete(); existing = 0; connection.disconnect(); continue; }
            if (offset == 0 && code != 200) throw new Exception("servidor HTTP " + code);
            try (InputStream in = new BufferedInputStream(connection.getInputStream());
                 FileOutputStream out = new FileOutputStream(part, offset > 0)) {
                byte[] buffer = new byte[1024 * 1024];
                int count; long done = offset; long lastUi = 0;
                while ((count = in.read(buffer)) != -1) {
                    out.write(buffer, 0, count); done += count;
                    if (done - lastUi >= 8L * 1024L * 1024L) {
                        update("Descargando cliente " + client.version + "…", (int)(done * 1000L / client.size));
                        lastUi = done;
                    }
                }
            } finally { connection.disconnect(); }
            existing = part.length();
        }
        if (part.length() != client.size) throw new Exception("tamaño de descarga incorrecto");
        if (!client.sha256.isEmpty() && !client.sha256.equalsIgnoreCase(sha256(part))) {
            throw new Exception("la comprobación SHA-256 no coincide");
        }
    }

    private void extract() throws Exception {
        storageDir().mkdirs();
        String root = storageDir().getCanonicalPath() + File.separator;
        int entries = 0;
        update("Extrayendo cliente…", 0);
        try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(new FileInputStream(archive()), 1024 * 1024))) {
            ZipEntry entry;
            byte[] buffer = new byte[1024 * 1024];
            while ((entry = zip.getNextEntry()) != null) {
                File output = new File(storageDir(), entry.getName());
                if (!output.getCanonicalPath().startsWith(root)) throw new Exception("entrada ZIP no válida");
                if (entry.isDirectory()) output.mkdirs();
                else {
                    File parent = output.getParentFile(); if (parent != null) parent.mkdirs();
                    try (BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream(output), 1024 * 1024)) {
                        int count; while ((count = zip.read(buffer)) != -1) out.write(buffer, 0, count);
                    }
                }
                entries++;
                if ((entries & 31) == 0) update("Extrayendo cliente… " + entries + " archivos", Math.min(999, entries * 1000 / 6154));
                zip.closeEntry();
            }
        }
        if (!executable().isFile()) throw new Exception("no se encontró " + EXE);
    }

    private void prepareAndLaunch() {
        action.setEnabled(false);
        status.setText("Preparando el entorno de juego…");
        RootFSInstaller.installIfNeeded(this);
        waitForRootFs(0);
    }

    private void waitForRootFs(int attempt) {
        RootFS rootFS = RootFS.find(this);
        if (rootFS.isValid() && rootFS.getVersion() >= RootFSInstaller.LATEST_VERSION) {
            createContainerAndLaunch();
        } else if (attempt < 600) {
            status.postDelayed(() -> waitForRootFs(attempt + 1), 500);
        } else fail("No se pudo preparar el entorno Wine.");
    }

    private void createContainerAndLaunch() {
        ContainerManager manager = new ContainerManager(this);
        Container container = null;
        for (Container item : manager.getContainers()) if ("HikariRO".equals(item.getName())) { container = item; break; }
        boolean compatible = PreferenceManager.getDefaultSharedPreferences(this).getBoolean("hikari_compat_mode", false);
        if (container != null) {
            applyGraphicsMode(container, compatible);
            launch(container);
            return;
        }
        try {
            JSONObject data = new JSONObject();
            data.put("name", "HikariRO");
            data.put("screenSize", "960x540");
            data.put("graphicsDriver", compatible ? "vortek,virgl" : "vortek,gladio");
            data.put("dxwrapper", compatible ? "wined3d" : "dxvk");
            data.put("box64Preset", Box64Preset.PERFORMANCE);
            data.put("drives", "E:" + AppUtils.INTERNAL_STORAGE);
            manager.createContainerAsync(data, created -> {
                if (created == null) fail("No se pudo crear el contenedor de HikariRO.");
                else launch(created);
            });
        } catch (Exception e) { fail("No se pudo configurar HikariRO: " + e.getMessage()); }
    }

    private void launch(Container container) {
        Intent intent = new Intent(this, XServerDisplayActivity.class);
        intent.putExtra("container_id", container.id);
        intent.putExtra("exec_path", executable().getAbsolutePath());
        startActivity(intent);
        action.setEnabled(true);
    }

    private void applyGraphicsMode(Container container, boolean compatible) {
        container.setGraphicsDriver(compatible ? "vortek,virgl" : "vortek,gladio");
        container.setDXWrapper(compatible ? "wined3d" : "dxvk");
        container.saveData();
    }

    private void checkForUpdates() {
        Executors.newSingleThreadExecutor().execute(() -> {
            try {
                ClientInfo remote = fetchClientInfo();
                SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(this);
                String installed = prefs.getString("hikari_client_version", "legacy-20260812");
                if (!remote.version.equals(installed)) runOnUiThread(() -> {
                    client = remote;
                    status.setText("Hay una actualización del cliente disponible: " + remote.version);
                    action.setText("Actualizar");
                    action.setOnClickListener(v -> install());
                });
            } catch (Exception ignored) {}
        });
    }

    private ClientInfo fetchClientInfo() throws Exception {
        HttpURLConnection connection = (HttpURLConnection)new URL(MANIFEST_URL).openConnection();
        connection.setConnectTimeout(8000);
        connection.setReadTimeout(8000);
        try {
            if (connection.getResponseCode() != 200) return client;
            StringBuilder json = new StringBuilder();
            try (InputStream in = connection.getInputStream()) {
                byte[] buffer = new byte[8192]; int count;
                while ((count = in.read(buffer)) != -1) json.append(new String(buffer, 0, count, java.nio.charset.StandardCharsets.UTF_8));
            }
            JSONObject value = new JSONObject(json.toString());
            return new ClientInfo(value.getString("version"), value.getString("url"), value.getLong("size"), value.optString("sha256", ""));
        } finally { connection.disconnect(); }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buffer = new byte[1024 * 1024]; int count;
            while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        StringBuilder value = new StringBuilder();
        for (byte b : digest.digest()) value.append(String.format(Locale.US, "%02x", b & 0xff));
        return value.toString();
    }

    private static class ClientInfo {
        final String version, url, sha256;
        final long size;
        ClientInfo(String version, String url, long size, String sha256) {
            this.version = version; this.url = url; this.size = size; this.sha256 = sha256;
        }
    }

    private void update(String message, int value) {
        runOnUiThread(() -> { status.setText(message); progress.setProgress(value); });
    }

    private void fail(String message) {
        runOnUiThread(() -> {
            status.setText(message);
            action.setText("Reintentar");
            action.setEnabled(true);
            action.setOnClickListener(v -> install());
        });
    }
}
