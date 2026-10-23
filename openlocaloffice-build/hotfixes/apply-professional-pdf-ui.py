from pathlib import Path
import re

root = Path("app/src/main")
css = root / "assets/style.css"
gradle = Path("app/build.gradle.kts")

source = css.read_text()
source += r"""

/* File Gestioner 0.10.3 — mobile-first, gesture-capable PDF reading */
#editor.fg-reader-host{position:relative;isolation:isolate}
.fg-pdf-scroll{
  touch-action:pan-x pan-y;
  -webkit-overflow-scrolling:touch;
  overscroll-behavior:contain;
  scroll-behavior:auto!important;
  scroll-padding:0;
  overflow:auto!important;
  width:100%;
  flex:1 1 auto;
  min-height:0;
  background:#0e1420;
  padding:0 0 calc(28px + env(safe-area-inset-bottom))!important;
}
.fg-pdf-stack{
  width:100%;
  min-width:0;
  max-width:none!important;
  box-sizing:border-box;
  margin:0;
  transform:none;
  user-select:none;
  -webkit-user-select:none;
}
.fg-pdf-container{
  gap:7px;
  padding:4px 0 calc(25px + env(safe-area-inset-bottom));
  box-sizing:border-box;
  width:100%;
  min-width:0;
}
.fg-pdf-section{
  position:relative;
  background:#fff;
  width:100%;
  min-width:0;
  flex-shrink:0;
  box-shadow:0 2px 9px #0003;
  touch-action:pan-x pan-y;
}
.fg-pdf-img{
  width:100%;
  height:100%;
  object-fit:fill;
  pointer-events:none;
  -webkit-user-drag:none;
  user-select:none;
}
.fg-pdf-skeleton{font-size:12px;letter-spacing:.01em;min-height:0}
.fg-pdf-toolbar{
  display:flex;
  align-items:center;
  gap:8px;
  background:color-mix(in srgb,var(--fg-card) 94%,transparent);
  backdrop-filter:blur(18px) saturate(125%);
}
.fg-pdf-toolbar .fg-reader-desc{display:none}
.fg-pdf-toolbar .fg-reader-tools{
  display:flex!important;
  flex-wrap:nowrap!important;
  gap:5px;
  align-items:center;
  width:auto;
  min-width:0;
}
.fg-pdf-toolbar .fg-reader-button{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:12px;
  min-width:39px;
  min-height:39px;
  padding:7px 9px;
  font-size:17px;
  font-weight:700;
  background:color-mix(in srgb,var(--fg-card) 80%,#9da9c8 20%);
  border:1px solid color-mix(in srgb,var(--fg-border) 85%,#fff 15%);
  color:var(--fg-text);
}
.fg-pdf-toolbar .fg-reader-button:active{background:#3c4d75}
.fg-pdf-toolbar .fg-pdf-percent{
  min-width:56px;
  font:650 12px system-ui;
  letter-spacing:-.01em;
  background:transparent;
  color:var(--fg-text);
  border-color:transparent;
}
.fg-pdf-toolbar .fg-reader-button:last-child{
  padding:8px 13px;min-width:45px;font-size:12px;
  background:var(--fg-accent);
  border-color:transparent;color:#fff
}
.fg-pdf-toolbar .fg-reader-counter{
  display:inline-block;
  text-align:center;
  min-width:44px;
  font:650 12px system-ui;
  padding:0 5px;
  white-space:nowrap;
  color:var(--fg-text);
}
.fg-pdf-page-label{font-size:11px;color:var(--fg-muted)}
body.fg-pdf-reading .bar .actions button:disabled{display:none!important}
@media(max-width:680px){
  body.fg-pdf-reading .bar{
    padding:6px 10px 7px;
    min-height:51px!important;
  }
  body.fg-pdf-reading .brand strong{font-size:13px}
  body.fg-pdf-reading .brand #status{
    font-size:10px;
    max-width:58vw;
    overflow:hidden;
    text-overflow:ellipsis;
    white-space:nowrap;
  }
  body.fg-pdf-reading .bar .actions{gap:4px}
  body.fg-pdf-reading .bar .actions button{
    min-height:36px;padding:7px 12px;font-size:12px;
  }
  .fg-pdf-toolbar{
    position:absolute!important;
    left:50%!important;
    bottom:calc(13px + env(safe-area-inset-bottom))!important;
    top:auto!important;
    transform:translateX(-50%);
    width:max-content;
    max-width:calc(100vw - 18px);
    padding:7px 9px!important;
    z-index:80;
    display:flex!important;
    border:1px solid #69789355!important;
    border-radius:18px!important;
    box-shadow:0 14px 42px #0008!important;
    background:color-mix(in srgb,var(--fg-card) 95%,transparent)!important;
    flex:0 0 auto;
  }
  .fg-pdf-toolbar .fg-reader-kind,
  .fg-pdf-toolbar .fg-reader-title,
  .fg-pdf-toolbar .fg-reader-desc,
  .fg-pdf-toolbar .fg-pdf-page-label{display:none!important}
  .fg-pdf-toolbar .fg-reader-tools{
    display:flex!important;flex:0 0 auto!important;
    width:auto!important;gap:3px!important;
    flex-wrap:nowrap!important;justify-content:center
  }
  .fg-pdf-toolbar .fg-reader-button{
    min-width:35px;min-height:37px;padding:6px 8px;font-size:18px;
    border-radius:11px
  }
  .fg-pdf-toolbar .fg-pdf-percent{
    min-width:47px;font-size:11px;padding:5px 3px
  }
  .fg-pdf-toolbar .fg-reader-counter{min-width:40px;font-size:11px;padding:0 5px}
  .fg-pdf-toolbar .fg-reader-button:last-child{min-width:41px;padding:7px 8px;font-size:11px}
  .fg-pdf-scroll{padding:0!important}
  .fg-pdf-container{gap:5px;padding:2px 0 calc(84px + env(safe-area-inset-bottom))}
}
"""
css.write_text(source)
version=gradle.read_text()
version,n=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda m:"versionCode = "+str(int(m.group(1))+1),version,count=1)
assert n==1
version,n=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.10.3"',version,count=1)
assert n==1
gradle.write_text(version)
print("File Gestioner v0.10.3 responsive PDF UI + pinch-zoom surface: OK")
