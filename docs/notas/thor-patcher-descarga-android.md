# Thor Patcher: descarga de parches grandes (Android/Wine)

## Incidencia observada (18-11-2026)
- Archivo: `20261025_palette_fix.thor` (~189 MiB).
- La descarga en la ventana de `HikariRO.exe` se detiene de forma variable, a veces nada mas empezar y otras tras transferir parte del fichero.
- Los parches mas pequenos funcionan.
- **No esta demostrada la causa**: Wine/WinINet, servidor/CDN, red, ruta temporal o procesamiento interno.

## Alcance de esta rama
La clase `HikariThorDownloadMonitor` registra en Logcat (`HikariThor`) los cambios de tamano de candidatos `.thor`, `.tmp`, `.part` y `.download` situados en la carpeta privada del cliente y subdirectorios cercanos. Si ya observo un candidato y pasan 90 segundos sin cambios, registra una advertencia con el espacio libre.

No modifica `HikariRO.exe`, ningun parche, la red ni el GRF. Tampoco interpreta un archivo inmovil como prueba definitiva de bloqueo: el patcher puede usar memoria o rutas temporales de Wine que este monitor no ve. Este cambio es **diagnostico**, no una correccion confirmada.

## Prueba en dispositivo
1. Compilar e instalar APK de esta rama (sin borrar los datos de la app).
2. Conectar Android por USB y ejecutar `adb logcat -c`.
3. Capturar `adb logcat -v time -s HikariThor:I HikariRO:I '*:S' > thor-mobile.log`.
4. Iniciar la app y dejar que el patcher intente descargar el archivo grande. Anotar la hora, el porcentaje visible y si cambia.
5. Esperar al menos 90 s cuando parezca bloqueado y guardar `thor-mobile.log`.
6. Comprobar si hay lineas `Archivo de parche` y si los bytes siguen aumentando. Si no aparecen, el monitor no ha localizado la descarga: **no concluir que no se esta descargando**.

## Diagnosticos siguientes
- Comprobar la URL de parches, respuestas HTTP (200/206, Content-Length, Accept-Ranges), redirecciones y estabilidad del host.
- Localizar en el cliente real la configuracion Thor, carpeta de descargas y rutas temporales de Wine antes de desarrollar un descargador Android alternativo.
- Comparar la descarga del mismo fichero en Android nativo y dentro de Wine.
- Si se implementa descarga nativa, validar integridad y el mecanismo de handoff con Thor antes de aplicarlo; nunca marcar un parche como instalado sin aplicarlo.

## Criterio de aceptacion final
Reproducir sobre el dispositivo afectado: descargar completo `20261025_palette_fix.thor`, aplicar el parche, actualizar el historial de Thor correctamente y continuar con los siguientes parches. Mantener `main` intacta hasta entonces.
