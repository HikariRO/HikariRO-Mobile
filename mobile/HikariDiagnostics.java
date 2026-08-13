package com.winlator;

import android.content.Context;

import com.winlator.core.ProcessHelper;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class HikariDiagnostics {
    private HikariDiagnostics() {}

    public static synchronized void reset(Context context) {
        File file = file(context);
        if (file.isFile()) file.delete();
        record(context, "Inicio del diagnóstico 0.6");
    }

    public static synchronized void record(Context context, String message) {
        try (FileWriter writer = new FileWriter(file(context), true)) {
            String time = new SimpleDateFormat("HH:mm:ss.SSS", Locale.US).format(new Date());
            writer.write("[" + time + "] " + message + "\n");
        } catch (Exception ignored) {}
    }

    public static synchronized void processes(Context context) {
        List<ProcessHelper.PStat> processes = ProcessHelper.getChildProcesses();
        record(context, "Procesos detectados: " + processes.size());
        for (ProcessHelper.PStat process : processes) record(context, "  " + process.toString());
    }

    public static File file(Context context) {
        return new File(context.getFilesDir(), "hikari-trace.log");
    }
}
