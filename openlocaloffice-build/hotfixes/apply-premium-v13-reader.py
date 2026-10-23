from pathlib import Path
import re
root=Path("app/src/main")
native=root/"java/com/openlocal/office/core"
assets=root/"assets"
for name in ["SeekableZip.java","ReaderLibrary.java","ReaderCovers.java","KoikatsuCards.java"]:
    (native/name).write_text((Path("../additions")/name).read_text())
(assets/"premium-library.js").write_text(
    (Path("../additions")/"premium-library.js").read_text())
css=assets/"style.css"
css.write_text(css.read_text()+"\n"+(Path("../additions")/"premium-library.css").read_text())
page=assets/"index.html"
html=page.read_text()
anchor='<script src="epub-reader.js"></script>'
assert html.count(anchor)==1
html=html.replace(anchor,anchor+"\n<script src=\"premium-library.js\"></script>")
page.write_text(html)
reader=assets/"universal-reader.js"
js=reader.read_text()
anchor=" stage(bar,body);\n}\nfunction addLines(host,raw,format){"
assert js.count(anchor)==1
js=js.replace(anchor,''' if(doc.koikatsuCard===true){
   bar.classList.add('fg-koikatsu-toolbar');
   const heading=E('span','fg-koikatsu-heading','KOIKATSU · CHARACTER CARD');
   const view3d=button(doc.linked3d?'View 3D':'Connect 3D',
     ()=>bridge()?.openKoikatsu3d?.());
   view3d.setAttribute('aria-label','Open actual Koikatsu character as converted Blender 3D preview');
   tools.prepend(heading);
   tools.appendChild(view3d);
 }
 stage(bar,body);
}
function addLines(host,raw,format){''',1)
reader.write_text(js)
css.write_text(css.read_text()+r"""
/* Koikatsu PNG is a native serialized character card, not a renderable mesh */
.fg-koikatsu-toolbar .fg-koikatsu-heading{
 color:var(--fg-accent,#9db2ff);font:800 10px/1.4 system-ui;
 letter-spacing:.06em;
}
.fg-koikatsu-toolbar .fg-reader-button{
 background:linear-gradient(120deg,#6c82fa,#5369dc);
 border-color:transparent;color:#fff;font-weight:700;min-height:35px;
 border-radius:11px;padding:8px 15px;
}
@media(max-width:700px){
 .fg-koikatsu-toolbar .fg-koikatsu-heading{font-size:9px}
}
""")
gradle=Path("app/build.gradle.kts")
s=gradle.read_text()
s,n=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda m:'versionCode = '+str(int(m.group(1))+1),s,count=1)
assert n==1
s,n=re.subn(r'versionName\s*=\s*"[^"]+"',
            'versionName = "0.13.0"',s,count=1)
assert n==1
gradle.write_text(s)
print("v0.13.0 premium library/Koikatsu UI and fast seekable ZIP wired")
