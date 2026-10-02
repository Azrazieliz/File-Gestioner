from pathlib import Path
import re, shutil

MARK = "/* File Gestioner landscape + real icon */"
CSS = Path("app/src/main/assets/style.css")
APP = Path("app/src/main/assets/app.js")
MANIFEST = Path("app/src/main/AndroidManifest.xml")
RES = Path("app/src/main/res")
BRANDING = Path("../branding")

m = MANIFEST.read_text()
if 'android:configChanges=' not in m:
    m = m.replace(
        'android:launchMode="singleTop"',
        'android:launchMode="singleTop"\n            android:configChanges="orientation|screenSize|keyboardHidden"'
    )
if 'android:resizeableActivity=' not in m:
    m = m.replace(
        '<application',
        '<application\n        android:resizeableActivity="true"',
        1
    )
MANIFEST.write_text(m)

# Use a real raster launcher asset on legacy launchers.
src = BRANDING / "ic_launcher.png"
for name in ("ic_launcher.png", "ic_launcher_round.png"):
    dest = RES / "mipmap-xxxhdpi" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

# Remove the generic anydpi legacy vectors so density-aware PNG resources are selected.
for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
    p = RES / "mipmap-anydpi" / name
    if p.exists():
        p.unlink()

# A cleaner adaptive icon foreground for Android 8+.
(RES / "drawable").mkdir(parents=True, exist_ok=True)
(RES / "drawable" / "ic_launcher_foreground.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#AEBBFF"
        android:pathData="M27,25 C27,19 32,14 38,14 H66 C72,14 77,19 77,25 V74 C77,80 72,85 66,85 H38 C32,85 27,80 27,74 Z"/>
    <path android:fillColor="#F8FAFF"
        android:pathData="M34,29 C34,23 39,18 45,18 H65 L82,35 V81 C82,87 77,92 71,92 H45 C39,92 34,87 34,81 Z"/>
    <path android:fillColor="#CDD6FF" android:pathData="M65,18 L82,35 H65 Z"/>
    <path android:fillColor="#EDF1FF"
        android:pathData="M44,53 C44,49 47,46 51,46 H69 C73,46 76,49 76,53 V70 C76,74 73,77 69,77 H51 C47,77 44,74 44,70 Z"/>
    <path android:strokeColor="#5E70EF" android:strokeWidth="3.2"
        android:strokeLineCap="round"
        android:pathData="M50,52 V71 M59,52 V71 M68,52 V71 M48,58 H72 M48,66 H72"/>
    <path android:fillColor="#4A58D6"
        android:pathData="M46,39 C46,37 47,36 49,36 H62 C64,36 65,37 65,39 C65,41 64,42 62,42 H49 C47,42 46,41 46,39 Z"/>
    <path android:fillColor="#4ED8CA" android:pathData="M71,37 A3,3 0,1 0,71,43 A3,3 0,1 0,71,37"/>
</vector>
""")

css = CSS.read_text()
if MARK not in css:
    css += r'''

/* File Gestioner landscape + real icon */
.brand strong::before{
  content:""!important;
  background:
    center/cover no-repeat
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='15' fill='%233342a8'/%3E%3Cpath d='M18 15h24l10 10v27H18z' rx='6' fill='%23f8faff'/%3E%3Cpath d='M42 15v10h10' fill='%23cdd6ff'/%3E%3Cpath d='M25 34h20M25 41h20M32 30v16M39 30v16' stroke='%235e70ef' stroke-width='2.5' stroke-linecap='round'/%3E%3C/svg%3E")!important;
  color:transparent!important;
  box-shadow:0 5px 14px rgba(74,88,214,.3)!important;
}

@media (orientation:landscape) and (max-height:720px){
  .bar{
    padding:5px max(10px,env(safe-area-inset-right)) 5px max(10px,env(safe-area-inset-left))!important;
    min-height:48px;
  }
  .brand strong{font-size:14px}
  .brand strong::before{width:28px;height:28px;flex-basis:28px;border-radius:8px}
  .brand #status{display:none!important}
  .actions{gap:5px!important}
  .actions button{min-height:36px!important;padding:6px 10px!important}

  .searchbar{
    padding:5px 8px!important;
    gap:6px!important;
    grid-template-columns:minmax(220px,1fr) auto!important;
  }
  .searchbar input,.searchbar button{min-height:36px!important;height:36px!important}

  .sheetbar{padding:0 8px 4px!important}
  .tabs{gap:5px!important;padding:2px 0 4px!important;max-height:40px}
  .tabs>button,.tabs>[role="tab"]{
    min-height:34px!important;
    height:34px!important;
    padding:5px 11px!important;
    font-size:13px!important;
    max-width:32vw!important;
  }

  .rangeNav{
    display:grid!important;
    grid-template-columns:auto auto minmax(120px,1fr) auto auto auto!important;
    gap:5px!important;
    align-items:center!important;
  }
  .rangeNav button{width:auto!important;min-width:58px!important;min-height:34px!important;height:34px!important;padding:4px 8px!important}
  #rangeInfo{grid-column:auto!important;min-width:120px!important;font-size:12px!important}
  #goCell{grid-column:auto!important;min-width:86px!important;height:34px!important;min-height:34px!important}
  #goCellBtn{grid-column:auto!important;height:34px!important;min-height:34px!important}

  .spreadsheetTools{
    grid-template-columns:58px minmax(180px,1fr) auto!important;
    gap:6px!important;
    padding:5px 8px!important;
  }
  #selectedCellRef,.formulaBox{height:34px!important;min-height:34px!important}
  .formulaBox input{height:32px!important;font-size:14px!important}
  .sheetQuickActions{gap:3px!important}
  .sheetQuickActions button{width:32px!important;min-width:32px!important;height:32px!important;font-size:15px!important}

  #sheetBar:not(.hidden) ~ #editor{
    max-height:calc(100dvh - 184px)!important;
    min-height:220px;
  }
  #sheetBar:not(.hidden) ~ #editor table th,
  #sheetBar:not(.hidden) ~ #editor table td{
    min-width:108px!important;
    max-width:190px!important;
  }
  #sheetBar:not(.hidden) ~ #editor table tr>th:first-child,
  #sheetBar:not(.hidden) ~ #editor table tr>td:first-child{
    width:42px!important;
    min-width:42px!important;
    max-width:42px!important;
  }

  .home{
    width:min(100%,1100px)!important;
    padding:10px 16px calc(14px + env(safe-area-inset-bottom))!important;
  }
  .hero{
    padding:18px 22px!important;
  }
  .hero h1{
    font-size:30px!important;
    max-width:none!important;
    margin-bottom:6px!important;
  }
  .hero p{margin:6px 0!important}
}
'''
    CSS.write_text(css)

app = APP.read_text()
jsmark = "/* File Gestioner landscape continuity */"
if jsmark not in app:
    app += r'''

/* File Gestioner landscape continuity */
(()=>{
  let timer=null;
  const restore=()=>{
    clearTimeout(timer);
    timer=setTimeout(()=>{
      const active=document.querySelector('#editor td.fg-active,#editor td.fg-active-cell');
      active?.scrollIntoView?.({block:'nearest',inline:'nearest'});
    },120);
  };
  window.addEventListener('orientationchange',restore,{passive:true});
  window.addEventListener('resize',restore,{passive:true});
})();
'''
    APP.write_text(app)
