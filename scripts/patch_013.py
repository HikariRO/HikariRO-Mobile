from pathlib import Path
import re, base64
root = Path('winlator/app')
build = root / 'app/build.gradle'
text = build.read_text(encoding='utf-8')
text = re.sub(r'versionCode\s+[^\n]+', 'versionCode Integer.parseInt("13")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.13.0-beta")', text, count=1)
build.write_text(text, encoding='utf-8')
for rel in ['app/src/main/java/com/winlator/HikariDiagnostics.java','app/src/main/java/com/winlator/HikariStartupDialog.java','app/src/main/java/com/winlator/HikariLauncherActivity.java']:
    p = root / rel
    p.write_text(p.read_text(encoding='utf-8').replace('0.12','0.13'), encoding='utf-8')
guest = root / 'app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java'
text = guest.read_text(encoding='utf-8')
needle = '        File box64File = new File(rootDir, "/usr/local/bin/box64");'
insert = base64.b64decode('ICAgICAgICBTdHJpbmcgbGF1bmNoRXhlY3V0YWJsZSA9IGd1ZXN0RXhlY3V0YWJsZTsKICAgICAgICBpZiAoZ3Vlc3RFeGVjdXRhYmxlICE9IG51bGwgJiYgZ3Vlc3RFeGVjdXRhYmxlLmNvbnRhaW5zKCJ3aW5oYW5kbGVyLmV4ZSIpKSB7CiAgICAgICAgICAgIEZpbGUgd2luZUJpbmFyeSA9IG5ldyBGaWxlKHJvb3REaXIsIHJvb3RGUy5nZXRXaW5lUGF0aCgpKyIvYmluL3dpbmUiKTsKICAgICAgICAgICAgRmlsZSB3aW5lU2VydmVyID0gbmV3IEZpbGUocm9vdERpciwgcm9vdEZTLmdldFdpbmVQYXRoKCkrIi9iaW4vd2luZXNlcnZlciIpOwogICAgICAgICAgICBIaWthcmlEaWFnbm9zdGljcy5yZWNvcmQoZW52aXJvbm1lbnQuZ2V0Q29udGV4dCgpLCAiMC4xMyBkaXJlY3QgV2luZSBsYXVuY2ggaGFiaWxpdGFkbyIpOwogICAgICAgICAgICBIaWthcmlEaWFnbm9zdGljcy5yZWNvcmQoZW52aXJvbm1lbnQuZ2V0Q29udGV4dCgpLCAid2luZSBleGlzdHM9IiArIHdpbmVCaW5hcnkuaXNGaWxlKCkpOwogICAgICAgICAgICBIaWthcmlEaWFnbm9zdGljcy5yZWNvcmQoZW52aXJvbm1lbnQuZ2V0Q29udGV4dCgpLCAid2luZXNlcnZlciBleGlzdHM9IiArIHdpbmVTZXJ2ZXIuaXNGaWxlKCkpOwogICAgICAgICAgICBsYXVuY2hFeGVjdXRhYmxlID0gIndpbmUgY21kIC9jIFwiRTogJiYgY2QgXFxIaWthcmlSTyAmJiByYWdoaWthcmkuZXhlXCIiOwogICAgICAgIH0KCiAgICAgICAgRmlsZSBib3g2NEZpbGUgPSBuZXcgRmlsZShyb290RGlyLCAiL3Vzci9sb2NhbC9iaW4vYm94NjQiKTs=').decode()
if needle not in text:
    raise RuntimeError('missing insertion point')
text = text.replace(needle, insert, 1)
text = text.replace('box64File.getAbsolutePath()+" "+guestExecutable', 'box64File.getAbsolutePath()+" "+launchExecutable')
text = text.replace('" guestExecutable=" + guestExecutable', '" guestExecutable=" + launchedExecutable')
marker = '        HikariDiagnostics.record(environment.getContext(), "Comando Box64/Wine preparado: " + command);\n'
if marker not in text:
    raise RuntimeError('missing process marker')
text = text.replace(marker, marker + '        final String launchedExecutable = launchExecutable;\n', 1)
guest.write_text(text, encoding='utf-8')
