from pathlib import Path
import re

root = Path('winlator/app')

# 0.18 runtime candidate: prioritize reaching Box64/Wine.
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
    if p.exists():
        p.write_text(p.read_text(encoding='utf-8').replace('0.17', '0.18'), encoding='utf-8')

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

guest.write_text(t, encoding='utf-8')
print('0.18 runtime patch applied: copyBox64RC bypass enabled')
