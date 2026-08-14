from pathlib import Path
import re

root = Path("winlator/app")

build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
# Deliberately use a high monotonic versionCode so Android always treats this as
# newer than all 0.7-0.15 test builds already installed on devices.
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("1501")', text, count=1)
text = re.sub(r"versionName\s+[^\n]+", 'versionName String.valueOf("0.15.1-beta")', text, count=1)
build.write_text(text, encoding="utf-8")

for rel in [
    "app/src/main/java/com/winlator/HikariDiagnostics.java",
    "app/src/main/java/com/winlator/HikariStartupDialog.java",
    "app/src/main/java/com/winlator/HikariLauncherActivity.java",
]:
    p = root / rel
    s = p.read_text(encoding="utf-8").replace("0.15", "0.15.1")
    p.write_text(s, encoding="utf-8")

print("0.15.1 patch applied: versionCode=1501")
