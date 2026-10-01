from pathlib import Path
import re

APP_NAME = "File Gestioner"
MARKER = "/* File Gestioner pro UI polish */"

MANIFEST = Path("app/src/main/AndroidManifest.xml")
INDEX = Path("app/src/main/assets/index.html")
CSS = Path("app/src/main/assets/style.css")
JS = Path("app/src/main/assets/app.js")
RES = Path("app/src/main/res")

def ensure_value(path: Path, name: str, value: str, kind: str = "string"):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text()
    else:
        text = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'
    pattern = rf'<{kind}\s+name="{re.escape(name)}"[^>]*>.*?</{kind}>'
    replacement = f'<{kind} name="{name}">{value}</{kind}>'
    if re.search(pattern, text, flags=re.S):
        text = re.sub(pattern, replacement, text, count=1, flags=re.S)
    else:
        text = text.replace('</resources>', f'    {replacement}\n</resources>', 1)
    path.write_text(text)

# Android identity: keep the package/application ID stable, change only the user-facing brand.
manifest = MANIFEST.read_text()
manifest = re.sub(r'android:label="[^"]*"', 'android:label="@string/app_name"', manifest, count=1)
if 'android:icon=' in manifest:
    manifest = re.sub(r'android:icon="[^"]*"', 'android:icon="@mipmap/ic_launcher"', manifest, count=1)
else:
    manifest = manifest.replace('<application', '<application\n        android:icon="@mipmap/ic_launcher"', 1)
if 'android:roundIcon=' in manifest:
    manifest = re.sub(r'android:roundIcon="[^"]*"', 'android:roundIcon="@mipmap/ic_launcher_round"', manifest, count=1)
else:
    manifest = manifest.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@mipmap/ic_launcher"\n        android:roundIcon="@mipmap/ic_launcher_round"', 1)
MANIFEST.write_text(manifest)

ensure_value(RES / "values" / "strings.xml", "app_name", APP_NAME)
ensure_value(RES / "values" / "colors.xml", "file_gestioner_icon_bg", "#111827", "color")

