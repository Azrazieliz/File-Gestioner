from pathlib import Path
import re

root=Path("app/src/main")
css=root/"assets/style.css"
gradle=Path("app/build.gradle.kts")
source=css.read_text()
source+="""

/* File Gestioner 0.10.2 — one continuous vertical reading surface */
.fg-pdf-scroll{
  padding:0 0 calc(40px + env(safe-area-inset-bottom))!important;
  overflow-y:auto;overflow-x:auto;
  background:var(--fg-app-bg);
  overscroll-behavior-y:contain;scrollbar-gutter:stable;
}
.fg-pdf-stack{width:100%;min-width:0;margin:0 auto;box-sizing:border-box}
.fg-pdf-container{width:100%;display:flex;flex-direction:column;gap:10px;
  padding:8px 0 16px;box-sizing:border-box}
.fg-pdf-section{display:flex;flex-direction:column;justify-content:center;align-items:center;
  position:relative;width:100%;box-sizing:border-box;background:#fff;
  overflow:hidden;border:none;box-shadow:0 1px 9px rgba(0,0,0,.18)}
.fg-pdf-img{width:100%;height:100%;max-width:none;max-height:none;
  display:block;object-fit:contain;background:#fff}
.fg-pdf-skeleton{width:100%;height:100%;display:flex;align-items:center;
  justify-content:center;background:color-mix(in srgb,var(--fg-text) 5%,var(--fg-paper));
  color:var(--fg-reader-muted);font:500 12px system-ui}
.fg-pdf-progress{font-size:12px;font-weight:650}
.fg-text-scroll,.fg-archive-scroll,.fg-docx-scroll{overflow-y:auto;
  overscroll-behavior-y:contain;scrollbar-gutter:stable}
.fg-continuous-text,.fg-docx-sheet{min-height:0!important}
.fg-continuous-text{padding:clamp(18px,4vw,44px)}
.fg-raw-text{border:0;border-radius:0;background:transparent;margin:0;
  padding:0;overflow-wrap:anywhere;white-space:pre-wrap;
  font:400 13px/1.6 ui-monospace,Consolas,monospace}
.fg-comic-stack{width:100%;max-width:860px}
.fg-comic-section{min-height:180px;width:100%;margin:0 0 10px;
  background:var(--fg-paper);display:flex;align-items:center;justify-content:center}
.fg-comic-page{width:100%;min-width:0}
.fg-comic-page .fg-archive-img{width:100%;max-width:100%;height:auto;display:block;
  margin:0 auto;object-fit:contain}
.fg-archive-list{width:min(100%,900px);margin:auto;padding:5px}
.fg-archive-entry{border:1px solid var(--fg-reader-border);
 background:var(--fg-card);border-radius:9px;margin:7px 0;
 overflow:hidden;color:var(--fg-text)}
.fg-archive-summary{padding:12px 14px;cursor:pointer;overflow-wrap:anywhere;
 font:550 13px/1.55 system-ui}
.fg-archive-entry[open] .fg-archive-summary{border-bottom:1px solid var(--fg-reader-border)}
.fg-archive-preview{padding:12px 14px;max-height:none;overflow:visible}
.fg-archive-preview img{max-width:100%;height:auto;display:block;margin:auto}
.fg-reader-toolbar{padding:8px 12px}
.fg-reader-desc{font-size:11px}
@media(max-width:680px){
 .fg-reader-toolbar{display:flex;align-items:center;gap:5px;padding:7px 10px}
 .fg-reader-kind{font-size:9px}
 .fg-reader-title{max-width:calc(100vw - 145px);font-size:12px}
 .fg-reader-desc{display:none}
 .fg-reader-tools{width:auto;flex:1 1 100%;gap:5px;flex-wrap:nowrap}
 .fg-reader-button{min-width:34px;min-height:33px;padding:6px 9px}
 .fg-pdf-scroll{padding:0 0 40px!important}
 .fg-pdf-container{gap:7px;padding-top:3px}
 .fg-pdf-section{box-shadow:0 1px 5px #0003}
 .fg-continuous-text{min-height:0!important;padding:17px 15px}
 .fg-docx-sheet{min-height:0!important}
 .fg-archive-scroll{padding:8px 4px 45px}
}
"""
css.write_text(source)
version=gradle.read_text()
updated,count=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda m:'versionCode = '+str(int(m.group(1))+1),version,count=1)
assert count==1
updated,count=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.10.2"',updated,count=1)
assert count==1
gradle.write_text(updated)
print("Continuous-scrolling reader layout + v0.10.2 update: OK")
