from pathlib import Path
import re

root = Path("winlator/app")
build = root / "app/build.gradle"
text = build.read_text(encoding="utf-8")
text = re.sub(r"versionCode\s+[^\n]+", 'versionCode Integer.parseInt("10")', text, count=1)
text = re.sub(r'versionName\s+[^\n]+', 'versionName String.valueOf("0.10.0-beta")', text, count=1)
build.write_text(text, encoding="utf-8")
