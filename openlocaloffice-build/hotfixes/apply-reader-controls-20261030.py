#!/usr/bin/env python3
"""Add shared reader controls without replacing PDF, EPUB or ZIP readers."""
from pathlib import Path
root=Path("app/src/main")
html=root/"assets/index.html"
s=html.read_text()
assert "</body>" in s and "reader-controls.js" not in s
s=s.replace("</body>",'<script src="reader-controls.js"></script>\n</body>')
html.write_text(s)
css=root/"assets/style.css"
style=css.read_text()
style+="""

/* One compact reader control dock; system bars remain immersive during reading. */
.fg-controls{position:fixed;bottom:max(3px,env(safe-area-inset-bottom,0px));
 left:50%;transform:translateX(-50%);width:min(calc(100% - 12px),700px);
 z-index:9950;background:#111a2be8;color:#e8eefd;border:1px solid #405376b0;
 border-radius:12px;box-shadow:0 4px 20px #0008;padding:4px;
 font:12px/1.25 system-ui;backdrop-filter:blur(12px);}
.fg-control-row{display:flex;gap:3px;align-items:center;justify-content:space-between;min-height:35px;}
.fg-control-row>.fg-control-button{flex:1 1 auto;min-width:0;}
.fg-control-button{border:0;background:#263753bf;color:#eef3ff;border-radius:8px;
 font:600 12px/1.2 system-ui;min-height:34px;padding:7px 4px;touch-action:manipulation;}
.fg-control-button:active{background:#526db8}
.fg-control-progress{flex:1;min-width:20px;accent-color:#8da3fa;height:20px;touch-action:pan-x}
.fg-control-position{flex:0 0 55px;text-align:center;font-size:10px;white-space:nowrap;}
.fg-controls-mini .fg-control-scrub,.fg-controls-mini .fg-control-row>.fg-control-button:not(:last-child){display:none}
.fg-controls-mini{width:46px;left:auto;right:7px;transform:none}
.fg-controls-mini .fg-control-row{min-height:30px}
.fg-control-settings{position:fixed;z-index:11000;right:8px;bottom:95px;
 width:min(360px,calc(100vw - 16px));max-height:65dvh;overflow:auto;
 padding:14px;background:#1d2638;color:#f1f4fc;border:1px solid #637493;
 border-radius:16px;box-shadow:0 0 40px #0008;font:14px/1.4 system-ui;}
.fg-control-settings-row{display:flex;align-items:center;gap:7px;justify-content:space-between;margin:8px 0;}
.fg-control-field{display:flex;align-items:center;justify-content:space-between;
 gap:12px;margin:10px 0;padding:4px 0;}
.fg-control-field>*:last-child{min-width:40px;max-width:60%;color:inherit}
.fg-control-field select{background:#303c55;border:1px solid #607396;padding:9px;
 border-radius:8px;min-width:130px!important}
.fg-control-field input[type=range]{width:50%}
.fg-control-field input[type=color]{width:72px;height:40px;background:transparent;border:0}
.fg-control-lightbox{position:fixed;inset:0;z-index:13000;
 background:#070b11;display:flex;align-items:center;justify-content:center;
 overflow:hidden;touch-action:none}
.fg-control-big-image{display:block;max-width:100%;max-height:100%;
 object-fit:contain;touch-action:none;will-change:transform}
.fg-control-image-close{position:absolute;top:max(12px,env(safe-area-inset-top));
 right:12px;padding:8px 18px;font-size:23px}
.fg-folder-reader{width:100%;height:100%;min-height:0;display:flex;flex-direction:column;
 background:var(--fg-reader-paper,#101114);color:var(--fg-reader-ink,#e3e0dc)}
.fg-folder-scroll{width:100%;height:100%;flex:1;overflow:auto;overscroll-behavior:contain;
 -webkit-overflow-scrolling:touch;touch-action:pan-y;box-sizing:border-box;padding:0!important}
.fg-folder-stack{width:100%;max-width:none!important;padding:0!important;margin:0!important;
 display:flex;flex-direction:column;gap:0!important}
.fg-folder-page{margin:0!important;border:0!important;padding:0!important;line-height:0!important;
 width:100%;min-height:0;scroll-snap-align:start}
.fg-folder-image{width:100%!important;height:auto!important;display:block!important;max-width:none!important;
 border:0!important;margin:0!important;padding:0!important;object-fit:contain}
body.fg-folder-reading #editor{padding:0!important;margin:0!important;width:100%!important;
 max-width:none!important;min-height:0!important;overflow:hidden!important}
body.fg-folder-reading #work{height:100dvh!important;overflow:hidden!important}
body.fg-folder-reading .bar{display:none!important}
.fg-control-pages{scroll-snap-type:y proximity}
.fg-control-pages .fg-comic-section,.fg-control-pages .fg-pdf-section,
.fg-control-pages .fg-book-chapter,.fg-control-pages .fg-progressive-page{scroll-snap-align:start}
.fg-book,.fg-book-scroll,.fg-book-article{background:var(--fg-book-bg,#101114)!important;
 color:var(--fg-book-text,#e3e0dc)!important}
.fg-book-article{font-family:var(--fg-book-font,Georgia,serif)!important;
 font-size:var(--fg-book-font-size,19px)!important}
.fg-book-content:has(img){max-width:100%!important}
.fg-book-illustration,.fg-book-illustration img,.fg-book-chapter img{max-width:100%!important;
 object-fit:contain}
.fg-reader-scroll{background:var(--fg-reader-paper,#101114)!important}
.fg-continuous-text,.fg-document-p,.fg-document-sheet{color:var(--fg-reader-ink,#e3e0dc)!important;
 font-family:var(--fg-reader-font,Georgia,serif)!important;
 font-size:var(--fg-reader-size,19px)!important}
"""
style+="""
/* Large folders: only 96 document tiles render at a time. */
.fg-lib-pager{display:flex;align-items:center;justify-content:center;
 gap:7px;margin:12px 0 24px;grid-column:1/-1;font:600 12px system-ui;
 color:#b7c7dd;flex-wrap:wrap}
.fg-lib-page-control{background:#283a58;color:#eef5ff;
 border:1px solid #455b7d;border-radius:9px;min-height:38px;
 padding:7px 13px;font:600 12px system-ui}
.fg-lib-page-control:disabled{opacity:.32}
.fg-lib-page-number{background:#19253a;color:#eef5ff;
 border:1px solid #50658a;border-radius:8px;width:56px;min-height:35px;
 text-align:center;font:600 13px system-ui}
.fg-folder-sentinel{display:flex;justify-content:center;align-items:center;
 padding:12px 4px;color:#aebed8;background:#111722;
 font:12px system-ui;min-height:32px;line-height:1.3}
"""
css.write_text(style)
print("Shared reader dock + paged mode + colors/fonts + zoomable EPUB illustrations + image-folder layout enabled")
