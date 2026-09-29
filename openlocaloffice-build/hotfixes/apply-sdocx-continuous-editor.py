from pathlib import Path

MAIN = Path('app/src/main/java/com/openlocal/office/MainActivity.java')
APP = Path('app/src/main/assets/app.js')
CSS = Path('app/src/main/assets/style.css')

main = MAIN.read_text()

repls = [
('''    private DocxSession docx;
    private String textDocument;
    private byte[] rawDocument;''',
 '''    private DocxSession docx;
    private SdocxSession sdocx;
    private String textDocument;
    private byte[] rawDocument;'''),
('''                xlsx = null; csv = null; docx = null; textDocument = null; rawDocument = null;''',
 '''                xlsx = null; csv = null; docx = null; sdocx = null; textDocument = null; rawDocument = null;'''),
('''                } else if ("sdocx".equals(type)) {
                    rawDocument = bytes; currentType = "sdocx"; currentMime = "application/zip"; json = sdocxJson(name);''',
 '''                } else if ("sdocx".equals(type)) {
                    sdocx = SdocxSession.open(bytes); currentType = "sdocx"; currentMime = "application/zip"; json = sdocxJson(name);'''),
('''        if ("sdocx".equals(currentType)) { js("window.showError(" + q("SDOCX preview is read-only. Use Save copy to preserve the original file.") + ")"); return; }
''', ''),
('''        if (textDocument != null) return textDocument.getBytes(StandardCharsets.UTF_8);
        if (rawDocument != null) return rawDocument;''',
 '''        if (textDocument != null) return textDocument.getBytes(StandardCharsets.UTF_8);
        if (sdocx != null) return sdocx.serialize();
        if (rawDocument != null) return rawDocument;'''),
('''        if ("xlsx".equals(currentType) || "csv".equals(currentType) || "docx".equals(currentType)) {
            OfficeDocumentValidator.validate(currentType, bytes);
        }''',
 '''        if ("xlsx".equals(currentType) || "csv".equals(currentType) || "docx".equals(currentType)) {
            OfficeDocumentValidator.validate(currentType, bytes);
        } else if ("sdocx".equals(currentType)) {
            SdocxSession.validate(bytes);
        }'''),
('''    private String sdocxJson(String name) {
        return new StringBuilder("{\\"type\\":\\"sdocx\\",\\"name\\":").append(q(name)).append(",\\"readOnly\\":true}").toString();
    }''',
 '''    private String sdocxJson(String name) {
        return new StringBuilder("{\\"type\\":\\"sdocx\\",\\"name\\":").append(q(name))
                .append(",\\"readOnly\\":").append(sdocx == null || !sdocx.editable()).append('}').toString();
    }'''),
('''        @JavascriptInterface public String getText(){ return textDocument==null?"":textDocument; }
        @JavascriptInterface public void setText(String value){ if(textDocument!=null)textDocument=value==null?"":value; }''',
 '''        @JavascriptInterface public String getText(){ return textDocument==null?"":textDocument; }
        @JavascriptInterface public void setText(String value){ if(textDocument!=null)textDocument=value==null?"":value; }
        @JavascriptInterface public String getSdocxText(){ return sdocx==null?"":sdocx.text(); }
        @JavascriptInterface public void setSdocxText(String value){
            try { if(sdocx!=null)sdocx.setText(value); }
            catch(Exception e){ runOnUiThread(() -> js("window.showError("+q(message(e))+")")); }
        }'''),
]
for old,new in repls:
    if old not in main:
        raise SystemExit('MainActivity replacement target not found:\n'+old[:180])
    main = main.replace(old,new,1)
MAIN.write_text(main)

app = APP.read_text()
app = app.replace('''    textTimer:null, sdocxSession:null, sdocxInspection:null, sdocxPage:0,
    sdocxStyle:{font:'',color:'',bold:false,italic:false,underline:false}''',
                  '''    textTimer:null, sdocxTimer:null, sdocxSession:null, sdocxInspection:null, sdocxPage:0,
    sdocxStyle:{font:'',color:'',bold:false,italic:false,underline:false}''',1)

old_clear = '''  function clearModeBars(){
    $('sheetBar').classList.add('hidden');
    $('textFormat').classList.add('hidden');
    $('notice').classList.add('hidden');
  }'''