# Small-scale readable document/grid mark for launchers.
(RES / "drawable").mkdir(parents=True, exist_ok=True)
(RES / "drawable" / "ic_launcher_foreground.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M30,17H62L79,34V89H30Z" />
    <path
        android:fillColor="#8EA6FF"
        android:pathData="M62,17V34H79Z" />
    <path
        android:strokeColor="#334155"
        android:strokeWidth="4"
        android:strokeLineCap="round"
        android:pathData="M39,47H70 M39,58H70 M39,69H70 M39,80H62" />
    <path
        android:strokeColor="#8EA6FF"
        android:strokeWidth="4"
        android:strokeLineCap="round"
        android:pathData="M49,43V83 M60,43V72" />
</vector>
""")

(RES / "mipmap-anydpi").mkdir(parents=True, exist_ok=True)
legacy = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#111827" android:pathData="M0,0H108V108H0Z"/>
    <path android:fillColor="#FFFFFF" android:pathData="M30,17H62L79,34V89H30Z"/>
    <path android:fillColor="#8EA6FF" android:pathData="M62,17V34H79Z"/>
    <path android:strokeColor="#334155" android:strokeWidth="4" android:strokeLineCap="round" android:pathData="M39,47H70 M39,58H70 M39,69H70 M39,80H62"/>
    <path android:strokeColor="#8EA6FF" android:strokeWidth="4" android:strokeLineCap="round" android:pathData="M49,43V83 M60,43V72"/>
</vector>
"""
(RES / "mipmap-anydpi" / "ic_launcher.xml").write_text(legacy)
(RES / "mipmap-anydpi" / "ic_launcher_round.xml").write_text(legacy)

for d in ("mipmap-anydpi-v26", "mipmap-anydpi-v33"):
    folder = RES / d
    folder.mkdir(parents=True, exist_ok=True)
    adaptive = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/file_gestioner_icon_bg" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
"""
    (folder / "ic_launcher.xml").write_text(adaptive)
    (folder / "ic_launcher_round.xml").write_text(adaptive)

# Brand the in-app shell without changing document behavior.
html = INDEX.read_text()
html = re.sub(r'<title>.*?</title>', f'<title>{APP_NAME}</title>', html, count=1, flags=re.S)
html = html.replace('<strong>OpenLocal Office</strong>', f'<strong>{APP_NAME}</strong>')
html = html.replace('Local document viewer & editor', 'Files that stay on your device')
html = html.replace(
    'Open large spreadsheets and documents on your phone. Processing stays on-device.',
    'Open, inspect and edit spreadsheets and documents with a fast, local-first workflow.'
)
html = html.replace('<strong>Privacy</strong>', '<strong>Private by design</strong>')
INDEX.write_text(html)

css = CSS.read_text()
if MARKER not in css:
    css += r'''

/* File Gestioner pro UI polish */
:root{
  --fg-accent:#7187ff;
  --fg-accent-strong:#5d73f2;
  --fg-surface:#f5f7fb;
  --fg-card:#ffffff;
  --fg-elevated:#ffffff;
  --fg-border:#dce2ec;
  --fg-text:#141925;
  --fg-muted:#667085;
  --fg-shadow:0 8px 28px rgba(20,25,37,.08);
  --fg-radius:14px;
}
@media(prefers-color-scheme:dark){
  :root{
    --fg-surface:#0c0f15;
    --fg-card:#141821;
    --fg-elevated:#181d27;
    --fg-border:#2a303d;
    --fg-text:#f5f7fb;
    --fg-muted:#9ba4b3;
    --fg-shadow:0 12px 32px rgba(0,0,0,.28);
  }
}
html,body{
  background:var(--fg-surface);
  color:var(--fg-text);
  font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;
  -webkit-tap-highlight-color:transparent;
}
.bar{
  position:sticky;
  top:0;
  z-index:60;
  padding-top:max(10px,env(safe-area-inset-top));
  background:color-mix(in srgb,var(--fg-card) 92%,transparent);
  border-bottom:1px solid var(--fg-border);
  box-shadow:0 1px 0 rgba(255,255,255,.02);
  backdrop-filter:blur(18px) saturate(140%);
}
.brand{
  display:flex;
  min-width:0;
  align-items:center;
  gap:10px;
}
.brand strong{
  display:flex;
  min-width:0;
  align-items:center;
  gap:9px;
  font-size:15px;
  letter-spacing:-.01em;
}
.brand strong::before{
  content:"FG";
  display:grid;
  place-items:center;
  width:30px;
  height:30px;
  flex:0 0 30px;
  border-radius:9px;
  color:white;
  background:linear-gradient(145deg,var(--fg-accent),#879cff);
  font-size:11px;
  font-weight:800;
  box-shadow:0 5px 14px rgba(113,135,255,.28);
}
.brand #status{
  color:var(--fg-muted);
  font-size:12px;
}
button,input,select,textarea{
  font:inherit;
}
button{
  border-radius:11px;
  font-weight:650;
  letter-spacing:-.005em;
  transition:transform .08s ease,filter .12s ease,background .12s ease,border-color .12s ease;
}
button:active{transform:scale(.975)}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{
  outline:2px solid var(--fg-accent);
  outline-offset:2px;
}
.primary{
  background:var(--fg-accent)!important;
  border-color:var(--fg-accent)!important;
  color:white!important;
  box-shadow:0 6px 16px rgba(113,135,255,.22);
}
.primary:active{background:var(--fg-accent-strong)!important}
.home{
  width:min(100%,760px);
  margin:0 auto;
  padding:clamp(18px,5vw,42px) 16px calc(32px + env(safe-area-inset-bottom));
}
.card{
  background:var(--fg-card);
  border:1px solid var(--fg-border);
  border-radius:18px;
  box-shadow:var(--fg-shadow);
}
.hero{
  padding:clamp(22px,6vw,42px);
}
.hero h1{
  margin:0 0 10px;
  max-width:14ch;
  font-size:clamp(30px,8vw,48px);
  line-height:1.02;
  letter-spacing:-.045em;
}
.hero p{
  max-width:52ch;
  color:var(--fg-muted);
}
.formats{
  letter-spacing:.04em;
  font-size:12px;
  font-weight:700;
  color:var(--fg-muted)!important;
}
.searchbar,.sheetbar,.formatbar{
  background:var(--fg-card);
  border-color:var(--fg-border)!important;
}
.searchbar input,#goCell,select{
  background:var(--fg-elevated);
  color:var(--fg-text);
  border:1px solid var(--fg-border);
  border-radius:12px;
}
.tabs>button,.tabs>[role="tab"]{
  border:1px solid var(--fg-border);
  background:var(--fg-elevated);
  color:var(--fg-text);
}
.tabs>button.active,.tabs>[aria-selected="true"]{
  background:var(--fg-accent)!important;
  color:white!important;
  border-color:var(--fg-accent)!important;
}
#rangeInfo{
  color:var(--fg-muted);
  font-variant-numeric:tabular-nums;
}
#editor{
  background:var(--fg-surface);
}
#editor table{
  background:var(--fg-card);
}
#editor th{
  background:var(--fg-elevated)!important;
  color:var(--fg-muted);
  font-weight:700;
}
#editor td,#editor th{
  border-color:var(--fg-border)!important;
}
#editor td:focus-within{
  outline:2px solid var(--fg-accent);
  outline-offset:-2px;
}
.overlay{
  backdrop-filter:blur(8px);
}
.toast{
  border-radius:12px;
  box-shadow:var(--fg-shadow);
}
@media(max-width:700px){
  .bar{padding-left:10px;padding-right:10px}
  .brand #status{max-width:40vw}
  .hero{border-radius:16px}
  .hero h1{font-size:34px}
  .actions button{border-radius:10px}
}
'''
    CSS.write_text(css)

js = JS.read_text()
js_marker = "/* File Gestioner desktop-grade shortcuts */"
if js_marker not in js:
    js += r'''

/* File Gestioner desktop-grade shortcuts */
document.addEventListener('keydown',(event)=>{
  const key=(event.key||'').toLowerCase();
  const mod=event.ctrlKey||event.metaKey;
  if(mod&&key==='s'){
    event.preventDefault();
    document.getElementById('saveBtn')?.click();
  }else if(mod&&key==='f'){
    event.preventDefault();
    const input=document.getElementById('searchInput');
    if(input&&!input.closest('.hidden')){
      input.focus();
      input.select?.();
    }
  }else if(event.key==='Escape'){
    document.getElementById('searchResults')?.classList.add('hidden');
    document.activeElement?.blur?.();
  }
});
document.getElementById('tabs')?.addEventListener('click',(event)=>{
  const tab=event.target.closest('button,[role="tab"]');
  if(tab)requestAnimationFrame(()=>tab.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'}));
});
'''
    JS.write_text(js)
