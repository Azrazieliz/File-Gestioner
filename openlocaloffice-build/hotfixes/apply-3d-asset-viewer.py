from pathlib import Path

root=Path("app/src/main")
java=root/"java/com/openlocal/office/MainActivity.java"
js=root/"assets/universal-reader.js"
index=root/"assets/index.html"
css=root/"assets/style.css"
manifest=root/"AndroidManifest.xml"

def repl(path,old,new):
    s=path.read_text()
    assert old in s, f"Missing integration anchor in {path}: {old[:90]}"
    path.write_text(s.replace(old,new,1))

j=java.read_text()
assert 'getRawDocumentChunk' in j
repl(java,
    '                } else if ("epub".equals(type) ||',
    '''                } else if (isModelType(type)) {
                    rawDocument=bytes; currentType=type; currentMime=modelMime(type);
                    json="{\\"type\\":\\"model3d\\",\\"name\\":"+q(name)+
                        ",\\"format\\":"+q(type)+",\\"bytes\\":"+bytes.length+",\\"readOnly\\":true}";
                } else if ("epub".equals(type) ||''')
repl(java,
    '    private static boolean isImageType(String type) {',
    '''    private static boolean isModelType(String type) {
        return Arrays.asList("glb","gltf","obj","fbx","stl","ply",
            "dae","3mf","3ds","amf","usdz","usda","usdc").contains(type);
    }
    private static String modelMime(String type) {
        if ("glb".equals(type))return "model/gltf-binary";
        if ("gltf".equals(type))return "model/gltf+json";
        if ("obj".equals(type))return "model/obj";
        if ("stl".equals(type))return "model/stl";
        if ("usdz".equals(type))return "model/vnd.usdz+zip";
        return "application/octet-stream";
    }
    private static boolean isImageType(String type) {''')
repl(java,
    '              isImageType(currentType) || isTextType(currentType)) {',
    '              isImageType(currentType) || isTextType(currentType) || isModelType(currentType)) {')
repl(java,
    '             isImageType(ext) || isTextType(ext)))return ext;',
    '             isImageType(ext) || isTextType(ext) || isModelType(ext)))return ext;')
repl(java,
    '        if("application/msword".equals(m))return "doc";',
    '''        if ("model/gltf-binary".equals(m))return "glb";
        if ("model/gltf+json".equals(m))return "gltf";
        if ("model/obj".equals(m))return "obj";
        if ("model/stl".equals(m)||"application/sla".equals(m))return "stl";
        if ("model/vnd.usdz+zip".equals(m))return "usdz";
        if("application/msword".equals(m))return "doc";''')
# Correct a stale 40 MiB message; actual global bound is 80 MiB.
j=java.read_text().replace("larger than 40 MB","larger than 80 MiB")
java.write_text(j)

repl(js,"const ro=d=>['pdf','image','reader','archive','binary'].includes(d?.type)",
        "const ro=d=>['pdf','image','reader','archive','binary','model3d'].includes(d?.type)")
repl(js,
    "window.loadDocument=function(d){\n if(assetUrl)",
    "window.loadDocument=function(d){\n  window.FileGestionerModelViewer?.dispose?.();\n  if(assetUrl)")
repl(js,
    " else if(d.type==='docx')docx();",
    '''  else if(d.type==='docx')docx();
  else if(d.type==='model3d'){
    const host=$('editor');
    const viewer=window.FileGestionerModelViewer;
    if(viewer)viewer.open(d,host,bridge());
    else {
      const [bar]=toolbar('Offline 3D preview');
      const content=E('div','fg-reader-scroll');
      content.append(E('p','fg-reader-empty','The 3D rendering engine was not bundled in this build.'));
      stage(bar,content);
    }
  }''')
repl(index,
    '<script src="universal-reader.js"></script>',
    '<script src="universal-reader.js"></script>\n<script src="model-viewer.bundle.js"></script>')
repl(index,
    'PDF · DOCX · XLSX · EPUB · ODT · ODS · ODP · SDOCX · RTF · HTML · TXT · MD · CBZ · ZIP · IMAGES',
    'PDF · DOCX · XLSX · EPUB · ODT · ODS · SDOCX · 3D MODELS · RTF · HTML · TXT · MD · CBZ · ZIP · IMAGES')
repl(index,
    'documents, ebooks, PDFs, spreadsheets and image archives.',
    'documents, ebooks, PDFs, spreadsheets, images and 3D models.')
repl(index,
    'Document pages, slide text, ebook chapters, image and comic previews.',
    'Structured pages, ebook chapters, model previews and image archives.')

m=manifest.read_text()
needle='<data android:mimeType="application/octet-stream" />'
assert needle in m
m=m.replace(needle,needle+'''
                <data android:mimeType="model/*" />
                <data android:mimeType="application/sla" />''')
manifest.write_text(m)

css.write_text(css.read_text()+r"""
/* File Gestioner v0.10 · local interactive 3D inspector */
.fg-3d-app{height:100%;display:flex;flex-direction:column;min-height:0;min-width:0;
  background:#101723;color:#f0f4fd;overflow:hidden;font:14px system-ui,-apple-system,Roboto,sans-serif}
.fg-3d-toolbar{display:flex;gap:9px;align-items:center;justify-content:space-between;
  flex-wrap:wrap;background:#172233;padding:10px 13px;border-bottom:1px solid #30415a}
.fg-3d-heading{display:flex;align-items:center;min-width:0;gap:9px}
.fg-3d-name{font-size:13px;max-width:46vw;white-space:nowrap;text-overflow:ellipsis;overflow:hidden}
.fg-3d-badge{background:#344c79;color:#eaf1ff;letter-spacing:.06em;font:bold 10px system-ui;
  padding:6px 7px;border-radius:5px}
.fg-3d-tools{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.fg-3d-button,.fg-3d-select{background:#25354b;color:#eaf1fb;border:1px solid #465a72;
  min-height:37px;padding:6px 11px;border-radius:9px;font:600 12px system-ui}
.fg-3d-button:active{background:#394d70}
.fg-3d-select{max-width:190px}
.fg-3d-area{position:relative;flex:1;min-height:220px;overflow:hidden}
.fg-3d-canvas{position:absolute;inset:0;touch-action:none}
.fg-3d-canvas>canvas{display:block;width:100%;height:100%;touch-action:none}
.fg-3d-overlay{position:absolute;z-index:2;inset:0;display:grid;place-items:center;
  padding:25px;text-align:center;white-space:pre-wrap;line-height:1.5;
  color:#f2f5fc;background:linear-gradient(135deg,#192536,#111722)}
.fg-3d-info{background:#172233;border-top:1px solid #30415a;
  padding:11px 13px;color:#c5d4ec;font:12px/1.6 system-ui;max-height:90px;overflow:auto}
@media(max-width:600px){
  .fg-3d-toolbar{padding:8px;gap:8px}
  .fg-3d-heading{width:100%}
  .fg-3d-name{max-width:76vw}
  .fg-3d-tools{width:100%}
  .fg-3d-button{min-height:35px;padding:5px 9px}
}
""")
# Make this a real Android upgrade beyond the 0.9 build's versionCode.
gradle=Path("app/build.gradle.kts")
g=gradle.read_text()
import re
g, count=re.subn(r"versionCode\s*=\s*(\d+)",
    lambda match: "versionCode = "+str(int(match.group(1))+1),g,count=1)
assert count==1
g, count=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.10.0"',g,count=1)
assert count==1
gradle.write_text(g)
print("3D asset backend, MIME picker, offline UI, version bump: OK")
