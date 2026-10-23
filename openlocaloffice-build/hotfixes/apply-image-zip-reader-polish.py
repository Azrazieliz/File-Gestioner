from pathlib import Path
import re
css=Path("app/src/main/assets/style.css")
gradle=Path("app/build.gradle.kts")
style=css.read_text()
style+="""

/* File Gestioner 0.12.1 — image-rich ZIP opens as a continuous comic */
.fg-archive-scroll:has(.fg-comic-stack){
  background:#0b0f17!important;
  overflow-y:auto!important;overflow-x:auto!important;
  padding:0 0 calc(85px + env(safe-area-inset-bottom))!important;
}
.fg-archive-scroll:has(.fg-comic-stack) .fg-comic-stack{
  max-width:none!important;width:100%;margin:0 auto;
}
.fg-archive-scroll:has(.fg-comic-stack) .fg-comic-section{
  min-height:110px;margin:0 auto 3px;width:100%;
  background:transparent;border:0;box-shadow:none;
}
.fg-archive-scroll:has(.fg-comic-stack) .fg-comic-page{
  margin:0;padding:0;width:100%;
}
.fg-archive-scroll:has(.fg-comic-stack) img{
  width:100%!important;height:auto!important;max-width:none!important;
  object-fit:contain;display:block;margin:0 auto;
}
.fg-reader-toolbar .fg-reader-counter{font-variant-numeric:tabular-nums}
@media(max-width:700px){
 .fg-archive-scroll:has(.fg-comic-stack){padding-top:0!important}
 .fg-archive-scroll:has(.fg-comic-stack) .fg-comic-section{margin-bottom:2px}
 .fg-archive-scroll:has(.fg-comic-stack) .fg-comic-stack{width:100%}
}
"""
css.write_text(style)
content=gradle.read_text()
content,n=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda m:'versionCode = '+str(int(m.group(1))+1),content,count=1)
assert n==1
content,n=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.12.1"',content,count=1)
assert n==1
gradle.write_text(content)
print("0.12.1: image ZIP continuous premium reader and source URI hardening")
