from pathlib import Path
import re

root=Path("app/src/main")
index=root/"assets/index.html"
css=root/"assets/style.css"
gradle=Path("app/build.gradle.kts")
html=index.read_text()
anchor='<script src="model-viewer.bundle.js"></script>'
assert html.count(anchor)==1
html=html.replace(anchor,anchor+'\n<script src="unified-viewer-controls.js"></script>')
index.write_text(html)
css.write_text(css.read_text()+r"""

/* File Gestioner 0.11 — single mobile reading experience across all formats */
body.fg-unified-reading .bar{
  min-height:54px;
  padding:7px max(10px,env(safe-area-inset-right))
    7px max(10px,env(safe-area-inset-left));
}
body.fg-unified-reading .bar .brand strong{font-size:14px}
body.fg-unified-reading .bar .brand #status{
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  font-size:11px;
}
body.fg-unified-reading .bar button:disabled{display:none!important}
body.fg-unified-reading .bar .actions button{
  min-height:38px;font-size:12px;border-radius:12px;
}
.fg-unified-dock{
  position:fixed;
  z-index:85;
  bottom:calc(15px + env(safe-area-inset-bottom));
  left:50%;
  transform:translateX(-50%);
  display:flex;align-items:center;justify-content:center;gap:5px;
  padding:7px 9px;
  border:1px solid #6a799350;
  border-radius:19px;
  background:color-mix(in srgb,var(--fg-card,#181d27) 96%,transparent);
  box-shadow:0 12px 42px #0007;
  backdrop-filter:blur(20px) saturate(140%);
  max-width:calc(100vw - 28px);
  width:max-content;
  touch-action:manipulation;
}
.fg-unified-control,.fg-unified-scale{
  display:inline-flex;align-items:center;justify-content:center;
  height:39px;min-width:39px;padding:7px 10px;
  font-size:18px;font-weight:750;
  background:color-mix(in srgb,var(--fg-elevated,#25354b) 84%,#b4c8ff 16%);
  color:var(--fg-text,#f3f5ff);
  border:1px solid color-mix(in srgb,var(--fg-border,#45536a) 88%,#c6d9ff 12%);
  border-radius:12px;
  touch-action:manipulation;
}
.fg-unified-scale{min-width:60px;font:650 12px system-ui;background:transparent;border-color:transparent}
.fg-unified-control:last-child{
  min-width:47px;background:var(--fg-accent,#7285ff);
  color:#fff;font:750 12px system-ui;border-color:transparent
}
.fg-unified-control:active,.fg-unified-scale:active{transform:scale(.96)}
.fg-unified-control:focus-visible,.fg-unified-scale:focus-visible{outline:2px solid var(--fg-accent);outline-offset:2px}
.fg-unified-scroll{
  overflow:auto!important;
  overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;
  touch-action:pan-x pan-y;
  scroll-behavior:auto!important;
}
.fg-unified-image-scroll{display:block!important;text-align:center}
.fg-unified-image-scroll .fg-display-image{
  display:block!important;margin:0 auto;max-width:none!important;
  max-height:none!important;object-fit:contain!important;
  height:auto!important;box-shadow:none!important;border-radius:0!important;
}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar){
  gap:8px;
  min-height:45px;
  background:color-mix(in srgb,var(--fg-card) 94%,transparent);
  border-bottom:1px solid var(--fg-border);
  padding:7px 12px!important;
  display:flex;align-items:center;flex-wrap:wrap;
}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-desc{display:none}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-kind{
  padding:5px 7px;border-radius:7px;font-size:9px
}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-title{
  font-size:12px;max-width:clamp(110px,40vw,420px);font-weight:650
}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-tools{
  display:flex;align-items:center;gap:5px;flex-wrap:wrap
}
body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-button{
  font-size:11px;min-height:34px;min-width:34px;padding:6px 9px;border-radius:9px
}
body.fg-unified-reading .fg-reader-scroll:not(.fg-pdf-scroll){
  padding-bottom:calc(95px + env(safe-area-inset-bottom))!important;
}
body.fg-unified-reading .fg-comic-stack{max-width:none!important}
body.fg-unified-reading .fg-comic-page .fg-archive-img{width:100%!important;max-width:none!important}
body.fg-unified-editor #editor:not(.fg-reader-host){
  padding-bottom:calc(75px + env(safe-area-inset-bottom));
}
body.fg-unified-editor .editorGridWrap{overflow:auto!important;max-height:none!important}
body.fg-unified-editor .sheetbar{padding:6px 10px;gap:4px}
body.fg-unified-editor .spreadsheetTools{padding:6px 8px;gap:5px}
body.fg-unified-editor .rangeNav{gap:5px}
body.fg-unified-editor .fg-docx-edit-scroll{
  padding-bottom:calc(110px + env(safe-area-inset-bottom))
}
body.fg-unified-editor .sdocxEditor{
  padding-bottom:calc(115px + env(safe-area-inset-bottom))
}
/* Native 3D interactions remain OrbitControls; same visual language/dock. */
body.fg-unified-reading .fg-3d-app{position:relative}
body.fg-unified-reading .fg-3d-toolbar{
  background:transparent;border-bottom:0;
  padding:8px 12px;
  min-height:44px;
}
body.fg-unified-reading .fg-3d-button,
body.fg-unified-reading .fg-3d-select{
  background:color-mix(in srgb,#1e293d 90%,#a0b8e5 10%);
  border:1px solid #5a708759;color:#f0f5ff;
  border-radius:11px;min-height:38px;
  font-size:12px;
}
body.fg-unified-reading .fg-3d-button:focus-visible{outline:2px solid #7c9cff}
body.fg-unified-reading .fg-3d-info{font-size:11px}
@media(max-width:700px){
  body.fg-unified-reading .bar{min-height:50px;gap:5px}
  body.fg-unified-reading .bar .brand strong{font-size:12px}
  body.fg-unified-reading .bar .brand strong::before{
    width:26px;height:26px;flex:0 0 26px;font-size:9px
  }
  body.fg-unified-reading .bar .brand #status{max-width:55vw;font-size:10px}
  body.fg-unified-reading .bar .actions button{font-size:12px;padding:6px 11px}
  body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar){
    padding:6px 9px!important;gap:6px
  }
  body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-title{
    max-width:calc(100vw - 170px);font-size:11px
  }
  body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-tools{
    width:auto;flex:1 1 auto
  }
  body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-find{
    width:clamp(105px,37vw,200px)
  }
  body.fg-unified-reading .fg-reader-toolbar:not(.fg-pdf-toolbar) .fg-reader-button{
    min-height:32px
  }
  .fg-unified-dock{bottom:calc(12px + env(safe-area-inset-bottom));padding:7px}
  .fg-unified-control{min-width:38px;min-height:38px;padding:7px 9px}
  .fg-unified-scale{min-width:58px}
  body.fg-unified-reading .fg-3d-toolbar{
    position:absolute;left:8px;right:8px;
    bottom:calc(10px + env(safe-area-inset-bottom));
    z-index:5;background:#182438ee;
    border:1px solid #657a9860;border-radius:16px;
    box-shadow:0 14px 40px #0007;
    display:flex!important;align-items:center;justify-content:center;
    flex-wrap:wrap;padding:8px
  }
  body.fg-unified-reading .fg-3d-heading{display:none!important}
  body.fg-unified-reading .fg-3d-tools{width:auto;justify-content:center;gap:5px}
  body.fg-unified-reading .fg-3d-button{padding:6px 8px;min-height:35px;font-size:12px}
  body.fg-unified-reading .fg-3d-select{max-width:40vw}
  body.fg-unified-reading .fg-3d-info{
    padding:5px 10px;font-size:10px;max-height:45px;overflow:hidden
  }
  body.fg-unified-reading .fg-3d-area{min-height:0}
  body.fg-unified-reading .fg-3d-canvas{touch-action:none}
  body.fg-unified-editor .spreadsheetTools{grid-template-columns:62px minmax(0,1fr);padding:5px}
  body.fg-unified-editor .sheetQuickActions{gap:2px}
}
""")
source=gradle.read_text()
source,c=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda match:'versionCode = '+str(int(match.group(1))+1),source,count=1)
assert c==1
source,c=re.subn(r'versionName\s*=\s*"[^"]+"','versionName = "0.11.0"',source,count=1)
assert c==1
gradle.write_text(source)
print("Unified reader controls installed for all supported formats; version 0.11.0")
