from pathlib import Path
import re

root=Path("app/src/main")
css=root/"assets/style.css"
index=root/"assets/index.html"
gradle=Path("app/build.gradle.kts")
html=index.read_text()
anchor='<script src="unified-viewer-controls.js"></script>'
assert html.count(anchor)==1
html=html.replace(anchor,anchor+'\n<script src="epub-reader.js"></script>')
index.write_text(html)
sheet=css.read_text()
sheet+=r"""

/* File Gestioner · premium EPUB long-form reading, not ZIP-to-plaintext */
body.fg-book-mode .bar{display:none!important}
body.fg-book-mode .work{height:100dvh!important;min-height:0!important}
body.fg-book-mode #editor.fg-reader-host{height:100%!important;flex:1 1 auto}
.fg-book-back{min-width:36px;min-height:36px;padding:5px 9px!important;font-size:23px!important;border:0!important}

body.fg-book-mode{background:#0d1016}
body.fg-book-mode #editor.fg-reader-host{padding:0!important;min-height:0}
body.fg-book-mode .bar{height:51px;min-height:51px;padding:5px 13px;
 border-bottom:0;box-shadow:none;background:#10131b}
body.fg-book-mode .bar .brand strong{font-size:12px;opacity:.88}
body.fg-book-mode .bar .brand #status{display:none}
body.fg-book-mode .bar .actions button:disabled{display:none!important}
body.fg-book-mode .bar .actions #openBtn{height:33px;min-height:33px;
 padding:6px 13px;font:600 12px system-ui}
.fg-book{
 --fg-book-font:"Noto Serif",Georgia,serif;
 --fg-book-font-size:19px;
 --fg-book-leading:1.7;
 --fg-book-side:20px;
 --fg-book-bg:#101114;
 --fg-book-paper:#101114;
 --fg-book-text:#e3e0dc;
 --fg-book-muted:#9a9896;
 --fg-book-accent:#b7a5f8;
 --fg-book-border:#31323a;
 position:relative;display:flex;flex-direction:column;flex:1 1 auto;
 height:100%;min-height:0;width:100%;
 background:var(--fg-book-bg);color:var(--fg-book-text);
 font:400 var(--fg-book-font-size)/var(--fg-book-leading) var(--fg-book-font);
 font-kerning:normal;text-rendering:optimizeLegibility;
 font-optical-sizing:auto;-webkit-font-smoothing:antialiased;
}
.fg-book-theme-paper{
 --fg-book-bg:#f3f0e8;--fg-book-paper:#f3f0e8;--fg-book-text:#252a2d;
 --fg-book-muted:#68685f;--fg-book-accent:#455f93;--fg-book-border:#d2cec2;
}
.fg-book-theme-sepia{
 --fg-book-bg:#eee3c9;--fg-book-paper:#eee3c9;--fg-book-text:#433525;
 --fg-book-muted:#786c58;--fg-book-accent:#806346;--fg-book-border:#c5b8a0;
}
.fg-book-theme-white{
 --fg-book-bg:#ffffff;--fg-book-paper:#ffffff;--fg-book-text:#202329;
 --fg-book-muted:#666c75;--fg-book-accent:#556ac0;--fg-book-border:#dadde5;
}
.fg-book-top{
 z-index:15;flex:0 0 auto;display:flex;align-items:center;gap:8px;
 min-height:50px;max-height:59px;
 padding:7px clamp(10px,2.5vw,18px);
 background:var(--fg-book-bg);
 border-bottom:1px solid var(--fg-book-border);
 font:500 12px/1.35 system-ui;
 transition:opacity .16s,transform .16s;
}
.fg-book-heading{flex:1 1 auto;min-width:0;overflow:hidden;
 white-space:nowrap;text-overflow:ellipsis;display:flex;flex-direction:column}
.fg-book-name{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 font-size:13px;letter-spacing:-.01em}
.fg-book-author{display:block;color:var(--fg-book-muted);font-size:10px;
 margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fg-book-button{
 border:1px solid var(--fg-book-border);color:var(--fg-book-text);
 background:transparent;border-radius:12px;min-height:37px;
 padding:7px 11px;font:600 12px system-ui;
}
.fg-book-button:focus-visible{outline:2px solid var(--fg-book-accent);outline-offset:2px}
.fg-book-button:active{background:color-mix(in srgb,var(--fg-book-text) 9%,transparent)}
.fg-book-scroll{
 flex:1 1 auto;min-height:0;min-width:0;
 overflow-y:auto;overflow-x:hidden;
 padding:0;
 touch-action:pan-y;
 overscroll-behavior-y:contain;-webkit-overflow-scrolling:touch;
 background:var(--fg-book-paper);
}
.fg-book-content{box-sizing:border-box;width:100%;max-width:790px;
 margin:0 auto;padding:0 var(--fg-book-side) 40vh}
.fg-book-chapter{
 width:100%;min-height:50vh;
 overflow-wrap:break-word;word-break:normal;
 padding:14px 0 clamp(25px,4vh,45px);
 box-sizing:border-box;
}
.fg-book-chapter+.fg-book-chapter{border-top:1px solid color-mix(in srgb,var(--fg-book-border) 42%,transparent)}
.fg-book-loading{min-height:70vh;display:flex;align-items:center;justify-content:center}
.fg-book-article{
 color:var(--fg-book-text);
 font:400 var(--fg-book-font-size)/var(--fg-book-leading) var(--fg-book-font);
 font-feature-settings:"kern" 1,"liga" 1;
 letter-spacing:.002em;text-align:start;
}
.fg-book-article p{margin:0 0 1.16em;line-height:inherit;orphans:2;widows:2}
.fg-book-article p+p{text-indent:0}
.fg-book-article h1,.fg-book-article h2,.fg-book-article h3,
.fg-book-article h4,.fg-book-article h5,.fg-book-article h6{
 color:var(--fg-book-text);font-family:var(--fg-book-font);
 font-weight:700;letter-spacing:-.018em;line-height:1.26;
 margin:1.5em 0 .85em;text-indent:0
}
.fg-book-article h1{font-size:1.65em;margin-top:1.3em}
.fg-book-article h2{font-size:1.42em}
.fg-book-article h3{font-size:1.2em}
.fg-book-article h4,.fg-book-article h5{font-size:1.04em}
.fg-book-article strong,.fg-book-article b{font-weight:700}
.fg-book-article em,.fg-book-article i{font-style:italic}
.fg-book-article blockquote{margin:1.3em 0 1.3em 1em;padding:0 0 0 .9em;
 border-left:2px solid var(--fg-book-accent);color:var(--fg-book-muted)}
.fg-book-article blockquote p{margin-bottom:.65em}
.fg-book-article ul,.fg-book-article ol{padding-left:1.35em;margin:1em 0}
.fg-book-article li{margin:.45em 0}
.fg-book-article img{
 display:block;max-width:100%;width:auto;height:auto;object-fit:contain;
 margin:1.4em auto;border:0;
}
.fg-book-article figure{margin:1.4em 0;padding:0;text-align:center}
.fg-book-article figure img{margin:0 auto}
.fg-book-article figcaption{font:400 .76em/1.5 system-ui;
 color:var(--fg-book-muted);padding-top:.5em}
.fg-book-article hr{height:1px;border:0;
 background:var(--fg-book-border);margin:2em 16%}
.fg-book-article ruby{ruby-position:over}
.fg-book-article rt{font-size:.5em}
.fg-book-article sup,.fg-book-article sub{font-size:.7em}
.fg-book-article table{max-width:100%;display:block;overflow-x:auto;
 border-collapse:collapse;margin:1.1em auto}
.fg-book-article th,.fg-book-article td{border:1px solid var(--fg-book-border);
 padding:6px 9px;vertical-align:top}
.fg-book-article pre{max-width:100%;overflow:auto;padding:12px 16px;
 background:color-mix(in srgb,var(--fg-book-text) 7%,transparent);
 border-radius:10px;line-height:1.5}
.fg-book-article code{font-size:.82em;overflow-wrap:anywhere}
.fg-book-article a{color:var(--fg-book-accent);text-decoration:underline;
 text-underline-offset:.17em;cursor:pointer}
.fg-book-article [dir=rtl]{direction:rtl;text-align:right}
.fg-book-bottom{
 z-index:15;display:flex;flex:0 0 auto;justify-content:space-between;align-items:center;
 gap:8px;padding:5px 11px calc(7px + env(safe-area-inset-bottom));
 background:var(--fg-book-bg);border-top:1px solid var(--fg-book-border);
 min-height:44px;font:500 11px system-ui;color:var(--fg-book-muted);
 transition:opacity .16s;
}
.fg-book-progress{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 flex:1;min-width:0;font:500 11px system-ui}
.fg-book-bottom .fg-book-button{border:0;font-size:20px;min-width:44px;min-height:32px}
.fg-book-chrome-hidden{opacity:0;pointer-events:none}
.fg-book-top.fg-book-chrome-hidden{height:0;max-height:0;min-height:0;padding:0;border:0;overflow:hidden}
.fg-book-bottom.fg-book-chrome-hidden{height:0;max-height:0;min-height:0;padding:0;border:0;overflow:hidden}
.fg-book-drawer{position:absolute;z-index:50;inset:auto 0 0;
 max-height:min(82vh,740px);min-height:35vh;
 display:flex;flex-direction:column;
 background:var(--fg-book-bg);color:var(--fg-book-text);
 border:1px solid var(--fg-book-border);border-radius:22px 22px 0 0;
 box-shadow:0 -20px 80px #0007;
 font:400 14px/1.5 system-ui;
}
.fg-book-hidden{display:none!important}
.fg-book-drawer-title{display:flex;align-items:center;justify-content:space-between;
 gap:12px;min-height:59px;padding:10px 18px;border-bottom:1px solid var(--fg-book-border);
 font-size:16px}
.fg-book-drawer-title .fg-book-button{font-size:23px;border:0;min-width:40px}
.fg-book-drawer-body{overflow:auto;flex:1;min-height:0;padding:12px 16px 28px}
.fg-book-toc-item{width:100%;height:auto;padding:15px 13px;min-height:49px;
 text-align:left;border:0;border-bottom:1px solid var(--fg-book-border);
 border-radius:0;display:block;white-space:normal;line-height:1.4;
 overflow-wrap:anywhere;font-weight:500}
.fg-book-option-title{margin:16px 0 8px;font:650 12px system-ui;
 color:var(--fg-book-muted);text-transform:uppercase;letter-spacing:.06em}
.fg-book-option-row{display:flex;gap:7px;flex-wrap:wrap}
.fg-book-option-row .fg-book-button{min-height:40px}
.fg-book-option-selected{border-color:var(--fg-book-accent);
 color:var(--fg-book-accent);background:color-mix(in srgb,var(--fg-book-accent) 10%,transparent)}
.fg-book-error{padding:20px;color:var(--fg-book-muted);font:14px system-ui}
body.fg-book-mode #fg-unified-dock{display:none}
@media(min-width:730px){
 .fg-book-content{padding-left:max(32px,var(--fg-book-side));
 padding-right:max(32px,var(--fg-book-side))}
 .fg-book-article{font-size:var(--fg-book-font-size)}
 .fg-book-drawer{left:auto;width:420px;right:18px;bottom:18px;
  border-radius:17px;max-height:70vh}
}
@media(max-width:700px){
 .fg-book-content{max-width:100%;padding:0 var(--fg-book-side) 25vh}
 .fg-book-chapter{padding-top:8px;padding-bottom:21px}
 .fg-book-top{min-height:47px;padding:6px 10px}
 .fg-book-name{font-size:12px}
 .fg-book-button{min-height:35px;padding:6px 10px}
 .fg-book-article{font-size:var(--fg-book-font-size)}
}
"""
css.write_text(sheet)
v=gradle.read_text()
v,c=re.subn(r'versionCode\s*=\s*(\d+)',lambda m:"versionCode = "+str(int(m.group(1))+1),v,count=1)
assert c==1
v,c=re.subn(r'versionName\s*=\s*"[^"]+"','versionName = "0.12.0"',v,count=1)
assert c==1
gradle.write_text(v)
print("Book typography/theming, TOC and offline reading layout + v0.12.0 wired")
