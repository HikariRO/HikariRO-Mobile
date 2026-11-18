package com.winlator.hikariro;

import android.os.Handler;
import android.os.Looper;
import android.os.StatFs;
import android.os.SystemClock;
import android.util.Log;

import java.io.File;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Diagnostico no invasivo de los archivos de parche que Thor escribe bajo el cliente.
 * No descarga, renombra ni borra archivos. No diagnostica trafico HTTP por si solo:
 * Thor puede mantener datos en memoria o usar una ruta temporal de Wine.
 */
public final class HikariThorDownloadMonitor {
    private static final String TAG = "HikariThor";
    private static final long INTERVAL_MS = 5000L;
    private static final long STALL_MS = 90000L;
    private static final int MAX_DEPTH = 3;
    private static final int MAX_ENTRIES = 20000;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final File clientDir;
    private final Map<String, Long> sizes = new HashMap<>();
    private long lastChangeMs;
    private boolean active;
    private boolean seenCandidate;
    private boolean warned;

    public HikariThorDownloadMonitor(File clientDir) {
        this.clientDir = clientDir;
    }

    public void start() {
        if (active) return;
        active = true;
        lastChangeMs = SystemClock.elapsedRealtime();
        Log.i(TAG, "Monitor Thor iniciado; ruta=" + clientDir.getAbsolutePath());
        handler.post(sample);
    }

    public void stop() {
        if (!active) return;
        active = false;
        handler.removeCallbacks(sample);
        Log.i(TAG, "Monitor Thor detenido");
    }

    private final Runnable sample = new Runnable() {
        @Override
        public void run() {
            if (!active) return;
            try {
                Map<String, Long> current = new HashMap<>();
                int[] visited = {0};
                collect(clientDir, 0, current, visited);
                Set<String> changed = new HashSet<>();
                for (Map.Entry<String, Long> item : current.entrySet()) {
                    Long previous = sizes.get(item.getKey());
                    if (previous == null || previous.longValue() != item.getValue()) {
                        changed.add(item.getKey());
                        Log.i(TAG, "Archivo de parche: " + item.getKey()
                            + " bytes=" + item.getValue()
                            + (previous == null ? " (nuevo)" : " delta=" + (item.getValue() - previous)));
                    }
                }
                if (!changed.isEmpty()) {
                    seenCandidate = true;
                    warned = false;
                    lastChangeMs = SystemClock.elapsedRealtime();
                }
                sizes.clear();
                sizes.putAll(current);
                if (seenCandidate && !warned
                    && SystemClock.elapsedRealtime() - lastChangeMs >= STALL_MS) {
                    long free = new StatFs(clientDir.getAbsolutePath()).getAvailableBytes();
                    Log.w(TAG, "Sin cambios en archivos de parche durante "
                        + STALL_MS / 1000 + " s; espacio_libre_bytes=" + free
                        + "; candidatos=" + current.size()
                        + ". Esto NO confirma por si solo un bloqueo HTTP.");
                    warned = true;
                }
                if (visited[0] >= MAX_ENTRIES) {
                    Log.w(TAG, "Limite de exploracion alcanzado; diagnostico parcial");
                }
            } catch (Exception e) {
                Log.w(TAG, "Error de muestreo (no afecta al patcher)", e);
            }
            if (active) handler.postDelayed(this, INTERVAL_MS);
        }
    };

    private static void collect(File dir, int depth, Map<String, Long> output, int[] visited) {
        if (depth > MAX_DEPTH || visited[0] >= MAX_ENTRIES || !dir.isDirectory()) return;
        File[] files = dir.listFiles();
        if (files == null) return;
        for (File file : files) {
            if (++visited[0] > MAX_ENTRIES) return;
            if (file.isDirectory()) {
                // No explorar arboles grandes que no albergan descargas.
                String name = file.getName().toLowerCase(java.util.Locale.ROOT);
                if (depth == 0 || name.contains("patch") || name.contains("temp")
                    || name.contains("thor") || name.contains("download")) {
                    collect(file, depth + 1, output, visited);
                }
            } else if (file.isFile() && isPatchCandidate(file.getName())) {
                output.put(file.getAbsolutePath(), file.length());
            }
        }
    }

    private static boolean isPatchCandidate(String name) {
        String lower = name.toLowerCase(java.util.Locale.ROOT);
        return lower.endsWith(".thor") || lower.endsWith(".tmp")
            || lower.endsWith(".part") || lower.endsWith(".download");
    }
}
