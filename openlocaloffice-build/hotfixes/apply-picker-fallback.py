from pathlib import Path

JAVA = Path("app/src/main/java/com/openlocal/office/MainActivity.java")
MANIFEST = Path("app/src/main/AndroidManifest.xml")

def method_span(text: str, signature: str) -> tuple[int, int]:
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise RuntimeError(f"Unclosed method: {signature}")

java = JAVA.read_text()
start, end = method_span(java, "private void openPicker(")
body = java[start:end]

# Android/Samsung file providers do not agree on a stable MIME type for .sdocx.
# Keep ACTION_OPEN_DOCUMENT at */* and remove the MIME whitelist entirely;
# OpenLocalOffice validates the selected file itself by name/MIME/content.
import re
body2 = re.sub(
    r'\s*intent\.putExtra\(Intent\.EXTRA_MIME_TYPES\s*,\s*new String\[\]\s*\{.*?\}\s*\);',
    '',
    body,
    flags=re.S,
)
if body2 == body:
    body2 = re.sub(
        r'\s*\w+\.putExtra\(Intent\.EXTRA_MIME_TYPES\s*,\s*new String\[\]\s*\{.*?\}\s*\);',
        '',
        body,
        flags=re.S,
    )
if body2 == body:
    raise RuntimeError("Could not locate openPicker MIME whitelist")
if '"*/*"' not in body2:
    raise RuntimeError("openPicker is not using */* after whitelist removal")
java = java[:start] + body2 + java[end:]
JAVA.write_text(java)

manifest = MANIFEST.read_text()
fallback = '                <data android:mimeType="application/*" />\n'
if fallback not in manifest:
    marker = '                <data android:mimeType="application/zip" />\n'
    if marker not in manifest:
        raise RuntimeError("Could not locate manifest MIME block")
    manifest = manifest.replace(marker, marker + fallback, 1)
MANIFEST.write_text(manifest)