new_clear = '''  function clearModeBars(){
    $('sheetBar').classList.add('hidden');
    $('textFormat').classList.add('hidden');
    $('notice').classList.add('hidden');
    document.querySelector('.searchbar')?.classList.remove('hidden');
  }'''
if old_clear not in app: raise SystemExit('clearModeBars target not found')
app=app.replace(old_clear,new_clear,1)

start=app.index('  async function renderSdocx(page=null){')
end=app.index('\n\n  function nativeSearch(q){',start)
new_render = r'''  function persistSdocx(){
    const ed=$('sdocxEditor');
    if(!ed||state.doc?.readOnly)return;
    try{bridge()?.setSdocxText(ed.value);setDirty(true);}catch(e){showError(String(e));}
  }
  function renderSdocx(focusOffset=null){
    clearModeBars();
    document.querySelector('.searchbar')?.classList.add('hidden');
    $('textFormat').classList.add('hidden');
    const wrap=document.createElement('div');wrap.className='sdocxEditorWrap';
    const ed=document.createElement('textarea');
    ed.id='sdocxEditor';ed.className='sdocxEditor';ed.spellcheck=false;ed.readOnly=!!state.doc?.readOnly;
    try{ed.value=bridge()?.getSdocxText?.()||'';}catch(e){showError(String(e));ed.value='';}
    if(!ed.readOnly){
      ed.addEventListener('input',()=>{
        clearTimeout(state.sdocxTimer);
        state.sdocxTimer=setTimeout(persistSdocx,250);
      });
    }
    wrap.appendChild(ed);$('editor').replaceChildren(wrap);
    if(Number.isInteger(focusOffset))requestAnimationFrame(()=>{
      const at=clamp(focusOffset,0,ed.value.length);ed.focus();ed.setSelectionRange(at,at);
      const line=ed.value.slice(0,at).split('\n').length;
      ed.scrollTop=Math.max(0,(line-4)*26);
    });
  }'''
app = app[:start] + new_render + app[end:]

app = app.replace("    const hits=state.doc?.type==='sdocx'?sdocxSearch(q):nativeSearch(q);", "    const hits=nativeSearch(q);",1)
app = app.replace("        else if(hit.kind==='sdocx'&&hit.page!=null)renderSdocx(hit.page);\n", "",1)

old_save="""  $('saveBtn').onclick=()=>{if($('plainTextEditor'))persistText();bridge()?.saveInPlace();};
  $('copyBtn').onclick=()=>{if($('plainTextEditor'))persistText();bridge()?.saveCopy();};"""
new_save="""  $('saveBtn').onclick=()=>{if($('plainTextEditor'))persistText();if($('sdocxEditor'))persistSdocx();bridge()?.saveInPlace();};
  $('copyBtn').onclick=()=>{if($('plainTextEditor'))persistText();if($('sdocxEditor'))persistSdocx();bridge()?.saveCopy();};"""
if old_save not in app: raise SystemExit('save handlers target not found')
app=app.replace(old_save,new_save,1)
APP.write_text(app)

css=CSS.read_text()
css += r'''

/* SDOCX: continuous integrated editor */
#editor{flex:1;min-height:0;display:flex;overflow:hidden;background:var(--bg)}
.sdocxEditorWrap{flex:1;min-width:0;min-height:0;overflow:hidden;background:var(--bg)}
.sdocxEditor{display:block;width:100%;height:100%;margin:0;padding:18px 20px max(84px,calc(24px + env(safe-area-inset-bottom)));border:0;border-radius:0;outline:0;resize:none;background:var(--bg);color:var(--text);caret-color:var(--accent);font:400 17px/1.55 system-ui,-apple-system,Roboto,sans-serif;overflow-y:auto;overscroll-behavior:contain;white-space:pre-wrap;overflow-wrap:anywhere}
.sdocxEditor:focus{outline:0}
.sdocxEditor[readonly]{opacity:.82}
.sdocxCanvas{background:var(--bg)!important;box-shadow:none!important}
@media(max-width:700px){.sdocxEditor{padding:14px 16px max(72px,calc(18px + env(safe-area-inset-bottom)));font-size:16px;line-height:1.52}}
'''
CSS.write_text(css)
