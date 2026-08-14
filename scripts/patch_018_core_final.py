from pathlib import Path
import re
root=Path('winlator/app')
build=root/'app/build.gradle'; s=build.read_text(); s=re.sub(r'versionCode\s+[^\n]+','versionCode Integer.parseInt("1800")',s,1); s=re.sub(r'versionName\s+[^\n]+','versionName String.valueOf("0.18.0-beta")',s,1); build.write_text(s)
for rel in ['app/src/main/java/com/winlator/HikariDiagnostics.java','app/src/main/java/com/winlator/HikariStartupDialog.java','app/src/main/java/com/winlator/HikariLauncherActivity.java']:
 p=root/rel; p.write_text(p.read_text().replace('0.17','0.18'))
g=root/'app/src/main/java/com/winlator/xenvironment/components/GuestProgramLauncherComponent.java'; t=g.read_text()
t=t.replace('HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC BEGIN");\n                copyDefaultBox64RCFile();\n                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC END");','File hikariRcFile = new File(environment.getRootFS().getRootDir(), "/etc/config.box64rc");\n                HikariDiagnostics.record(hikariContext, "GPL STEP copyBox64RC BYPASSED existing=" + hikariRcFile.isFile() + " size=" + (hikariRcFile.isFile() ? hikariRcFile.length() : 0));')
g.write_text(t)
print('0.18 final core patch')